'use client';

import { useState } from 'react';
import Link from 'next/link';
import { searchThemes } from '@/lib/api';
import { ThemeResponse, SearchResult } from '@/types';
import VerseCard from '@/components/VerseCard';

const POPULAR_THEMES = [
  { theme: 'love and compassion', label: 'Love & Compassion', emoji: '💖' },
  { theme: 'faith and trust', label: 'Faith & Trust', emoji: '🙏' },
  { theme: 'forgiveness', label: 'Forgiveness', emoji: '✨' },
  { theme: 'hope and encouragement', label: 'Hope', emoji: '🌟' },
  { theme: 'wisdom and guidance', label: 'Wisdom', emoji: '📚' },
  { theme: 'prayer', label: 'Prayer', emoji: '🕊️' },
  { theme: 'salvation and redemption', label: 'Salvation', emoji: '⛪' },
  { theme: 'peace', label: 'Peace', emoji: '🕊️' },
];

const TRANSLATIONS = [
  { abbrev: 'NIV', name: 'NIV', language: 'en' },
  { abbrev: 'ESV', name: 'ESV', language: 'en' },
  { abbrev: 'RKV', name: '개역개정', language: 'ko' },
  { abbrev: 'KRV', name: '개역한글', language: 'ko' },
];

export default function ThemesPage() {
  const [theme, setTheme] = useState('');
  const [testament, setTestament] = useState<'OT' | 'NT' | 'both'>('both');
  const [selectedTranslations, setSelectedTranslations] = useState<string[]>(['NIV', 'RKV']);
  const [results, setResults] = useState<ThemeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (themeQuery: string) => {
    if (!themeQuery.trim()) return;

    setIsLoading(true);
    setError(null);
    setTheme(themeQuery);

    try {
      const response = await searchThemes({
        theme: themeQuery,
        testament,
        languages: ['en', 'ko'],
        translations: selectedTranslations,
        max_results: 15,
      });
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(theme);
  };

  const toggleTranslation = (abbrev: string) => {
    setSelectedTranslations((prev) => {
      if (prev.includes(abbrev)) {
        if (prev.length === 1) return prev;
        return prev.filter((t) => t !== abbrev);
      }
      return [...prev, abbrev];
    });
  };

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-slate-900">
      {/* Header */}
      <div className="bg-gradient-to-br from-purple-600 via-purple-700 to-indigo-800 text-white">
        <div className="container mx-auto px-4 py-12 md:py-16">
          <div className="max-w-4xl mx-auto">
            {/* Navigation */}
            <div className="flex justify-between items-center mb-6">
              <Link
                href="/"
                className="inline-flex items-center gap-2 text-purple-100 hover:text-white transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span>Back to Search</span>
              </Link>
              <div className="flex gap-2">
                <Link
                  href="/browse"
                  className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition-colors"
                >
                  📖 Browse
                </Link>
                <Link
                  href="/compare"
                  className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition-colors"
                >
                  ⚖️ Compare
                </Link>
              </div>
            </div>

            <div className="text-center mb-8">
              <h1 className="text-4xl md:text-5xl font-bold mb-4">Thematic Search</h1>
              <p className="text-xl text-purple-100 max-w-2xl mx-auto">
                Explore biblical themes across the Old and New Testaments
              </p>
              <p className="text-purple-200 mt-2">
                구약과 신약을 통해 성경 주제 탐색하기
              </p>
            </div>

            {/* Search form */}
            <form onSubmit={handleSubmit} className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  placeholder="Enter a theme (e.g., 'love', 'faith', 'forgiveness')..."
                  className="w-full px-6 py-4 text-lg rounded-2xl shadow-lg focus:ring-4 focus:ring-purple-300 outline-none text-gray-800"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !theme.trim()}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2.5 bg-purple-600 text-white rounded-xl hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {isLoading ? 'Searching...' : 'Search'}
                </button>
              </div>

              {/* Testament filter */}
              <div className="mt-4 flex items-center justify-center gap-4">
                <span className="text-purple-100 text-sm font-medium">Testament:</span>
                <div className="flex gap-2">
                  {(['both', 'OT', 'NT'] as const).map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setTestament(t)}
                      className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                        testament === t
                          ? 'bg-white text-purple-700'
                          : 'bg-purple-700/50 text-purple-100 hover:bg-purple-700/70'
                      }`}
                    >
                      {t === 'both' ? 'Both' : t}
                    </button>
                  ))}
                </div>
              </div>

              {/* Translation filter */}
              <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
                <span className="text-purple-100 text-sm font-medium">Translations:</span>
                {TRANSLATIONS.map((trans) => (
                  <button
                    key={trans.abbrev}
                    type="button"
                    onClick={() => toggleTranslation(trans.abbrev)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      selectedTranslations.includes(trans.abbrev)
                        ? 'bg-white text-purple-700'
                        : 'bg-purple-700/50 text-purple-100 hover:bg-purple-700/70'
                    }`}
                  >
                    {trans.name}
                  </button>
                ))}
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Popular themes */}
      {!results && !isLoading && !error && (
        <div className="container mx-auto px-4 py-12">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6 text-center">
              Popular Themes
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {POPULAR_THEMES.map((t) => (
                <button
                  key={t.theme}
                  onClick={() => handleSearch(t.theme)}
                  className="p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700 hover:shadow-md hover:border-purple-200 dark:hover:border-purple-600 transition-all text-center group"
                >
                  <div className="text-4xl mb-2">{t.emoji}</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100 group-hover:text-purple-700 dark:group-hover:text-purple-400">
                    {t.label}
                  </div>
                </button>
              ))}
            </div>

            {/* Info section */}
            <div className="mt-12 bg-white dark:bg-slate-800 rounded-xl p-8 shadow-sm border border-gray-100 dark:border-slate-700">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                What is Thematic Search?
              </h3>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                Thematic search helps you explore specific topics or concepts throughout the Bible.
                Unlike keyword search, it understands the meaning and context of themes, finding
                relevant passages even when they use different words.
              </p>
              <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-purple-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>Search by concept, not just keywords</span>
                </div>
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-purple-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>Filter by Old Testament, New Testament, or both</span>
                </div>
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-purple-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>View results in multiple translations simultaneously</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="container mx-auto px-4 py-12">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-block w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mb-4"></div>
            <p className="text-gray-700 dark:text-gray-300">Searching for verses about "{theme}"...</p>
          </div>
        </div>
      )}

      {/* Results */}
      {results && !isLoading && (
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            {/* Results header */}
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Results for "{results.theme}"
                </h2>
                <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                  {results.total_results} verses found
                  {results.testament_filter && ` in ${results.testament_filter}`}
                  {' · '}
                  {results.query_time_ms}ms
                </p>
              </div>
              <button
                onClick={() => {
                  setResults(null);
                  setTheme('');
                }}
                className="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium"
              >
                New Search
              </button>
            </div>

            {/* Verse cards */}
            <div className="space-y-4">
              {results.results.map((result: SearchResult, idx: number) => (
                <VerseCard
                  key={`${result.reference.book}-${result.reference.chapter}-${result.reference.verse}-${idx}`}
                  result={result}
                />
              ))}
            </div>

            {/* Related themes (if available) */}
            {results.related_themes && results.related_themes.length > 0 && (
              <div className="mt-8 p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Related Themes
                </h3>
                <div className="flex flex-wrap gap-2">
                  {results.related_themes.map((relatedTheme) => (
                    <button
                      key={relatedTheme}
                      onClick={() => handleSearch(relatedTheme)}
                      className="px-4 py-2 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm font-medium hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-colors"
                    >
                      {relatedTheme}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
