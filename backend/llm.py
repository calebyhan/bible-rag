"""LLM integration for generating contextual responses.

Supports Google Gemini (primary) and Groq (fallback) for generating
AI-powered contextual responses based on search results.
"""

import time
from typing import Optional

from config import get_settings

settings = get_settings()

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
    # Format verses for context
    verse_context = []
    for v in verses[:5]:  # Limit to top 5 for context
        ref = v.get("reference", {})
        translations = v.get("translations", {})

        # Get first available translation text
        text = next(iter(translations.values()), "")

        verse_context.append(
            f"- {ref.get('book', '')} {ref.get('chapter', '')}:{ref.get('verse', '')}: {text}"
        )

    verses_text = "\n".join(verse_context)

    if language == "ko":
        prompt = f"""다음 성경 구절들을 바탕으로 질문에 답변해 주세요.

질문: {query}

관련 성경 구절:
{verses_text}

위 구절들을 바탕으로 간결하고 명확한 답변을 한국어로 작성해 주세요.
답변은 2-3문장으로 제한하고, 성경적 맥락을 설명해 주세요."""
    else:
        prompt = f"""Based on the following Bible verses, please answer the question.

Question: {query}

Relevant Bible verses:
{verses_text}

Please provide a concise and clear answer based on these verses.
Limit your response to 2-3 sentences and explain the biblical context."""

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
        return None

    if not _check_rate_limit("gemini", settings.gemini_rpm):
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)

        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = _build_prompt(query, verses, language)

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=256,
                temperature=0.7,
            ),
        )

        return response.text

    except Exception as e:
        print(f"Gemini error: {e}")
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
        return None

    if not _check_rate_limit("groq", settings.groq_rpm):
        return None

    try:
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)

        prompt = _build_prompt(query, verses, language)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful Bible study assistant. Provide concise, accurate responses based on the provided verses.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=256,
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Groq error: {e}")
        return None


def generate_contextual_response(
    query: str,
    verses: list[dict],
    language: str = "en",
) -> Optional[str]:
    """Generate a contextual response using available LLMs.

    Tries Gemini first, falls back to Groq if rate limited or failed.

    Args:
        query: User's search query
        verses: List of verse result dictionaries
        language: Response language ('en' or 'ko')

    Returns:
        Generated response string or None if all providers failed
    """
    if not verses:
        return None

    # Try Gemini first
    response = generate_response_gemini(query, verses, language)
    if response:
        return response

    # Fall back to Groq
    response = generate_response_groq(query, verses, language)
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
