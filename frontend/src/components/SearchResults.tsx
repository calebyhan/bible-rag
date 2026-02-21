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
      <div className="text-center py-space-lg">
        <div className="spinner w-6 h-6 mx-auto mb-4" />
        <p className="font-body text-lg text-text-secondary italic">Searching the Scriptures...</p>
      </div>
    );
  }

  if (!results) return null;

  const { results: verses, ai_response, ai_error, search_metadata, query_time_ms } = results;

  return (
    <div>
      {/* Search stats and controls */}
      <div className="flex items-center justify-between mb-space-md pb-space-sm border-b border-border-light">
        <div className="font-ui text-sm text-text-secondary">
          <span className="text-text-primary font-medium">{search_metadata.total_results}</span> result{search_metadata.total_results !== 1 ? 's' : ''}
          {query && <span className="ml-1">for "{query}"</span>}
        </div>

        <div className="flex items-center gap-4">
          {/* Language toggle - minimal buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowLanguage('default')}
              className={`font-ui text-xs uppercase tracking-wide transition-colors pb-1 ${
                showLanguage === 'default'
                  ? 'text-text-primary border-b-2 border-text-primary'
                  : 'text-text-tertiary hover:text-text-secondary border-b-2 border-transparent'
              }`}
            >
              Default
            </button>
            <button
              onClick={() => setShowLanguage('all')}
              className={`font-ui text-xs uppercase tracking-wide transition-colors pb-1 ${
                showLanguage === 'all'
                  ? 'text-text-primary border-b-2 border-text-primary'
                  : 'text-text-tertiary hover:text-text-secondary border-b-2 border-transparent'
              }`}
            >
              All
            </button>
          </div>

          <span className="font-ui text-xs text-text-tertiary">
            {query_time_ms}ms
            {search_metadata.cached && (
              <span className="ml-2 text-success">• cached</span>
            )}
          </span>
        </div>
      </div>

      {/* AI Response */}
      {ai_response && <AIResponse response={ai_response} />}

      {/* AI Error Message */}
      {ai_error && !ai_response && (
        <div className="border-2 border-warning bg-surface p-4 mb-space-md">
          <p className="font-ui text-xs uppercase tracking-wide text-warning mb-1">Warning</p>
          <p className="font-body text-sm text-text-secondary">
            {ai_error}
          </p>
          {verses.length > 0 && (
            <p className="font-ui text-xs text-text-tertiary mt-2 italic">
              Showing verse results below.
            </p>
          )}
        </div>
      )}

      {/* Results list */}
      {verses.length > 0 ? (
        <div className="space-y-4">
          {verses.map((verse, index) => (
            <VerseCard
              key={`${verse.reference.book}-${verse.reference.chapter}-${verse.reference.verse}`}
              result={verse}
              showAllTranslations={showLanguage === 'all'}
              defaultTranslation={defaultTranslation}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-space-xl">
          <p className="font-body text-lg text-text-secondary italic mb-2">
            No results found.
          </p>
          <p className="font-ui text-sm text-text-tertiary">
            Try a different search query or adjust your translation selections.
          </p>
        </div>
      )}
    </div>
  );
}
