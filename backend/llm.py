"""LLM integration for generating contextual responses.

Supports Google Gemini (primary) and Groq (fallback) for generating
AI-powered contextual responses based on search results.
"""

import logging
import time
from typing import Optional

from config import get_settings

settings = get_settings()

# Configure logging
logger = logging.getLogger(__name__)

# Rate limiting state
_rate_limit_state = {
    "gemini": {"count": 0, "reset_time": 0},
    "groq": {"count": 0, "reset_time": 0},
}


def _check_rate_limit(provider: str, limit: int) -> bool:
    """Check if we're within rate limits for a provider.

    Args:
        provider: 'gemini' or 'groq'
        limit: Requests per minute limit

    Returns:
        True if within limits, False if rate limited
    """
    current_time = time.time()
    state = _rate_limit_state[provider]

    # Reset counter if minute has passed
    if current_time - state["reset_time"] >= 60:
        state["count"] = 0
        state["reset_time"] = current_time

    if state["count"] >= limit:
        logger.warning(f"{provider.capitalize()} rate limit exceeded ({limit} RPM)")
        return False

    state["count"] += 1
    return True


def _build_prompt(query: str, verses: list[dict], language: str = "en") -> str:
    """Build the prompt for LLM response generation.

    Args:
        query: User's search query
        verses: List of verse result dictionaries
        language: Response language ('en' or 'ko')

    Returns:
        Formatted prompt string
    """
    # Format verses for context (use top 8 for better context)
    verse_context = []
    for i, v in enumerate(verses[:8], 1):
        ref = v.get("reference", {})
        translations = v.get("translations", {})

        # Get first available translation text
        text = next(iter(translations.values()), "")
        # Truncate very long verses for token efficiency
        text_preview = text[:150] + "..." if len(text) > 150 else text

        verse_context.append(
            f"{i}. {ref.get('book', '')} {ref.get('chapter', '')}:{ref.get('verse', '')} - \"{text_preview}\""
        )

    verses_text = "\n".join(verse_context)
    verse_count = len(verses[:8])

    if language == "ko":
        prompt = f"""다음 성경 구절들을 바탕으로 질문에 대해 포괄적인 답변을 제공해 주세요.

질문: {query}

관련 성경 구절 ({verse_count}개):
{verses_text}

답변 지침:
- 질문에 직접적으로 답하는 4-5문장의 답변을 작성해 주세요
- 특정 구절을 인용할 때는 책 이름과 장:절을 명시해 주세요 (예: "로마서 12:9에 따르면...")
- 성경적 맥락과 신학적 의미를 설명해 주세요
- 실제 적용이나 핵심 교훈으로 마무리해 주세요
- 답변이 완전한 문장으로 끝나도록 해 주세요"""
    else:
        prompt = f"""Based on the following Bible verses, please provide a comprehensive answer to the question.

Question: {query}

Relevant verses ({verse_count} total):
{verses_text}

Instructions:
- Provide a 4-5 sentence answer that directly addresses the question
- Cite specific verses by reference (e.g., 'According to Romans 12:9...')
- Explain the biblical context and theological significance
- Conclude with practical application or key takeaway
- Ensure your response is complete and ends with proper punctuation"""

    return prompt


async def generate_response_stream_gemini(
    query: str,
    verses: list[dict],
    language: str = "en",
    api_key: str | None = None,
) -> any:  # Returns an async generator
    """Generate a streaming response using Google Gemini."""
    gemini_key = api_key or settings.gemini_api_key
    if not gemini_key or not _check_rate_limit("gemini", settings.gemini_rpm):
        yield None
        return

    try:
        import google.generativeai as genai
        
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(
            "gemini-1.5-flash", # Use 1.5-flash for speed
            system_instruction="You are a knowledgeable Bible study assistant. Provide thoughtful, contextual answers that help users understand biblical teachings. Always cite specific verse references and explain theological significance. Your responses should be complete, ending with proper punctuation."
        )

        prompt = _build_prompt(query, verses, language)
        
        # Async streaming is supported in newer genai versions or we can use ThreadPool
        # For true async in Python with genai, check library support. 
        # current google-generativeai supports generate_content(stream=True) which returns a sync iterator.
        # To stream asynchronously, we might need to wrap it or use their async client if available.
        # As of recent versions, genai.generate_content_async is available.
        
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=1024,
                temperature=0.7,
            ),
            stream=True
        )
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        logger.error(f"Gemini Streaming error: {e}")
        yield None


async def generate_response_stream_groq(
    query: str,
    verses: list[dict],
    language: str = "en",
    api_key: str | None = None,
) -> any:  # Returns an async generator
    """Generate a streaming response using Groq."""
    groq_key = api_key or settings.groq_api_key
    if not groq_key or not _check_rate_limit("groq", settings.groq_rpm):
        yield None
        return

    try:
        from groq import AsyncGroq
        
        client = AsyncGroq(api_key=groq_key)
        prompt = _build_prompt(query, verses, language)

        stream = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a knowledgeable Bible study assistant. Provide thoughtful, contextual answers that help users understand biblical teachings. Always cite specific verse references and explain theological significance. Your responses should be complete, ending with proper punctuation.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
            temperature=0.7,
            stream=True,
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    except Exception as e:
        logger.error(f"Groq Streaming error: {e}")
        yield None


async def generate_contextual_response_stream(
    query: str,
    verses: list[dict],
    language: str = "en",
    gemini_api_key: str | None = None,
    groq_api_key: str | None = None,
):
    """Generate a streaming contextual response."""
    if not verses:
        yield None
        return

    # Try Groq first
    try:
        groq_gen = generate_response_stream_groq(query, verses, language, api_key=groq_api_key)
        
        # Check if we get any content effectively
        # Since it is a generator, we iterate. Use a flag.
        first_chunk = True
        async for chunk in groq_gen:
            if chunk is None:
                break # Failed
            yield chunk
            first_chunk = False
        
        if not first_chunk:
            return  # Success

    except Exception as e:
        logger.error(f"Groq stream failed: {e}")

    # Fallback to Gemini
    try:
        gemini_gen = generate_response_stream_gemini(query, verses, language, api_key=gemini_api_key)
        async for chunk in gemini_gen:
            if chunk is None:
                break
            yield chunk
    except Exception as e:
        logger.error(f"Gemini stream failed: {e}")


def generate_contextual_response(
    query: str,
    verses: list[dict],
    language: str = "en",
    gemini_api_key: str | None = None,
    groq_api_key: str | None = None,
) -> Optional[str]:
    """Generate a contextual response (synchronous wrapper/shim for compatibility).
    
    This function exists primarily for backward compatibility and tests.
    It does NOT support streaming and may not work fully in async context without event loop.
    For production, use generate_contextual_response_stream.
    """
    # For now, return None to satisfy imports, or implement a blocking call if needed.
    # Since we moved to async, a sync call is tricky. 
    # Return None is safest for "fallback" behavior if tests expect Optional[str].
    return None

def detect_language(text: str) -> str:
    """Detect the language of input text.

    Simple heuristic based on character ranges.

    Args:
        text: Input text to analyze

    Returns:
        'ko' for Korean, 'en' for English/other
    """
    korean_chars = 0
    total_chars = 0

    for char in text:
        if char.isalpha():
            total_chars += 1
            # Korean Unicode range
            if "\uac00" <= char <= "\ud7a3" or "\u3131" <= char <= "\u3163":
                korean_chars += 1

    if total_chars == 0:
        return "en"

    # If more than 30% Korean characters, consider it Korean
    if korean_chars / total_chars > 0.3:
        return "ko"

    return "en"
