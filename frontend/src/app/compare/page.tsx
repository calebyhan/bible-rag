'use client';

import { useState, useEffect } from 'react';
import ParallelView from '@/components/ParallelView';
import KoreanToggle, { KoreanDisplayMode } from '@/components/KoreanToggle';
import OriginalLanguage from '@/components/OriginalLanguage';
import { getVerse, getTranslations, getBooks } from '@/lib/api';
import { VerseDetailResponse, Translation, Book } from '@/types';

interface VerseSelection {
  book: string;
  chapter: number;
  verse: number;
}

export default function ComparePage() {
  // State for verse selection
  const [verseSelection, setVerseSelection] = useState<VerseSelection>({
    book: 'John',
    chapter: 3,
    verse: 16,
  });

  // State for translations
  const [availableTranslations, setAvailableTranslations] = useState<Translation[]>([]);
  const [selectedTranslations, setSelectedTranslations] = useState<string[]>(['NIV', 'ESV', 'KJV']);

  // State for books
  const [books, setBooks] = useState<Book[]>([]);

  // State for verse data
  const [verseData, setVerseData] = useState<VerseDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for layout
  const [layout, setLayout] = useState<'vertical' | 'grid'>('grid');

  // State for Korean display mode
  const [koreanMode, setKoreanMode] = useState<KoreanDisplayMode>('hangul');

  // State for original language display
  const [showOriginal, setShowOriginal] = useState(false);

  // State for translation dropdown
  const [showTranslations, setShowTranslations] = useState(false);

  // State for book dropdown
  const [showBookDropdown, setShowBookDropdown] = useState(false);

  // Load translations and books on mount
  useEffect(() => {
    loadTranslationsAndBooks();
  }, []);

  // Load verse when selection changes
  useEffect(() => {
    loadVerse();
  }, [verseSelection, selectedTranslations, showOriginal]);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.book-dropdown-container')) {
        setShowBookDropdown(false);
      }
    };

    if (showBookDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showBookDropdown]);

  const loadTranslationsAndBooks = async () => {
    try {
      const [translationsRes, booksRes] = await Promise.all([
        getTranslations(),
        getBooks(),
      ]);

      setAvailableTranslations(translationsRes.translations);
      setBooks(booksRes.books);

      // Default translations are set in state initialization (NIV, ESV, KJV)
    } catch (err) {
      console.error('Failed to load translations/books:', err);
    }
  };

  const loadVerse = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getVerse(
        verseSelection.book,
        verseSelection.chapter,
        verseSelection.verse,
        selectedTranslations,
        showOriginal
      );
      setVerseData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load verse');
      setVerseData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTranslationToggle = (abbreviation: string) => {
    const isSelected = selectedTranslations.includes(abbreviation);

    if (isSelected) {
      // Don't allow deselecting if it's the only one
      if (selectedTranslations.length === 1) return;
      setSelectedTranslations((prev) => prev.filter((t) => t !== abbreviation));
    } else {
      setSelectedTranslations((prev) => [...prev, abbreviation]);
    }
  };

  const handleBookChange = (bookName: string) => {
    setVerseSelection(prev => ({
      ...prev,
      book: bookName,
      chapter: 1,
      verse: 1,
    }));
  };

  // Get max chapter for selected book
  const getMaxChapter = () => {
    const book = books.find(b => b.name === verseSelection.book);
    return book?.total_chapters || 150;
  };

  return (
    <main className="bg-background dark:bg-background-dark transition-colors">
      {/* Header */}
      <div className="bg-surface dark:bg-surface-dark border-b border-border-light dark:border-border-dark-light transition-colors">
        <div className="max-w-content mx-auto px-space-md py-space-lg">
          <h1 className="font-heading text-2xl sm:text-3xl md:text-4xl text-text-primary dark:text-text-dark-primary mb-space-xs">Verse Comparison</h1>
          <p className="font-ui text-sm text-text-secondary dark:text-text-dark-secondary">
            Compare Bible translations side-by-side • 성경 번역본 비교
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-surface dark:bg-surface-dark border-b border-border-light dark:border-border-dark-light transition-colors">
        <div className="max-w-content mx-auto px-space-md py-space-md">
          {/* Verse Selector */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-space-sm mb-space-md">
            {/* Book selector */}
            <div className="relative book-dropdown-container">
              <span className="block font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-1">Book / 책</span>
              <button
                onClick={() => setShowBookDropdown(!showBookDropdown)}
                className="w-full px-space-sm py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary font-body text-sm focus:outline-none focus:border-text-scripture dark:focus:border-accent-dark-scripture text-left flex items-center justify-between transition-colors"
              >
                <span>{verseSelection.book}</span>
                <span className="text-xs">{showBookDropdown ? '▲' : '▼'}</span>
              </button>

              {/* Book Dropdown */}
              {showBookDropdown && (
                <div className="absolute z-50 mt-1 left-0 w-full sm:min-w-[500px] max-w-[95vw] bg-surface dark:bg-surface-dark border-2 border-text-primary dark:border-text-dark-primary max-h-96 overflow-y-auto transition-colors">
                  {/* Old Testament */}
                  {books.filter(b => b.testament === 'OT').length > 0 && (
                    <div className="p-space-sm">
                      <h3 className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary font-semibold mb-space-xs px-space-xs">
                        Old Testament / 구약
                      </h3>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-1">
                        {books.filter(b => b.testament === 'OT').map((book) => (
                          <button
                            key={book.id}
                            onClick={() => {
                              handleBookChange(book.name);
                              setShowBookDropdown(false);
                            }}
                            className="text-left px-space-xs py-space-xs hover:bg-background dark:hover:bg-background-dark transition-colors border border-transparent hover:border-border-medium dark:hover:border-border-dark-medium"
                          >
                            <div className="font-body text-sm text-text-primary dark:text-text-dark-primary">
                              {book.name}
                            </div>
                            <div className="font-korean text-xs text-text-tertiary dark:text-text-dark-tertiary">
                              {book.name_korean}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Divider */}
                  <div className="border-t-2 border-text-tertiary dark:border-text-dark-tertiary"></div>

                  {/* New Testament */}
                  {books.filter(b => b.testament === 'NT').length > 0 && (
                    <div className="p-space-sm">
                      <h3 className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary font-semibold mb-space-xs px-space-xs">
                        New Testament / 신약
                      </h3>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-1">
                        {books.filter(b => b.testament === 'NT').map((book) => (
                          <button
                            key={book.id}
                            onClick={() => {
                              handleBookChange(book.name);
                              setShowBookDropdown(false);
                            }}
                            className="text-left px-space-xs py-space-xs hover:bg-background dark:hover:bg-background-dark transition-colors border border-transparent hover:border-border-medium dark:hover:border-border-dark-medium"
                          >
                            <div className="font-body text-sm text-text-primary dark:text-text-dark-primary">
                              {book.name}
                            </div>
                            <div className="font-korean text-xs text-text-tertiary dark:text-text-dark-tertiary">
                              {book.name_korean}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Chapter selector */}
            <div>
              <label htmlFor="compare-chapter" className="block font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-1">Chapter / 장</label>
              <input
                id="compare-chapter"
                type="number"
                min="1"
                max={getMaxChapter()}
                value={verseSelection.chapter}
                onChange={(e) => setVerseSelection(prev => ({
                  ...prev,
                  chapter: Math.max(1, Math.min(getMaxChapter(), parseInt(e.target.value) || 1))
                }))}
                className="w-full px-space-sm py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary font-body text-sm focus:outline-none focus:border-text-scripture dark:focus:border-accent-dark-scripture transition-colors"
              />
            </div>

            {/* Verse selector */}
            <div>
              <label htmlFor="compare-verse" className="block font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-1">Verse / 절</label>
              <input
                id="compare-verse"
                type="number"
                min="1"
                max="200"
                value={verseSelection.verse}
                onChange={(e) => setVerseSelection(prev => ({
                  ...prev,
                  verse: Math.max(1, parseInt(e.target.value) || 1)
                }))}
                className="w-full px-space-sm py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary font-body text-sm focus:outline-none focus:border-text-scripture dark:focus:border-accent-dark-scripture transition-colors"
              />
            </div>

            {/* Quick reference input */}
            <div>
              <label htmlFor="compare-quick-ref" className="block font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-1">Quick Reference / 빠른 참조</label>
              <input
                id="compare-quick-ref"
                type="text"
                placeholder="e.g., John 3:16"
                className="w-full px-space-sm py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary placeholder:text-text-tertiary dark:placeholder:text-text-dark-tertiary placeholder:italic font-body text-sm focus:outline-none focus:border-text-scripture dark:focus:border-accent-dark-scripture transition-colors"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const input = e.currentTarget.value;
                    const match = input.match(/^([A-Za-z\s]+)\s*(\d+):(\d+)$/);
                    if (match) {
                      setVerseSelection({
                        book: match[1].trim(),
                        chapter: parseInt(match[2]),
                        verse: parseInt(match[3]),
                      });
                      e.currentTarget.value = '';
                    }
                  }
                }}
              />
            </div>
          </div>

          {/* Translation selector */}
          <div className="mb-space-md">
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
                <div className="flex flex-wrap justify-center gap-4">
                  {availableTranslations.map((trans) => {
                    const isSelected = selectedTranslations.includes(trans.abbreviation);

                    return (
                      <button
                        key={trans.id}
                        type="button"
                        onClick={() => handleTranslationToggle(trans.abbreviation)}
                        className={`font-ui text-sm transition-colors ${isSelected
                            ? 'text-text-primary dark:text-text-dark-primary border-b-2 border-accent-scripture dark:border-accent-dark-scripture'
                            : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-secondary dark:hover:text-text-dark-secondary border-b-2 border-transparent'
                          }`}
                        title={trans.name}
                      >
                        {trans.name}
                      </button>
                    );
                  })}
                </div>
                <p className="text-xs text-center text-text-tertiary dark:text-text-dark-tertiary font-ui">
                  Click to select/deselect translations
                </p>
              </div>
            )}
          </div>

          {/* Layout and display controls */}
          <div className="flex flex-wrap items-center justify-between gap-space-sm">
            <div className="flex items-center gap-space-sm flex-wrap">
              {/* Layout selector */}
              <div className="flex items-center gap-space-xs">
                <span className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary">Layout / 레이아웃:</span>
                <div className="inline-flex border-2 border-text-primary dark:border-text-dark-primary">
                  {(['grid', 'vertical'] as const).map(l => (
                    <button
                      key={l}
                      onClick={() => setLayout(l)}
                      className={`
                        px-space-sm py-space-xs font-ui text-xs uppercase tracking-wide font-semibold transition-all border-r-2 last:border-r-0 border-text-primary dark:border-text-dark-primary
                        ${layout === l
                          ? 'bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark'
                          : 'bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark'
                        }
                      `}
                    >
                      {l === 'grid' && 'Grid'}
                      {l === 'vertical' && 'Vertical'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Original Language Toggle */}
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className={`px-space-sm py-space-xs font-ui text-xs uppercase tracking-wide font-semibold transition-colors whitespace-nowrap border-2 ${showOriginal
                    ? 'border-text-primary dark:border-text-dark-primary bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark'
                    : 'border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark'
                  }`}
              >
                원어 {showOriginal ? 'Hide' : 'Show'}
              </button>
            </div>

            {/* Korean toggle */}
            <KoreanToggle onModeChange={setKoreanMode} defaultMode={koreanMode} />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-content mx-auto px-space-md py-space-lg">
        {error && (
          <div className="mb-space-md border-l-4 border-error dark:border-error-dark pl-space-md py-space-sm">
            <p className="font-ui text-sm uppercase tracking-wide text-text-primary dark:text-text-dark-primary mb-space-xs">Error / 오류</p>
            <p className="font-body text-sm text-text-secondary dark:text-text-dark-secondary">{error}</p>
          </div>
        )}

        {isLoading && (
          <div className="text-center py-space-xl">
            <div className="spinner mx-auto mb-space-sm"></div>
            <p className="font-ui text-sm text-text-secondary dark:text-text-dark-secondary">Loading verse... / 구절 로딩 중...</p>
          </div>
        )}

        {!isLoading && !error && verseData && selectedTranslations.length > 0 && (
          <>
            {/* Original Language Display (if enabled) */}
            {verseData.original && showOriginal && (
              <div className="mb-space-lg">
                <div className="border-l-4 border-border-light dark:border-border-dark-light pl-space-md mb-space-md">
                  <p className="font-body text-sm text-text-secondary dark:text-text-dark-secondary italic">
                    <strong className="text-text-primary dark:text-text-dark-primary not-italic">Original Text Context:</strong> The translations below are all derived from this original{' '}
                    {verseData.original.language === 'greek' ? 'Greek' : verseData.original.language === 'hebrew' ? 'Hebrew' : 'Aramaic'}{' '}
                    text. Notice how different translators interpret and convey the same source material.
                  </p>
                </div>
                <OriginalLanguage
                  language={verseData.original.language as 'greek' | 'hebrew' | 'aramaic'}
                  text={verseData.original.words?.map(w => w.word).join(' ') || ''}
                  transliteration={verseData.original.words?.map(w => w.transliteration).filter(Boolean).join(' ') || ''}
                  words={verseData.original.words || []}
                  strongs={verseData.original.words?.map(w => w.strongs).filter(Boolean) as string[] || []}
                  showInterlinear={true}
                />
              </div>
            )}

            {/* Parallel Translation View */}
            <ParallelView
              reference={verseData.reference}
              translations={selectedTranslations
                .map(abbrev => ({
                  abbreviation: abbrev,
                  text: verseData.translations[abbrev] || 'Translation not available',
                  language: availableTranslations.find(t => t.abbreviation === abbrev)?.language_code || 'en'
                }))
                .filter(t => verseData.translations[t.abbreviation])
              }
              layout={layout}
              koreanMode={koreanMode}
            />
          </>
        )}

        {!isLoading && !error && selectedTranslations.length === 0 && (
          <div className="text-center py-space-xl border border-border-light dark:border-border-dark-light p-space-lg">
            <p className="font-body text-text-primary dark:text-text-dark-primary">Please select at least one translation to compare.</p>
            <p className="font-korean text-sm text-text-secondary dark:text-text-dark-secondary mt-space-xs">비교할 번역본을 하나 이상 선택하세요.</p>
          </div>
        )}

        {/* Verse context navigation */}
        {verseData?.context && (
          <div className="mt-space-lg">
            <div className="border-t border-border-light dark:border-border-dark-light pt-space-lg">
              <h3 className="font-ui text-sm uppercase tracking-wide text-text-primary dark:text-text-dark-primary mb-space-md">Context Navigation / 맥락 탐색</h3>
              <div className="grid md:grid-cols-2 gap-space-sm">
                {verseData.context.previous && (
                  <button
                    onClick={() => setVerseSelection(prev => ({
                      ...prev,
                      verse: prev.verse - 1
                    }))}
                    className="text-left p-space-sm border-2 border-border-light dark:border-border-dark-light hover:border-text-primary dark:hover:border-text-dark-primary bg-background dark:bg-background-dark transition-colors"
                  >
                    <div className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-1">← 이전 절 / Previous Verse</div>
                    <div className="font-ui text-sm font-semibold text-text-primary dark:text-text-dark-primary">
                      {verseSelection.chapter}:{verseSelection.verse - 1}
                    </div>
                    <p className="font-body text-xs text-text-secondary dark:text-text-dark-secondary mt-space-xs line-clamp-2">
                      {verseData.context.previous.text}
                    </p>
                  </button>
                )}
                {verseData.context.next && (
                  <button
                    onClick={() => setVerseSelection(prev => ({
                      ...prev,
                      verse: prev.verse + 1
                    }))}
                    className="text-left p-space-sm border-2 border-border-light dark:border-border-dark-light hover:border-text-primary dark:hover:border-text-dark-primary bg-background dark:bg-background-dark transition-colors"
                  >
                    <div className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-1">다음 절 / Next Verse →</div>
                    <div className="font-ui text-sm font-semibold text-text-primary dark:text-text-dark-primary">
                      {verseSelection.chapter}:{verseSelection.verse + 1}
                    </div>
                    <p className="font-body text-xs text-text-secondary dark:text-text-dark-secondary mt-space-xs line-clamp-2">
                      {verseData.context.next.text}
                    </p>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tips */}
        <div className="mt-space-lg">
          <div className="border-l-4 border-border-light dark:border-border-dark-light pl-space-md py-space-sm">
            <h4 className="font-ui text-xs uppercase tracking-wide text-text-primary dark:text-text-dark-primary mb-space-sm">Comparison Tips / 비교 팁</h4>
            <ul className="font-body text-sm text-text-secondary dark:text-text-dark-secondary space-y-1">
              <li>• Compare word choices and emphasis across different translations</li>
              <li>• Notice how translators handle the same original text differently</li>
              <li>• Enable "Show Original" to see the Greek/Hebrew source text with Strong's numbers</li>
              <li>• Use the layout toggle to find your preferred viewing style</li>
              <li>• Try comparing English and Korean translations together</li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  );
}
