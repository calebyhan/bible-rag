'use client';

import { useState } from 'react';
import { SearchResponse } from '@/types';
import VerseCard from './VerseCard';
import AIResponse from './AIResponse';

interface SearchResultsProps {
  results: SearchResponse | null;
  isLoading?: boolean;
  query?: string;
  defaultTranslation?: string;
}

export default function SearchResults({ results, isLoading = false, query, defaultTranslation = 'NIV' }: SearchResultsProps) {
  const [showLanguage, setShowLanguage] = useState<'default' | 'all'>('default');

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto mt-8">
        <div className="flex flex-col items-center justify-center py-12">
          <div className="spinner w-8 h-8" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Searching...</p>
        </div>
      </div>
    );
  }

  if (!results) return null;

  const { results: verses, ai_response, ai_error, search_metadata, query_time_ms } = results;

  return (
    <div className="max-w-4xl mx-auto mt-8">
      {/* Search stats and controls */}
      <div className="flex items-center justify-between mb-4 text-sm text-gray-600 dark:text-gray-400">
        <span>
          {search_metadata.total_results} result{search_metadata.total_results !== 1 ? 's' : ''} found
          {query && <span className="ml-1">for &quot;{query}&quot;</span>}
        </span>

        <div className="flex items-center gap-3">
          {/* Language toggle */}
          <div className="flex items-center gap-1 bg-gray-100 dark:bg-slate-800 rounded-full p-1">
            <button
              onClick={() => setShowLanguage('default')}
              className={`px-3 py-1 rounded-full text-xs transition-colors ${
                showLanguage === 'default'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-700'
              }`}
            >
              Default
            </button>
            <button
              onClick={() => setShowLanguage('all')}
              className={`px-3 py-1 rounded-full text-xs transition-colors ${
                showLanguage === 'all'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-700'
              }`}
            >
              All
            </button>
          </div>

          <span>
            {query_time_ms}ms
            {search_metadata.cached && (
              <span className="ml-2 px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full text-xs">
                cached
              </span>
            )}
          </span>
        </div>
      </div>

      {/* AI Response */}
      {ai_response && <AIResponse response={ai_response} />}

      {/* AI Error Message */}
      {ai_error && !ai_response && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 text-yellow-600 dark:text-yellow-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                {ai_error}
              </p>
              {verses.length > 0 && (
                <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                  Showing verse results below.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Results list */}
      {verses.length > 0 ? (
        <div className="space-y-4">
          {verses.map((verse, index) => (
            <VerseCard
              key={`${verse.reference.book}-${verse.reference.chapter}-${verse.reference.verse}-${index}`}
              result={verse}
              showAllTranslations={showLanguage === 'all'}
              defaultTranslation={defaultTranslation}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-gray-400 dark:text-gray-600 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200">No results found</h3>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Try a different search query or adjust your filters.</p>
        </div>
      )}
    </div>
  );
}
