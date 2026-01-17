'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { searchThemes, getTranslations } from '@/lib/api';
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

interface Translation {
  abbrev: string;
  name: string;
  language: string;
}

export default function ThemesPage() {
  const [theme, setTheme] = useState('');
  const [testament, setTestament] = useState<'OT' | 'NT' | 'both'>('both');
  const [selectedTranslations, setSelectedTranslations] = useState<string[]>(['NIV', 'NKRV']);
  const [defaultTranslation, setDefaultTranslation] = useState<string>('NIV');
  const [showLanguage, setShowLanguage] = useState<'default' | 'all'>('default');
  const [results, setResults] = useState<ThemeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [translations, setTranslations] = useState<Translation[]>([]);
  const [translationsLoading, setTranslationsLoading] = useState(true);

  // Fetch translations from API on mount
  useEffect(() => {
    const fetchTranslations = async () => {
      try {
        const response = await getTranslations();
        const mappedTranslations = response.translations
          .filter(t => !t.is_original_language)
          .map(t => ({
            abbrev: t.abbreviation,
            name: t.name,
            language: t.language_code,
          }));
        setTranslations(mappedTranslations);
      } catch (error) {
        console.error('Failed to fetch translations:', error);
        setTranslations([
          { abbrev: 'NIV', name: 'New International Version', language: 'en' },
          { abbrev: 'ESV', name: 'English Standard Version', language: 'en' },
          { abbrev: 'KJV', name: 'King James Version', language: 'en' },
          { abbrev: 'NKRV', name: '개역개정', language: 'ko' },
          { abbrev: 'KRV', name: '개역한글', language: 'ko' },
        ]);
      } finally {
        setTranslationsLoading(false);
      }
    };

    fetchTranslations();
  }, []);

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

  const toggleTranslation = (abbrev: string, isDoubleClick: boolean = false) => {
    const isSelected = selectedTranslations.includes(abbrev);
    const isDefault = abbrev === defaultTranslation;

    // Double-click: always set as default
    if (isDoubleClick) {
      setDefaultTranslation(abbrev);
      // Ensure it's selected
      if (!isSelected) {
        setSelectedTranslations((prev) => [...prev, abbrev]);
      }
      return;
    }

    // Single-click: toggle selection (but can't deselect the default)
    if (isSelected) {
      // Can't deselect if it's the only one
      if (selectedTranslations.length === 1) return;

      // Can't deselect if it's the default - must double-click another first
      if (isDefault) return;

      // Deselect it
      setSelectedTranslations((prev) => prev.filter((t) => t !== abbrev));
    } else {
      // Select it
      setSelectedTranslations((prev) => [...prev, abbrev]);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-slate-900">
      {/* Header */}
      <div className="bg-gradient-to-br from-purple-600 via-purple-700 to-indigo-800 text-white">
        <div className="container mx-auto px-4 py-12 md:py-16">
          <div className="max-w-4xl mx-auto">
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
                <span className="text-purple-100 text-sm font-medium">Testament / 성경:</span>
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
                <span className="text-purple-100 text-sm font-medium">Translations / 번역본:</span>
                {translationsLoading ? (
                  <span className="text-purple-200 text-xs">Loading...</span>
                ) : (
                  translations.map((trans) => {
                  const isSelected = selectedTranslations.includes(trans.abbrev);
                  const isDefault = trans.abbrev === defaultTranslation;

                  return (
                    <button
                      key={trans.abbrev}
                      type="button"
                      onClick={() => toggleTranslation(trans.abbrev, false)}
                      onDoubleClick={() => toggleTranslation(trans.abbrev, true)}
                      className={`px-3 py-1 rounded-full text-xs font-medium transition-colors flex items-center gap-1 ${
                        isSelected
                          ? 'bg-white text-purple-700 border-2 border-white'
                          : 'bg-purple-700/50 text-purple-100 hover:bg-purple-700/70 border-2 border-transparent'
                      } ${isDefault ? 'ring-2 ring-yellow-300' : ''}`}
                      title={isDefault ? `${trans.name} (Default)` : trans.name}
                    >
                      {isDefault && <span className="text-yellow-500">★</span>}
                      {trans.name}
                    </button>
                  );
                })
                )}
              </div>
              <p className="mt-2 text-xs text-center text-purple-200">
                Click to select/deselect • Double-click to set as default (★) • Default can't be deselected
              </p>
              <p className="text-xs text-center text-purple-200">
                클릭하여 선택/해제 • 더블클릭으로 기본값 설정 (★) • 기본값은 해제 불가
              </p>
            </form>
          </div>
        </div>
      </div>

      {/* Popular themes */}
      {!results && !isLoading && !error && (
        <div className="container mx-auto px-4 py-12">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6 text-center">
              Popular Themes / 인기 주제
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
                What is Thematic Search? / 주제별 검색이란?
              </h3>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                Thematic search helps you explore specific topics or concepts throughout the Bible.
                Unlike keyword search, it understands the meaning and context of themes, finding
                relevant passages even when they use different words.
              </p>
              <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm">
                주제별 검색은 성경 전체에서 특정 주제나 개념을 탐색하는 데 도움을 줍니다.
                키워드 검색과 달리 주제의 의미와 맥락을 이해하여 다른 단어를 사용하더라도 관련 구절을 찾습니다.
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
            <p className="font-medium">Error / 오류</p>
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
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
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
                <div className="flex items-center gap-3">
                  {/* Language toggle */}
                  <div className="flex items-center gap-1 bg-gray-100 dark:bg-slate-800 rounded-full p-1">
                    <button
                      onClick={() => setShowLanguage('default')}
                      className={`px-3 py-1 rounded-full text-xs transition-colors ${
                        showLanguage === 'default'
                          ? 'bg-purple-600 text-white'
                          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-700'
                      }`}
                    >
                      Default
                    </button>
                    <button
                      onClick={() => setShowLanguage('all')}
                      className={`px-3 py-1 rounded-full text-xs transition-colors ${
                        showLanguage === 'all'
                          ? 'bg-purple-600 text-white'
                          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-700'
                      }`}
                    >
                      All
                    </button>
                  </div>
                  <button
                    onClick={() => {
                      setResults(null);
                      setTheme('');
                    }}
                    className="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium"
                  >
                    New Search / 새 검색
                  </button>
                </div>
              </div>
            </div>

            {/* Verse cards */}
            <div className="space-y-4">
              {results.results.map((result: SearchResult, idx: number) => (
                <VerseCard
                  key={`${result.reference.book}-${result.reference.chapter}-${result.reference.verse}-${idx}`}
                  result={result}
                  showAllTranslations={showLanguage === 'all'}
                  defaultTranslation={defaultTranslation}
                />
              ))}
            </div>

            {/* Related themes (if available) */}
            {results.related_themes && results.related_themes.length > 0 && (
              <div className="mt-8 p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Related Themes / 관련 주제
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
