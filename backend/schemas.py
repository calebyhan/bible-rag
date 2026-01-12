"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request Schemas ---


class SearchFilters(BaseModel):
    """Filters for search requests."""

    testament: Optional[str] = Field(
        None,
        description="Filter by testament: 'OT', 'NT', or 'both'",
        pattern="^(OT|NT|both)$",
    )
    genre: Optional[str] = Field(
        None,
        description="Filter by genre: law, history, wisdom, poetry, prophecy, gospel, epistle",
    )
    books: Optional[list[str]] = Field(
        None,
        description="Filter by book abbreviations",
    )


class SearchRequest(BaseModel):
    """Request schema for semantic search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query text",
    )
    languages: list[str] = Field(
        default=["en"],
        description="Language codes for response (en, ko)",
    )
    translations: list[str] = Field(
        ...,
        min_length=1,
        description="Translation abbreviations to search",
    )
    include_original: bool = Field(
        default=False,
        description="Include original language (Greek/Hebrew) data",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results",
    )
    search_type: str = Field(
        default="semantic",
        pattern="^(semantic|keyword)$",
        description="Search type: semantic or keyword",
    )
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Optional filters",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "love and forgiveness",
                    "languages": ["en"],
                    "translations": ["NIV"],
                    "max_results": 10,
                }
            ]
        }
    }


class ThemeRequest(BaseModel):
    """Request schema for thematic search."""

    theme: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Theme keyword or phrase",
    )
    testament: str = Field(
        default="both",
        pattern="^(OT|NT|both)$",
        description="Testament filter",
    )
    languages: list[str] = Field(
        default=["en"],
        description="Language codes",
    )
    translations: list[str] = Field(
        ...,
        min_length=1,
        description="Translation abbreviations",
    )
    max_results: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum results",
    )


# --- Response Schemas ---


class VerseReference(BaseModel):
    """Verse reference information."""

    book: str
    book_korean: Optional[str] = None
    book_abbrev: Optional[str] = None
    chapter: int
    verse: int
    testament: Optional[str] = None
    genre: Optional[str] = None


class OriginalWord(BaseModel):
    """Original language word data."""

    word: str
    transliteration: Optional[str] = None
    strongs: Optional[str] = None
    morphology: Optional[str] = None
    definition: Optional[str] = None


class OriginalLanguageData(BaseModel):
    """Original language data for a verse."""

    language: str
    words: list[OriginalWord]


class CrossReferenceItem(BaseModel):
    """Cross-reference to another verse."""

    book: str
    book_korean: Optional[str] = None
    chapter: int
    verse: int
    relationship: str
    confidence: Optional[float] = None


class VerseContext(BaseModel):
    """Context around a verse (previous/next)."""

    chapter: int
    verse: int
    text: str


class SearchResult(BaseModel):
    """Individual search result."""

    reference: VerseReference
    translations: dict[str, str]
    relevance_score: float
    cross_references: Optional[list[CrossReferenceItem]] = None
    original: Optional[OriginalLanguageData] = None


class SearchMetadata(BaseModel):
    """Metadata about the search."""

    total_results: int
    embedding_model: Optional[str] = None
    generation_model: Optional[str] = None
    cached: bool = False
    error: Optional[str] = None


class SearchResponse(BaseModel):
    """Response schema for search endpoint."""

    query_time_ms: int
    results: list[SearchResult]
    ai_response: Optional[str] = None
    search_metadata: SearchMetadata


class VerseDetailResponse(BaseModel):
    """Response schema for verse detail endpoint."""

    reference: VerseReference
    translations: dict[str, str]
    original: Optional[OriginalLanguageData] = None
    cross_references: Optional[list[CrossReferenceItem]] = None
    context: Optional[dict[str, Optional[VerseContext]]] = None


class TranslationInfo(BaseModel):
    """Translation information."""

    id: UUID
    name: str
    abbreviation: str
    language_code: str
    language_name: Optional[str] = None
    description: Optional[str] = None
    is_original_language: bool
    verse_count: Optional[int] = None


class TranslationsResponse(BaseModel):
    """Response schema for translations list."""

    translations: list[TranslationInfo]
    total_count: int


class BookInfo(BaseModel):
    """Book information."""

    id: UUID
    name: str
    name_korean: Optional[str] = None
    abbreviation: str
    testament: str
    genre: Optional[str] = None
    book_number: int
    total_chapters: int
    total_verses: Optional[int] = None


class BooksResponse(BaseModel):
    """Response schema for books list."""

    books: list[BookInfo]
    total_count: int


class ServiceStatus(BaseModel):
    """Status of an individual service."""

    status: str = Field(description="'healthy' or 'unhealthy'")
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response schema for health check."""

    status: str
    timestamp: datetime
    version: str = "1.0.0"
    services: dict[str, str]
    stats: Optional[dict] = None
    errors: Optional[list[str]] = None


class ErrorDetail(BaseModel):
    """Error detail information."""

    field: Optional[str] = None
    issue: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: dict = Field(
        ...,
        description="Error details",
        json_schema_extra={
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": {"field": "query", "issue": "Query is required"},
            }
        },
    )


# --- Theme Response ---


class ThemeResponse(BaseModel):
    """Response schema for theme search."""

    theme: str
    testament_filter: Optional[str] = None
    query_time_ms: int
    results: list[SearchResult]
    related_themes: Optional[list[str]] = None
    total_results: int
