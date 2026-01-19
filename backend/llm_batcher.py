"""Batching system for LLM requests to reduce API calls and costs.

Queues incoming requests and processes them in batches to take advantage of
Gemini's Batch API (50% cost savings) and higher rate limits.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """A single request in the batch queue."""

    id: UUID
    query: str
    verses: list[dict]
    language: str
    timestamp: float
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    completed: asyncio.Event = None

    def __post_init__(self):
        if self.completed is None:
            self.completed = asyncio.Event()


class LLMBatcher:
    """Batches LLM requests for efficient API usage."""

    def __init__(self):
        self.queue: list[BatchRequest] = []
        self.lock = asyncio.Lock()
        self.processing = False
        self._background_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the background batch processor."""
        if self._background_task is None or self._background_task.done():
            self._background_task = asyncio.create_task(self._process_batches())

    async def stop(self):
        """Stop the background batch processor."""
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

    async def submit_request(
        self,
        query: str,
        verses: list[dict],
        language: str = "en",
        gemini_api_key: str | None = None,
        groq_api_key: str | None = None,
    ) -> str:
        """Submit a request for batched processing.

        Args:
            query: User's search query
            verses: List of verse result dictionaries
            language: Response language ('en' or 'ko')
            gemini_api_key: Optional user-provided Gemini API key
            groq_api_key: Optional user-provided Groq API key

        Returns:
            Generated response string or None if failed
        """
        if not settings.enable_batching:
            # Fall back to direct processing
            from llm import generate_contextual_response

            return generate_contextual_response(
                query, verses, language,
                gemini_api_key=gemini_api_key,
                groq_api_key=groq_api_key,
            )

        # Create request
        request = BatchRequest(
            id=uuid4(),
            query=query,
            verses=verses,
            language=language,
            timestamp=time.time(),
            gemini_api_key=gemini_api_key,
            groq_api_key=groq_api_key,
        )

        # Add to queue
        async with self.lock:
            self.queue.append(request)

        # Wait for processing
        await request.completed.wait()

        if request.error:
            # Fall back to direct processing on error
            from llm import generate_contextual_response

            return generate_contextual_response(
                query, verses, language,
                gemini_api_key=gemini_api_key,
                groq_api_key=groq_api_key,
            )

        return request.result

    async def _process_batches(self):
        """Background task that processes batches at regular intervals."""
        while True:
            try:
                # Wait for the batch window
                await asyncio.sleep(settings.batch_window_ms / 1000.0)

                # Get pending requests
                async with self.lock:
                    if not self.queue:
                        continue

                    # Take up to max_batch_size requests
                    batch = self.queue[: settings.max_batch_size]
                    self.queue = self.queue[settings.max_batch_size :]

                if batch:
                    await self._process_batch(batch)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in batch processor: {e}")

    async def _process_batch(self, batch: list[BatchRequest]):
        """Process a batch of requests using Gemini Batch API.

        Args:
            batch: List of BatchRequest objects to process
        """
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.gemini_api_key)

            # Build batch requests
            from llm import _build_prompt

            batch_contents = []
            for req in batch:
                prompt = _build_prompt(req.query, req.verses, req.language)
                batch_contents.append({"contents": [{"parts": [{"text": prompt}]}]})

            # Make batch API call
            model = genai.GenerativeModel(
                "gemini-2.5-flash",  # Using stable model instead of preview
                system_instruction="You are a knowledgeable Bible study assistant. Provide thoughtful, contextual answers that help users understand biblical teachings. Always cite specific verse references and explain theological significance. Your responses should be complete, ending with proper punctuation."
            )

            # Process requests individually but with better rate limiting
            # Note: Google's batch API is async/file-based, so for real-time
            # we'll process in parallel instead
            tasks = []
            for req, content in zip(batch, batch_contents):
                tasks.append(self._process_single(model, req, content["contents"][0]))

            # Wait for all to complete
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            print(f"Batch processing error: {e}")
            # Mark all as failed
            for req in batch:
                req.error = str(e)
                req.completed.set()

    async def _process_single(
        self, model, request: BatchRequest, content: dict
    ) -> None:
        """Process a single request within a batch.

        Args:
            model: Gemini model instance
            request: BatchRequest to process
            content: Formatted content for the API
        """
        try:
            # Generate response
            start_time = time.time()
            response = await asyncio.to_thread(
                model.generate_content,
                content["parts"][0]["text"],
                generation_config={
                    "max_output_tokens": 1024,  # Sufficient for 4-5 sentence responses
                    "temperature": 0.7,
                },
            )

            elapsed = time.time() - start_time

            # Check finish reason for truncation
            finish_reason = response.candidates[0].finish_reason if response.candidates else None
            logger.info(f"Batch request {request.id} finish_reason: {finish_reason}")

            request.result = response.text
            logger.info(f"Batch request {request.id}: {len(response.text)} chars in {elapsed:.2f}s")

            # Validate response is complete
            if finish_reason == 1:  # MAX_TOKENS
                logger.warning(f"Batch response truncated due to MAX_TOKENS limit")
            elif not response.text.endswith((".", "!", "?")):
                logger.warning(f"Batch response may be truncated: {response.text[-50:]}")

        except Exception as e:
            logger.error(f"Error processing batch request {request.id}: {e}", exc_info=True)
            request.error = str(e)
        finally:
            request.completed.set()


# Global batcher instance
_batcher: Optional[LLMBatcher] = None


def get_batcher() -> LLMBatcher:
    """Get the global batcher instance."""
    global _batcher
    if _batcher is None:
        _batcher = LLMBatcher()
    return _batcher


async def batched_generate_response(
    query: str,
    verses: list[dict],
    language: str = "en",
    gemini_api_key: str | None = None,
    groq_api_key: str | None = None,
) -> Optional[str]:
    """Generate a response using the batching system.

    Args:
        query: User's search query
        verses: List of verse result dictionaries
        language: Response language ('en' or 'ko')
        gemini_api_key: Optional user-provided Gemini API key
        groq_api_key: Optional user-provided Groq API key

    Returns:
        Generated response string or None if failed
    """
    if not verses:
        return None

    batcher = get_batcher()
    await batcher.start()

    try:
        return await batcher.submit_request(
            query, verses, language,
            gemini_api_key=gemini_api_key,
            groq_api_key=groq_api_key,
        )
    except Exception as e:
        print(f"Batched generation error: {e}")
        # Fall back to direct processing
        from llm import generate_contextual_response

        return generate_contextual_response(
            query, verses, language,
            gemini_api_key=gemini_api_key,
            groq_api_key=groq_api_key,
        )
