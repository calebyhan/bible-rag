'use client';

import { useState } from 'react';
import SearchBar from '@/components/SearchBar';
import SearchResults from '@/components/SearchResults';
import SearchMethodWarning from '@/components/SearchMethodWarning';
import { searchVerses } from '@/lib/api';
import { SearchResponse } from '@/types';

import { useSearchParams, useRouter } from 'next/navigation';
import { useEffect, useCallback, Suspense } from 'react';

// Wrap content in Suspense for useSearchParams
function HomeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const initialQuery = searchParams.get('q') || '';
  const initialTranslations = searchParams.get('t')?.split(',') || ['NIV', 'KRV'];
  const initialDefaultTranslation = searchParams.get('dt') || 'NIV';

  const [results, setResults] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuery, setCurrentQuery] = useState(initialQuery);
  const [defaultTranslation, setDefaultTranslation] = useState<string>(initialDefaultTranslation);
  const [error, setError] = useState<string | null>(null);

  // Perform search
  const performSearch = useCallback(async (query: string, translations: string[], defaultTrans: string) => {
    if (!query) return;

    setIsLoading(true);
    setError(null);
    setCurrentQuery(query);
    setDefaultTranslation(defaultTrans);
    setResults(null);

    try {
      // Use streaming API
      const { streamSearchVerses } = await import('@/lib/api');

      await streamSearchVerses({
        query,
        languages: ['en', 'ko'],
        translations,
        max_results: 10,
        include_original: false,
      }, {
        onResults: (data) => {
          setResults(data);
        },
        onToken: (token) => {
          setResults((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              ai_response: (prev.ai_response || '') + token
            };
          });
        },
        onError: (msg) => {
          setError(msg);
          setIsLoading(false);
        },
        onComplete: () => {
          setIsLoading(false);
        }
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setIsLoading(false);
    }
  }, []);

  // Initial search from URL
  useEffect(() => {
    if (initialQuery && !results && !isLoading) {
      performSearch(initialQuery, initialTranslations, initialDefaultTranslation);
    }
  }, [initialQuery, initialTranslations, initialDefaultTranslation, performSearch, results, isLoading]);

  const handleSearch = async (query: string, translations: string[], defaultTrans: string) => {
    // Update URL
    const params = new URLSearchParams();
    params.set('q', query);
    params.set('t', translations.join(','));
    params.set('dt', defaultTrans);
    router.push(`/?${params.toString()}`);

    // Perform search
    await performSearch(query, translations, defaultTrans);
  };

  return (
    <main className="min-h-screen bg-background dark:bg-background-dark transition-colors">
      {/* Search Method Warning */}
      <SearchMethodWarning searchMetadata={results?.search_metadata} />

      {/* Hero section - Minimal, Typography-Focused */}
      <div className="bg-surface dark:bg-surface-dark transition-colors">
        <div className="container-content py-space-xl">
          <div className="text-center mb-space-lg">
            <h1 className="font-serif text-4xl sm:text-5xl md:text-6xl tracking-tight text-text-primary dark:text-text-dark-primary mb-4">
              Bible RAG
            </h1>
            <p className="font-serif text-lg sm:text-xl text-text-secondary dark:text-text-dark-secondary mb-2">
              Semantic search across English and Korean translations
            </p>
            <p className="font-korean text-base sm:text-lg text-text-tertiary dark:text-text-dark-tertiary">
              다국어 의미 검색
            </p>
          </div>

          {/* Search bar */}
          <SearchBar
            onSearch={handleSearch}
            isLoading={isLoading}
            placeholder="What does the Bible say about..."
          />
        </div>
      </div>

      {/* Results section */}
      <div className="container-content py-space-lg">
        {error && (
          <div className="mb-space-md p-4 border-2 border-error dark:border-error-dark bg-surface dark:bg-surface-dark transition-colors">
            <p className="font-ui text-sm font-medium text-error dark:text-error-dark uppercase tracking-wide">Error / 오류</p>
            <p className="font-body text-sm text-text-secondary dark:text-text-dark-secondary mt-1">{error}</p>
          </div>
        )}

        <SearchResults results={results} isLoading={isLoading} query={currentQuery} defaultTranslation={defaultTranslation} />

        {/* Initial state - no search yet */}
        {!results && !isLoading && !error && (
          <div className="text-center py-space-xl">
            <p className="font-body text-lg text-text-secondary dark:text-text-dark-secondary italic">
              Enter a question or topic to search the Scriptures.
            </p>
            <p className="font-korean text-base text-text-tertiary dark:text-text-dark-tertiary mt-2">
              질문이나 주제를 입력하여 성경을 검색하세요.
            </p>
          </div>
        )}
      </div>
    </main>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background dark:bg-background-dark flex items-center justify-center text-text-primary dark:text-text-dark-primary">Loading...</div>}>
      <HomeContent />
    </Suspense>
  );
}
