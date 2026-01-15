'use client';

import { SearchResponse } from '@/types';
import VerseCard from './VerseCard';
import AIResponse from './AIResponse';

interface SearchResultsProps {
  results: SearchResponse | null;
  isLoading?: boolean;
  query?: string;
}

export default function SearchResults({ results, isLoading = false, query }: SearchResultsProps) {
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

  const { results: verses, ai_response, search_metadata, query_time_ms } = results;

  return (
    <div className="max-w-4xl mx-auto mt-8">
      {/* Search stats */}
      <div className="flex items-center justify-between mb-4 text-sm text-gray-600 dark:text-gray-400">
        <span>
          {search_metadata.total_results} result{search_metadata.total_results !== 1 ? 's' : ''} found
          {query && <span className="ml-1">for &quot;{query}&quot;</span>}
        </span>
        <span>
          {query_time_ms}ms
          {search_metadata.cached && (
            <span className="ml-2 px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full text-xs">
              cached
            </span>
          )}
        </span>
      </div>

      {/* AI Response */}
      {ai_response && <AIResponse response={ai_response} />}

      {/* Results list */}
      {verses.length > 0 ? (
        <div className="space-y-4">
          {verses.map((verse, index) => (
            <VerseCard key={`${verse.reference.book}-${verse.reference.chapter}-${verse.reference.verse}-${index}`} result={verse} />
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
