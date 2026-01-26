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

// API key storage keys
const GEMINI_API_KEY_STORAGE = 'bible-rag-gemini-api-key';
const GROQ_API_KEY_STORAGE = 'bible-rag-groq-api-key';

// API key management
export function setGeminiApiKey(apiKey: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(GEMINI_API_KEY_STORAGE, apiKey);
  }
}

export function getGeminiApiKey(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(GEMINI_API_KEY_STORAGE);
  }
  return null;
}

export function removeGeminiApiKey(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(GEMINI_API_KEY_STORAGE);
  }
}

export function setGroqApiKey(apiKey: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(GROQ_API_KEY_STORAGE, apiKey);
  }
}

export function getGroqApiKey(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(GROQ_API_KEY_STORAGE);
  }
  return null;
}

export function removeGroqApiKey(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(GROQ_API_KEY_STORAGE);
  }
}

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Add request interceptor to include API keys from localStorage
api.interceptors.request.use(
  (config) => {
    const geminiKey = getGeminiApiKey();
    const groqKey = getGroqApiKey();

    if (geminiKey) {
      config.headers['X-Gemini-API-Key'] = geminiKey;
    }
    if (groqKey) {
      config.headers['X-Groq-API-Key'] = groqKey;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

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
/**
 * Semantic search for Bible verses with streaming support.
 */
export async function searchVerses(request: SearchRequest): Promise<SearchResponse> {
  // Legacy support or fallback if needed. Ideally page.tsx switches to streamSearchVerses.
  // For now, we can wrap the stream to return a full promise, OR update page.tsx to use streamSearchVerses.
  // Given the backend now returns stream, this standard axios call might fail or buffer everything.
  // If backend returns NDJSON, axios parses it as one big string or JSON?
  // Axios will fail JSON parsing if multiple JSON objects are concatenated without array.
  // So searchVerses MUST be updated to handle NDJSON buffering if we want to keep the signature,
  // OR we just abandon searchVerses for the main flow.
  // Let's implement buffering here for compatibility:

  return new Promise((resolve, reject) => {
    let finalResults: any = null;
    let fullTokenText = "";

    streamSearchVerses(request, {
      onResults: (data) => { finalResults = data; },
      onToken: (token) => { fullTokenText += token; },
      onError: (msg) => reject(new Error(msg)),
      onComplete: () => {
        if (finalResults) {
          finalResults.ai_response = fullTokenText || null;
          resolve(finalResults);
        } else {
          reject(new Error("No results received"));
        }
      }
    }).catch(reject);
  });
}

export interface StreamCallbacks {
  onResults?: (results: SearchResponse) => void;
  onToken?: (token: string) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}

export async function streamSearchVerses(
  request: SearchRequest,
  callbacks: StreamCallbacks
): Promise<void> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const geminiKey = getGeminiApiKey();
  const groqKey = getGroqApiKey();

  if (geminiKey) headers['X-Gemini-API-Key'] = geminiKey;
  if (groqKey) headers['X-Groq-API-Key'] = groqKey;

  try {
    const response = await fetch(`${API_BASE_URL}/api/search`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    if (!response.body) return;

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const msg = JSON.parse(line);
          if (msg.type === 'results') {
            callbacks.onResults?.(msg.data);
          } else if (msg.type === 'token') {
            callbacks.onToken?.(msg.content);
          } else if (msg.type === 'error') {
            callbacks.onError?.(msg.message);
          }
        } catch (e) {
          console.error('JSON parse error', e);
        }
      }
    }

    callbacks.onComplete?.();

  } catch (error) {
    callbacks.onError?.(error instanceof Error ? error.message : String(error));
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

    const url = `/api/verse/${encodeURIComponent(book)}/${chapter}/${verse}?${params.toString()}`;
    const response = await api.get<VerseDetailResponse>(url);
    return response.data;
  } catch (error) {
    handleError(error as AxiosError);
  }
}

/**
 * Get an entire chapter with all verses.
 */
export async function getChapter(
  book: string,
  chapter: number,
  translations?: string[],
  includeOriginal: boolean = false,
): Promise<any> {
  try {
    const params = new URLSearchParams();
    if (translations?.length) {
      params.set('translations', translations.join(','));
    }
    params.set('include_original', String(includeOriginal));

    const response = await api.get(
      `/api/chapter/${encodeURIComponent(book)}/${chapter}?${params.toString()}`
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
 * Results are cached in memory to avoid repeated API calls.
 */
let translationsCache: TranslationsResponse | null = null;
let translationsCachePromise: Promise<TranslationsResponse> | null = null;

export async function getTranslations(language?: string): Promise<TranslationsResponse> {
  // If filtering by language, skip cache and fetch fresh
  if (language) {
    try {
      const response = await api.get<TranslationsResponse>(`/api/translations?language=${language}`);
      return response.data;
    } catch (error) {
      handleError(error as AxiosError);
    }
  }

  // Return cached data if available
  if (translationsCache) {
    return translationsCache;
  }

  // If a fetch is already in progress, wait for it
  if (translationsCachePromise) {
    return translationsCachePromise;
  }

  // Fetch and cache
  translationsCachePromise = (async () => {
    try {
      const response = await api.get<TranslationsResponse>('/api/translations');
      translationsCache = response.data;
      return response.data;
    } catch (error) {
      translationsCachePromise = null; // Clear on error to allow retry
      handleError(error as AxiosError);
    }
  })();

  return translationsCachePromise;
}

/**
 * Preload translations into cache.
 * Call this early (e.g., in layout) to have data ready before components need it.
 */
export function preloadTranslations(): void {
  if (!translationsCache && !translationsCachePromise) {
    getTranslations().catch(() => { }); // Fire and forget, errors handled in getTranslations
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
