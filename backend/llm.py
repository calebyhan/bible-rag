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


def generate_response_gemini(
    query: str,
    verses: list[dict],
    language: str = "en",
) -> Optional[str]:
    """Generate a response using Google Gemini.

    Args:
        query: User's search query
        verses: List of verse result dictionaries
        language: Response language

    Returns:
        Generated response string or None if failed
    """
    if not settings.gemini_api_key:
        logger.warning("Gemini API key not configured")
        return None

    if not _check_rate_limit("gemini", settings.gemini_rpm):
        return None

    try:
        import google.generativeai as genai

        start_time = time.time()

        genai.configure(api_key=settings.gemini_api_key)

        # Configure model with system instruction
        model = genai.GenerativeModel(
            "gemini-2.5-flash",  # Using stable model instead of preview
            system_instruction="You are a knowledgeable Bible study assistant. Provide thoughtful, contextual answers that help users understand biblical teachings. Always cite specific verse references and explain theological significance. Your responses should be complete, ending with proper punctuation."
        )

        prompt = _build_prompt(query, verses, language)

        logger.info(f"Calling Gemini API for query: {query[:50]}...")

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=1024,  # Sufficient for 4-5 sentence responses
                temperature=0.7,
            ),
        )

        elapsed = time.time() - start_time

        # Check finish reason for truncation
        finish_reason = response.candidates[0].finish_reason if response.candidates else None
        logger.info(f"Gemini finish_reason: {finish_reason}")

        response_text = response.text

        logger.info(f"Gemini response generated: {len(response_text)} chars in {elapsed:.2f}s")

        # Validate response is complete
        if finish_reason == 1:  # MAX_TOKENS
            logger.warning(f"Gemini response truncated due to MAX_TOKENS limit")
        elif not response_text.endswith((".", "!", "?")):
            logger.warning(f"Gemini response may be truncated (no ending punctuation): {response_text[-50:]}")

        return response_text

    except Exception as e:
        logger.error(f"Gemini API error: {e}", exc_info=True)
        return None


def generate_response_groq(
    query: str,
    verses: list[dict],
    language: str = "en",
) -> Optional[str]:
    """Generate a response using Groq.

    Args:
        query: User's search query
        verses: List of verse result dictionaries
        language: Response language

    Returns:
        Generated response string or None if failed
    """
    if not settings.groq_api_key:
        logger.warning("Groq API key not configured")
        return None

    if not _check_rate_limit("groq", settings.groq_rpm):
        return None

    try:
        from groq import Groq

        start_time = time.time()

        client = Groq(api_key=settings.groq_api_key)

        prompt = _build_prompt(query, verses, language)

        logger.info(f"Calling Groq API for query: {query[:50]}...")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a knowledgeable Bible study assistant. Provide thoughtful, contextual answers that help users understand biblical teachings. Always cite specific verse references and explain theological significance. Your responses should be complete, ending with proper punctuation.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,  # Increased for complete responses
            temperature=0.7,
        )

        elapsed = time.time() - start_time
        response_text = response.choices[0].message.content

        logger.info(f"Groq response generated: {len(response_text)} chars in {elapsed:.2f}s")

        # Validate response is complete
        if not response_text.endswith((".", "!", "?")):
            logger.warning(f"Groq response may be truncated (no ending punctuation): {response_text[-50:]}")

        return response_text

    except Exception as e:
        logger.error(f"Groq API error: {e}", exc_info=True)
        return None


def generate_contextual_response(
    query: str,
    verses: list[dict],
    language: str = "en",
) -> Optional[str]:
    """Generate a contextual response using available LLMs.

    Tries Groq first (more reliable), falls back to Gemini if failed.

    Args:
        query: User's search query
        verses: List of verse result dictionaries
        language: Response language ('en' or 'ko')

    Returns:
        Generated response string or None if all providers failed
    """
    if not verses:
        return None

    # Try Groq first (more reliable complete responses)
    response = generate_response_groq(query, verses, language)
    if response:
        return response

    # Fall back to Gemini
    response = generate_response_gemini(query, verses, language)
    if response:
        return response

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
