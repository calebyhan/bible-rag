'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { searchThemes, getTranslations } from '@/lib/api';
import { ThemeResponse, SearchResult } from '@/types';
import VerseCard from '@/components/VerseCard';

const POPULAR_THEMES = [
  { theme: 'love and compassion', label: 'Love & Compassion' },
  { theme: 'faith and trust', label: 'Faith & Trust' },
  { theme: 'forgiveness', label: 'Forgiveness' },
  { theme: 'hope and encouragement', label: 'Hope' },
  { theme: 'wisdom and guidance', label: 'Wisdom' },
  { theme: 'prayer', label: 'Prayer' },
  { theme: 'salvation and redemption', label: 'Salvation' },
  { theme: 'peace', label: 'Peace' },
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
  const [showTranslations, setShowTranslations] = useState(false);
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
    <main className="min-h-screen bg-background dark:bg-background-dark transition-colors">
      {/* Header */}
      <div className="bg-surface dark:bg-surface-dark border-b border-border-light dark:border-border-dark-light transition-colors">
        <div className="container mx-auto px-space-md py-space-xl md:py-space-2xl">
          <div className="max-w-content mx-auto">
            <div className="text-center mb-space-lg">
              <h1 className="font-heading text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-space-md text-text-primary dark:text-text-dark-primary">
                Thematic Search
              </h1>
              <p className="font-body text-base sm:text-lg md:text-xl text-text-primary dark:text-text-dark-primary max-w-2xl mx-auto px-4">
                Explore biblical themes across the Old and New Testaments
              </p>
              <p className="font-korean text-sm sm:text-base md:text-lg text-text-secondary dark:text-text-dark-secondary mt-space-sm px-4">
                구약과 신약을 통해 성경 주제 탐색하기
              </p>
            </div>

            {/* Search form */}
            <form onSubmit={handleSubmit} className="mb-space-md">
              <div className="relative">
                <input
                  type="text"
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  placeholder="Enter a theme (e.g., 'love', 'faith', 'forgiveness')..."
                  className="w-full px-space-md py-space-md font-body text-lg border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary focus:outline-none focus:border-text-scripture dark:focus:border-accent-dark-scripture transition-colors"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !theme.trim()}
                  className={`absolute right-2 top-1/2 -translate-y-1/2 px-space-md py-space-sm font-ui text-sm uppercase tracking-wide font-semibold transition-all border-2 ${
                    isLoading || !theme.trim()
                      ? 'border-text-tertiary dark:border-text-dark-tertiary bg-surface dark:bg-surface-dark text-text-tertiary dark:text-text-dark-tertiary cursor-not-allowed'
                      : 'border-text-primary dark:border-text-dark-primary bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark hover:bg-background dark:hover:bg-background-dark hover:text-text-primary dark:hover:text-text-dark-primary'
                  }`}
                >
                  {isLoading ? 'Searching...' : 'Search'}
                </button>
              </div>

              {/* Testament filter */}
              <div className="mt-space-md flex items-center justify-center gap-space-sm">
                <span className="font-ui text-sm uppercase tracking-wide text-text-primary dark:text-text-dark-primary font-semibold">
                  Testament / 성경:
                </span>
                <div className="inline-flex border-2 border-text-primary dark:border-text-dark-primary">
                  {(['both', 'OT', 'NT'] as const).map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setTestament(t)}
                      className={`px-space-sm py-space-xs font-ui text-xs uppercase tracking-wide font-semibold transition-all border-r-2 last:border-r-0 border-text-primary dark:border-text-dark-primary ${
                        testament === t
                          ? 'bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark'
                          : 'bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark'
                      }`}
                    >
                      {t === 'both' ? 'Both' : t}
                    </button>
                  ))}
                </div>
              </div>

              {/* Translation filter */}
              <div className="mt-space-md">
                <div className="flex justify-center mb-space-xs">
                  <button
                    type="button"
                    onClick={() => setShowTranslations(!showTranslations)}
                    className="btn-text"
                  >
                    {showTranslations ? '▾' : '▸'} Translations ({selectedTranslations.length} selected)
                  </button>
                </div>

                {showTranslations && (
                  <div className="space-y-2">
                    {translationsLoading ? (
                      <div className="text-center text-text-tertiary dark:text-text-dark-tertiary text-sm">Loading translations...</div>
                    ) : (
                      <div className="flex flex-wrap justify-center gap-4">
                        {translations.map((trans) => {
                          const isSelected = selectedTranslations.includes(trans.abbrev);
                          const isDefault = trans.abbrev === defaultTranslation;

                          return (
                            <button
                              key={trans.abbrev}
                              type="button"
                              onClick={() => toggleTranslation(trans.abbrev, false)}
                              onDoubleClick={() => toggleTranslation(trans.abbrev, true)}
                              className={`font-ui text-sm transition-colors ${
                                isSelected
                                  ? 'text-text-primary dark:text-text-dark-primary border-b-2 border-accent-scripture dark:border-accent-dark-scripture'
                                  : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-secondary dark:hover:text-text-dark-secondary border-b-2 border-transparent'
                              } ${isDefault ? 'font-bold' : 'font-normal'}`}
                              title={isDefault ? `${trans.name} (Default)` : trans.name}
                            >
                              {isDefault && <span className="text-accent-scripture dark:text-accent-dark-scripture mr-1">★</span>}
                              {trans.name}
                            </button>
                          );
                        })}
                      </div>
                    )}
                    <p className="text-xs text-center text-text-tertiary dark:text-text-dark-tertiary font-ui">
                      Click to select/deselect • Double-click to set as default (★)
                    </p>
                  </div>
                )}
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Popular themes */}
      {!results && !isLoading && !error && (
        <div className="container mx-auto px-space-md py-space-xl">
          <div className="max-w-content mx-auto">
            <h2 className="font-heading text-2xl sm:text-3xl font-bold text-text-primary dark:text-text-dark-primary mb-space-lg text-center">
              Popular Themes / 인기 주제
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-space-sm">
              {POPULAR_THEMES.map((t) => (
                <button
                  key={t.theme}
                  onClick={() => handleSearch(t.theme)}
                  className="p-space-md border-2 border-text-primary dark:border-text-dark-primary bg-transparent text-text-primary dark:text-text-dark-primary hover:bg-text-primary dark:hover:bg-text-dark-primary hover:text-surface dark:hover:text-surface-dark transition-all text-center"
                >
                  <div className="font-ui text-sm uppercase tracking-wide">
                    {t.label}
                  </div>
                </button>
              ))}
            </div>

            {/* Info section */}
            <div className="mt-space-xl border-l-4 border-border-light dark:border-border-dark-light pl-space-lg py-space-md">
              <h3 className="font-heading text-xl sm:text-2xl text-text-primary dark:text-text-dark-primary mb-space-md">
                What is Thematic Search? / 주제별 검색이란?
              </h3>
              <p className="font-body text-base text-text-primary dark:text-text-dark-primary mb-space-md leading-relaxed">
                Thematic search helps you explore specific topics or concepts throughout the Bible.
                Unlike keyword search, it understands the meaning and context of themes, finding
                relevant passages even when they use different words.
              </p>
              <p className="font-korean text-base text-text-secondary dark:text-text-dark-secondary mb-space-md leading-relaxed">
                주제별 검색은 성경 전체에서 특정 주제나 개념을 탐색하는 데 도움을 줍니다.
                키워드 검색과 달리 주제의 의미와 맥락을 이해하여 다른 단어를 사용하더라도 관련 구절을 찾습니다.
              </p>
              <div className="space-y-space-xs border-t border-border-light dark:border-border-dark-light pt-space-md mt-space-md">
                <p className="font-body text-sm text-text-primary dark:text-text-dark-primary">
                  • Search by concept, not just keywords
                </p>
                <p className="font-body text-sm text-text-primary dark:text-text-dark-primary">
                  • Filter by Old Testament, New Testament, or both
                </p>
                <p className="font-body text-sm text-text-primary dark:text-text-dark-primary">
                  • View results in multiple translations simultaneously
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="container mx-auto px-space-md py-space-lg">
          <div className="max-w-content mx-auto border-l-4 border-error dark:border-error-dark pl-space-md py-space-sm">
            <p className="font-ui text-sm uppercase tracking-wide text-text-primary dark:text-text-dark-primary mb-space-xs">
              Error / 오류
            </p>
            <p className="font-body text-sm text-text-secondary dark:text-text-dark-secondary">{error}</p>
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="container mx-auto px-space-md py-space-xl">
          <div className="max-w-content mx-auto text-center">
            <div className="inline-block w-12 h-12 border-4 border-text-tertiary dark:border-text-dark-tertiary border-t-text-primary dark:border-t-text-dark-primary animate-spin mb-space-md"></div>
            <p className="font-body text-base text-text-primary dark:text-text-dark-primary">Searching for verses about "{theme}"...</p>
          </div>
        </div>
      )}

      {/* Results */}
      {results && !isLoading && (
        <div className="container mx-auto px-space-md py-space-lg">
          <div className="max-w-content mx-auto">
            {/* Results header */}
            <div className="mb-space-lg">
              <div className="flex items-center justify-between mb-space-sm">
                <div>
                  <h2 className="font-heading text-2xl sm:text-3xl font-bold text-text-primary dark:text-text-dark-primary">
                    Results for "{results.theme}"
                  </h2>
                  <p className="font-ui text-sm text-text-secondary dark:text-text-dark-secondary mt-space-xs">
                    {results.total_results} verses found
                    {results.testament_filter && ` in ${results.testament_filter}`}
                    {' · '}
                    {results.query_time_ms}ms
                  </p>
                </div>
                <div className="flex items-center gap-space-sm">
                  {/* Language toggle */}
                  <div className="inline-flex border-2 border-text-primary dark:border-text-dark-primary">
                    <button
                      onClick={() => setShowLanguage('default')}
                      className={`px-space-sm py-space-xs font-ui text-xs uppercase tracking-wide font-semibold transition-all border-r-2 border-text-primary dark:border-text-dark-primary ${
                        showLanguage === 'default'
                          ? 'bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark'
                          : 'bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark'
                      }`}
                    >
                      Default
                    </button>
                    <button
                      onClick={() => setShowLanguage('all')}
                      className={`px-space-sm py-space-xs font-ui text-xs uppercase tracking-wide font-semibold transition-all ${
                        showLanguage === 'all'
                          ? 'bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark'
                          : 'bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark'
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
                    className="font-ui text-sm uppercase tracking-wide text-text-primary dark:text-text-dark-primary hover:text-text-scripture dark:hover:text-accent-dark-scripture font-semibold pb-1 border-b-2 border-transparent hover:border-text-scripture dark:hover:border-accent-dark-scripture transition-colors"
                  >
                    New Search / 새 검색
                  </button>
                </div>
              </div>
            </div>

            {/* Verse cards */}
            <div className="space-y-space-md">
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
              <div className="mt-space-lg border-t border-border-light dark:border-border-dark-light pt-space-lg">
                <h3 className="font-heading text-xl text-text-primary dark:text-text-dark-primary mb-space-sm">
                  Related Themes / 관련 주제
                </h3>
                <div className="flex flex-wrap gap-2">
                  {results.related_themes.map((relatedTheme) => (
                    <button
                      key={relatedTheme}
                      onClick={() => handleSearch(relatedTheme)}
                      className="px-space-sm py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-transparent text-text-primary dark:text-text-dark-primary font-ui text-sm uppercase tracking-wide hover:bg-text-primary dark:hover:bg-text-dark-primary hover:text-surface dark:hover:text-surface-dark transition-all"
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
