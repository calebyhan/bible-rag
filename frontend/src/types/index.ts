/**
 * TypeScript types for Bible RAG frontend.
 */

// --- Verse Types ---

export interface VerseReference {
  book: string;
  book_korean?: string;
  book_abbrev?: string;
  chapter: number;
  verse: number;
  testament?: string;
  genre?: string;
}

export interface OriginalWord {
  word: string;
  transliteration?: string;
  strongs?: string;
  morphology?: string;
  definition?: string;
}

export interface OriginalLanguageData {
  language: string;
  words: OriginalWord[];
}

export interface CrossReference {
  book: string;
  book_korean?: string;
  chapter: number;
  verse: number;
  relationship: string;
  confidence?: number;
}

export interface VerseContext {
  chapter: number;
  verse: number;
  text: string;
}

// --- Search Types ---

export interface SearchFilters {
  testament?: 'OT' | 'NT' | 'both';
  genre?: string;
  books?: string[];
}

export interface SearchRequest {
  query: string;
  languages: string[];
  translations: string[];
  include_original?: boolean;
  max_results?: number;
  search_type?: 'semantic' | 'keyword';
  filters?: SearchFilters;
}

export interface SearchResult {
  reference: VerseReference;
  translations: Record<string, string>;
  relevance_score: number;
  cross_references?: CrossReference[];
  original?: OriginalLanguageData;
}

export interface SearchMetadata {
  total_results: number;
  embedding_model?: string;
  generation_model?: string;
  cached: boolean;
  error?: string;
}

export interface SearchResponse {
  query_time_ms: number;
  results: SearchResult[];
  ai_response?: string;
  search_metadata: SearchMetadata;
}

// --- Theme Types ---

export interface ThemeRequest {
  theme: string;
  testament?: 'OT' | 'NT' | 'both';
  languages: string[];
  translations: string[];
  max_results?: number;
}

export interface ThemeResponse {
  theme: string;
  testament_filter?: string;
  query_time_ms: number;
  results: SearchResult[];
  related_themes?: string[];
  total_results: number;
}

// --- Verse Detail Types ---

export interface VerseDetailResponse {
  reference: VerseReference;
  translations: Record<string, string>;
  original?: OriginalLanguageData;
  cross_references?: CrossReference[];
  context?: {
    previous?: VerseContext;
    next?: VerseContext;
  };
}

// --- Translation Types ---

export interface Translation {
  id: string;
  name: string;
  abbreviation: string;
  language_code: string;
  language_name?: string;
  description?: string;
  is_original_language: boolean;
  verse_count?: number;
}

export interface TranslationsResponse {
  translations: Translation[];
  total_count: number;
}

// --- Book Types ---

export interface Book {
  id: string;
  name: string;
  name_korean?: string;
  abbreviation: string;
  testament: string;
  genre?: string;
  book_number: number;
  total_chapters: number;
  total_verses?: number;
}

export interface BooksResponse {
  books: Book[];
  total_count: number;
}

// --- Health Types ---

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  services: Record<string, string>;
  stats?: Record<string, number>;
  errors?: string[];
}

// --- Error Types ---

export interface APIError {
  code: string;
  message: string;
  details?: Record<string, string>;
}
