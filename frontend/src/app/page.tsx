'use client';

import { useState } from 'react';
import SearchBar from '@/components/SearchBar';
import SearchResults from '@/components/SearchResults';
import { searchVerses } from '@/lib/api';
import { SearchResponse } from '@/types';

export default function Home() {
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const [defaultTranslation, setDefaultTranslation] = useState<string>('NIV');
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (query: string, translations: string[], defaultTrans: string) => {
    setIsLoading(true);
    setError(null);
    setCurrentQuery(query);
    setDefaultTranslation(defaultTrans);

    try {
      const response = await searchVerses({
        query,
        languages: ['en', 'ko'],
        translations,
        max_results: 10,
        include_original: false,
      });
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen">
      {/* Hero section */}
      <div className="bg-gradient-to-br from-primary-600 via-primary-700 to-blue-800 text-white">
        <div className="container mx-auto px-4 py-16 md:py-24">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Bible RAG</h1>
            <p className="text-xl text-primary-100 max-w-2xl mx-auto">
              Multilingual semantic search across English and Korean Bible translations
            </p>
            <p className="text-primary-200 mt-2">
              다국어 의미 검색 - 영어와 한국어 성경 번역본
            </p>
          </div>

          {/* Search bar */}
          <SearchBar
            onSearch={handleSearch}
            isLoading={isLoading}
            placeholder="What does the Bible say about...  성경에서 무엇을 찾고 계신가요?"
          />
        </div>
      </div>

      {/* Results section */}
      <div className="container mx-auto px-4 py-8">
        {error && (
          <div className="max-w-4xl mx-auto mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        <SearchResults results={results} isLoading={isLoading} query={currentQuery} defaultTranslation={defaultTranslation} />

        {/* Initial state - no search yet */}
        {!results && !isLoading && !error && (
          <div className="max-w-4xl mx-auto text-center py-12">
            <div className="text-gray-400 dark:text-gray-500 mb-6">
              <svg className="w-24 h-24 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
            </div>
            <h2 className="text-xl font-medium text-gray-700 dark:text-gray-200 mb-2">Search the Bible</h2>
            <p className="text-gray-600 dark:text-gray-300 max-w-md mx-auto">
              Enter a question or topic to find relevant verses using AI-powered semantic search.
              Supports both English and Korean.
            </p>

            {/* Features */}
            <div className="mt-12 grid md:grid-cols-3 gap-6 text-left">
              <div className="p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700">
                <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-5 h-5 text-primary-600 dark:text-primary-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Semantic Search</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Find verses by meaning, not just keywords. Ask questions in natural language.
                </p>
              </div>

              <div className="p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700">
                <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-5 h-5 text-primary-600 dark:text-primary-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Multilingual</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Search in English or Korean. Compare translations side by side.
                </p>
              </div>

              <div className="p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700">
                <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-5 h-5 text-primary-600 dark:text-primary-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">AI Insights</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Get contextual explanations powered by AI to deepen your understanding.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
