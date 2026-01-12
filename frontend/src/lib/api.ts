/**
 * API client for Bible RAG backend.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  SearchRequest,
  SearchResponse,
  ThemeRequest,
  ThemeResponse,
  VerseDetailResponse,
  TranslationsResponse,
  BooksResponse,
  HealthResponse,
  APIError,
} from '@/types';

// API base URL from environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Error handler
function handleError(error: AxiosError): never {
  if (error.response) {
    const data = error.response.data as { error?: APIError };
    if (data.error) {
      throw new Error(data.error.message);
    }
    throw new Error(`API error: ${error.response.status}`);
  } else if (error.request) {
    throw new Error('No response from server. Please check your connection.');
  } else {
    throw new Error(error.message);
  }
}

/**
 * Semantic search for Bible verses.
 */
export async function searchVerses(request: SearchRequest): Promise<SearchResponse> {
  try {
    const response = await api.post<SearchResponse>('/api/search', request);
    return response.data;
  } catch (error) {
    handleError(error as AxiosError);
  }
}

/**
 * Get a specific verse by reference.
 */
export async function getVerse(
  book: string,
  chapter: number,
  verse: number,
  translations?: string[],
  includeOriginal: boolean = false,
): Promise<VerseDetailResponse> {
  try {
    const params = new URLSearchParams();
    if (translations?.length) {
      params.set('translations', translations.join(','));
    }
    params.set('include_original', String(includeOriginal));

    const response = await api.get<VerseDetailResponse>(
      `/api/verse/${encodeURIComponent(book)}/${chapter}/${verse}?${params.toString()}`
    );
    return response.data;
  } catch (error) {
    handleError(error as AxiosError);
  }
}

/**
 * Thematic search.
 */
export async function searchThemes(request: ThemeRequest): Promise<ThemeResponse> {
  try {
    const response = await api.post<ThemeResponse>('/api/themes', request);
    return response.data;
  } catch (error) {
    handleError(error as AxiosError);
  }
}

/**
 * Get all available translations.
 */
export async function getTranslations(language?: string): Promise<TranslationsResponse> {
  try {
    const params = language ? `?language=${language}` : '';
    const response = await api.get<TranslationsResponse>(`/api/translations${params}`);
    return response.data;
  } catch (error) {
    handleError(error as AxiosError);
  }
}

/**
 * Get all Bible books.
 */
export async function getBooks(
  testament?: 'OT' | 'NT',
  genre?: string,
): Promise<BooksResponse> {
  try {
    const params = new URLSearchParams();
    if (testament) params.set('testament', testament);
    if (genre) params.set('genre', genre);

    const queryString = params.toString();
    const url = `/api/books${queryString ? `?${queryString}` : ''}`;

    const response = await api.get<BooksResponse>(url);
    return response.data;
  } catch (error) {
    handleError(error as AxiosError);
  }
}

/**
 * Health check.
 */
export async function checkHealth(): Promise<HealthResponse> {
  try {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  } catch (error) {
    handleError(error as AxiosError);
  }
}

export default api;
