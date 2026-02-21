'use client';

import { useEffect, useState, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { getBooks, getChapter, getTranslations } from '@/lib/api';
import { Book, Translation } from '@/types';
import ChapterView from '@/components/ChapterView';
import Toast from '@/components/Toast';

interface ChapterData {
  reference: {
    book: string;
    book_korean?: string;
    chapter: number;
    testament: string;
  };
  verses: Array<{
    verse: number;
    translations: Record<string, string>;
    original?: any;
  }>;
}

export const dynamic = 'force-dynamic';

function BrowsePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [books, setBooks] = useState<Book[]>([]);
  const [translations, setTranslations] = useState<Translation[]>([]);
  const [selectedTranslation, setSelectedTranslation] = useState<string>('NIV');
  const [showTranslationDropdown, setShowTranslationDropdown] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Navigation state
  const [selectedBook, setSelectedBook] = useState<string>('');
  const [selectedChapter, setSelectedChapter] = useState<number>(1);
  const [searchBook, setSearchBook] = useState<string>('');
  const [searchChapter, setSearchChapter] = useState<string>('');
  const [searchVerse, setSearchVerse] = useState<string>('');
  const [showBookDropdown, setShowBookDropdown] = useState(false);

  // Chapter display state
  const [loadedChapters, setLoadedChapters] = useState<Map<string, ChapterData>>(new Map());
  const [visibleChapters, setVisibleChapters] = useState<string[]>([]);

  // Original language display toggle
  const [showOriginal, setShowOriginal] = useState(true);

  // Toast notification
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' | 'info' | 'warning' } | null>(null);

  const chapterRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const bookInputRef = useRef<HTMLDivElement>(null);
  const translationInputRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [booksData, translationsData] = await Promise.all([
          getBooks(),
          getTranslations(),
        ]);
        setBooks(booksData.books);
        setTranslations(translationsData.translations);

        // Get initial book/chapter from URL params
        const bookParam = searchParams.get('book');
        const chapterParam = searchParams.get('chapter');
        if (bookParam) {
          setSelectedBook(bookParam);
          setSearchBook(bookParam);
          if (chapterParam) {
            const chapterNum = parseInt(chapterParam);
            setSelectedChapter(chapterNum);
            setSearchChapter(chapterParam);
            // Load initial chapter
            await loadChapter(bookParam, chapterNum);
          }
        }
      } catch (err: any) {
        console.error('Error fetching data:', err);
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (bookInputRef.current && !bookInputRef.current.contains(event.target as Node)) {
        setShowBookDropdown(false);
      }
      if (translationInputRef.current && !translationInputRef.current.contains(event.target as Node)) {
        setShowTranslationDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Reload chapters when translation changes
  useEffect(() => {
    if (selectedBook && selectedChapter && books.length > 0) {
      // Clear all loaded chapters
      setLoadedChapters(new Map());
      setVisibleChapters([]);
      // Reload current chapter with new translation
      loadChapter(selectedBook, selectedChapter, true);
    }
  }, [selectedTranslation]);

  const loadChapter = async (bookName: string, chapter: number, forceReload = false) => {
    const key = `${bookName}-${chapter}-${selectedTranslation}`;
    if (loadedChapters.has(key) && !forceReload) {
      // Already loaded, just show it (replace current view)
      setVisibleChapters([key]);
      setTimeout(() => scrollToChapter(key), 100);
      return;
    }

    try {
      const chapterData = await getChapter(bookName, chapter, [selectedTranslation], false);
      setLoadedChapters((prev) => new Map(prev).set(key, chapterData));
      // Replace visible chapters with just this one
      setVisibleChapters([key]);
      // Scroll after a brief delay to ensure DOM is updated
      setTimeout(() => scrollToChapter(key), 100);
    } catch (err: any) {
      console.error('Error loading chapter:', err);
      setToast({ message: `Failed to load ${bookName} ${chapter} / ${bookName} ${chapter}장을 불러오는데 실패했습니다`, type: 'error' });
    }
  };

  const scrollToChapter = (key: string) => {
    const element = chapterRefs.current.get(key);
    if (element) {
      // Calculate offset for navbar
      const navbarHeight = 64;
      const totalOffset = navbarHeight + 16;

      const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
      const offsetPosition = elementPosition - totalOffset;

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
    }
  };

  const handleBookSelect = (book: Book) => {
    setSearchBook(book.name);
    setShowBookDropdown(false);
  };

  const handleJumpTo = async (bookName?: string, chapterNum?: number) => {
    // Use provided values or state values
    const targetBook = bookName || searchBook;
    const targetChapter = chapterNum ?? (searchChapter ? parseInt(searchChapter) : null);

    // Validate inputs
    if (!targetBook || typeof targetBook !== 'string' || targetBook.trim() === '') {
      setToast({ message: 'Please select a book / 책을 선택하세요', type: 'warning' });
      return;
    }

    if (!targetChapter || isNaN(targetChapter) || targetChapter < 1) {
      setToast({ message: 'Please enter a valid chapter number / 유효한 장 번호를 입력하세요', type: 'warning' });
      return;
    }

    const book = books.find(
      (b) =>
        b.name.toLowerCase() === targetBook.trim().toLowerCase() ||
        b.name_korean === targetBook.trim() ||
        b.abbreviation?.toLowerCase() === targetBook.trim().toLowerCase()
    );

    if (!book) {
      setToast({ message: `Book "${targetBook}" not found / 책을 찾을 수 없습니다`, type: 'error' });
      return;
    }

    if (targetChapter > book.total_chapters) {
      setToast({
        message: `Invalid chapter. ${book.name} has ${book.total_chapters} chapters. / 잘못된 장입니다. ${book.name_korean || book.name}은(는) ${book.total_chapters}장까지 있습니다.`,
        type: 'warning'
      });
      return;
    }

    setSelectedBook(book.name);
    setSelectedChapter(targetChapter);
    setSearchBook(book.name);
    setSearchChapter(targetChapter.toString());

    // Update URL
    const params = new URLSearchParams();
    params.set('book', book.name);
    params.set('chapter', targetChapter.toString());
    if (searchVerse) params.set('verse', searchVerse);
    router.push(`/browse?${params.toString()}`, { scroll: false });

    // Load and scroll to chapter
    await loadChapter(book.name, targetChapter);

    // If verse specified, scroll to that verse
    if (searchVerse) {
      setTimeout(() => {
        const verseElement = document.getElementById(`verse-${searchVerse}`);
        if (verseElement) {
          const navbarHeight = 64;
          const totalOffset = navbarHeight + 16;

          const elementPosition = verseElement.getBoundingClientRect().top + window.pageYOffset;
          const offsetPosition = elementPosition - totalOffset;

          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });

          verseElement.classList.add('bg-background', 'border-l-4', 'border-text-scripture');
          setTimeout(
            () =>
              verseElement.classList.remove('bg-background', 'border-l-4', 'border-text-scripture'),
            2000
          );
        }
      }, 500);
    }
  };

  // Filter books based on search
  const filteredOTBooks = books.filter(
    (b) =>
      b.testament === 'OT' &&
      (searchBook === '' ||
        b.name.toLowerCase().includes(searchBook.toLowerCase()) ||
        b.name_korean?.includes(searchBook) ||
        b.abbreviation?.toLowerCase().includes(searchBook.toLowerCase()))
  );

  const filteredNTBooks = books.filter(
    (b) =>
      b.testament === 'NT' &&
      (searchBook === '' ||
        b.name.toLowerCase().includes(searchBook.toLowerCase()) ||
        b.name_korean?.includes(searchBook) ||
        b.abbreviation?.toLowerCase().includes(searchBook.toLowerCase()))
  );

  const handleLoadAdjacentChapter = async (bookName: string, chapter: number) => {
    const book = books.find((b) => b.name === bookName);
    if (!book) return;

    if (chapter >= 1 && chapter <= book.total_chapters) {
      await loadChapter(bookName, chapter);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 bg-background dark:bg-background-dark flex items-center justify-center transition-colors">
        <div className="text-center">
          <div className="spinner mx-auto mb-space-sm"></div>
          <p className="font-ui text-sm text-text-secondary dark:text-text-dark-secondary">Loading... / 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 bg-background dark:bg-background-dark flex items-center justify-center transition-colors">
        <div className="text-center max-w-md border-2 border-text-tertiary dark:border-text-dark-tertiary p-space-lg bg-surface dark:bg-surface-dark transition-colors">
          <h2 className="font-heading text-2xl text-text-primary dark:text-text-dark-primary mb-space-sm">Error / 오류</h2>
          <p className="font-body text-text-secondary dark:text-text-dark-secondary mb-space-md">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="btn-text border-2 border-text-primary dark:border-text-dark-primary px-space-md py-space-sm dark:text-text-dark-secondary dark:hover:text-text-dark-primary"
          >
            Return Home / 홈으로
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-background dark:bg-background-dark transition-colors">
      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header with Navigation */}
      <header className="bg-surface dark:bg-surface-dark border-b-2 border-text-tertiary dark:border-text-dark-tertiary transition-colors">
        <div className="max-w-content mx-auto px-space-md py-space-md">
          <div className="flex flex-col gap-space-sm">
            {/* Title */}
            <div>
              <h1 className="font-heading text-xl sm:text-2xl text-text-primary dark:text-text-dark-primary">
                Browse Bible
              </h1>
              <p className="font-korean text-xs sm:text-sm text-text-secondary dark:text-text-dark-secondary">성경 둘러보기</p>
            </div>

            {/* Navigation Bar */}
            <div className="flex flex-col sm:flex-row gap-space-sm items-start sm:items-end">
              {/* Book Input */}
              <div className="flex-1 relative" ref={bookInputRef}>
                <label htmlFor="browse-book" className="block font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-1">
                  Book / 책
                </label>
                <input
                  id="browse-book"
                  type="text"
                  value={searchBook}
                  onChange={(e) => {
                    setSearchBook(e.target.value);
                    setShowBookDropdown(true);
                  }}
                  onFocus={() => setShowBookDropdown(true)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleJumpTo();
                    }
                  }}
                  placeholder="Genesis, 창세기, Gen..."
                  className="w-full px-space-sm py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary font-body text-sm focus:outline-none focus:border-text-scripture dark:focus:border-accent-dark-scripture transition-colors"
                />

                {/* Book Dropdown */}
                {showBookDropdown && (filteredOTBooks.length > 0 || filteredNTBooks.length > 0) && (
                  <div className="absolute z-50 mt-1 left-0 w-[800px] max-w-[90vw] bg-surface dark:bg-surface-dark border-2 border-text-primary dark:border-text-dark-primary max-h-96 overflow-y-auto transition-colors">
                    {/* Old Testament */}
                    {filteredOTBooks.length > 0 && (
                      <div className="p-space-sm">
                        <h3 className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary font-semibold mb-space-xs px-space-xs">
                          Old Testament / 구약
                        </h3>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-1">
                          {filteredOTBooks.map((book) => (
                            <button
                              key={book.id}
                              onClick={() => handleBookSelect(book)}
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
                    {filteredOTBooks.length > 0 && filteredNTBooks.length > 0 && (
                      <div className="border-t-2 border-text-tertiary dark:border-text-dark-tertiary"></div>
                    )}

                    {/* New Testament */}
                    {filteredNTBooks.length > 0 && (
                      <div className="p-space-sm">
                        <h3 className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary font-semibold mb-space-xs px-space-xs">
                          New Testament / 신약
                        </h3>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-1">
                          {filteredNTBooks.map((book) => (
                            <button
                              key={book.id}
                              onClick={() => handleBookSelect(book)}
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

              {/* Chapter Input */}
              <div className="w-24">
                <label htmlFor="browse-chapter" className="block font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-1">
                  Chapter / 장
                </label>
                <input
                  id="browse-chapter"
                  type="number"
                  value={searchChapter}
                  onChange={(e) => setSearchChapter(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleJumpTo();
                    }
                  }}
                  placeholder="1"
                  min="1"
                  className="w-full px-space-sm py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary font-body text-sm focus:outline-none focus:border-text-scripture dark:focus:border-accent-dark-scripture transition-colors"
                />
              </div>

              {/* Verse Input (Optional) */}
              <div className="w-24">
                <label htmlFor="browse-verse" className="block font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-1">
                  Verse / 절
                </label>
                <input
                  id="browse-verse"
                  type="number"
                  value={searchVerse}
                  onChange={(e) => setSearchVerse(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleJumpTo();
                    }
                  }}
                  placeholder="1"
                  min="1"
                  className="w-full px-space-sm py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary font-body text-sm focus:outline-none focus:border-text-scripture dark:focus:border-accent-dark-scripture transition-colors"
                />
              </div>

              {/* Translation Selector */}
              <div className="relative" ref={translationInputRef}>
                <span className="block font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-1">
                  Translation / 번역
                </span>
                <button
                  onClick={() => setShowTranslationDropdown(!showTranslationDropdown)}
                  className="px-space-sm py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary font-body text-sm focus:outline-none focus:border-text-scripture dark:focus:border-accent-dark-scripture text-left flex items-center justify-between gap-2 min-w-[80px] transition-colors"
                >
                  <span className="font-semibold">{selectedTranslation}</span>
                  <span className="text-xs">{showTranslationDropdown ? '▲' : '▼'}</span>
                </button>

                {/* Translation Dropdown */}
                {showTranslationDropdown && (
                  <div className="absolute z-50 mt-1 right-0 min-w-64 bg-surface dark:bg-surface-dark border-2 border-text-primary dark:border-text-dark-primary max-h-80 overflow-y-auto transition-colors">
                    {/* Group translations by language */}
                    {(() => {
                      const grouped = translations.reduce((acc, t) => {
                        const lang = t.language_code === 'ko' ? 'Korean' : t.language_code === 'en' ? 'English' : t.language_code === 'he' ? 'Hebrew' : t.language_code === 'el' ? 'Greek' : 'Other';
                        if (!acc[lang]) acc[lang] = [];
                        acc[lang].push(t);
                        return acc;
                      }, {} as Record<string, Translation[]>);

                      const languageOrder = ['English', 'Korean', 'Hebrew', 'Greek', 'Other'];

                      return languageOrder.map((lang) => {
                        const langTranslations = grouped[lang];
                        if (!langTranslations?.length) return null;

                        return (
                          <div key={lang} className="p-space-xs">
                            <h3 className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary font-semibold mb-space-xs px-space-xs">
                              {lang}
                            </h3>
                            {langTranslations.map((t) => (
                              <button
                                key={t.id}
                                onClick={() => {
                                  setSelectedTranslation(t.abbreviation);
                                  setShowTranslationDropdown(false);
                                }}
                                className={`w-full text-left px-space-sm py-space-xs transition-colors border-l-4 ${
                                  selectedTranslation === t.abbreviation
                                    ? 'border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark'
                                    : 'border-transparent hover:border-border-medium dark:hover:border-border-dark-medium hover:bg-background dark:hover:bg-background-dark'
                                }`}
                              >
                                <div className="flex items-center justify-between">
                                  <span className="font-ui text-sm font-semibold text-text-primary dark:text-text-dark-primary">
                                    {t.abbreviation}
                                  </span>
                                  {selectedTranslation === t.abbreviation && (
                                    <span className="text-text-primary dark:text-text-dark-primary">✓</span>
                                  )}
                                </div>
                                <div className="font-body text-xs text-text-tertiary dark:text-text-dark-tertiary mt-px">
                                  {t.name}
                                </div>
                              </button>
                            ))}
                          </div>
                        );
                      });
                    })()}
                  </div>
                )}
              </div>

              {/* Original Language Toggle */}
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className={`px-space-sm py-space-xs font-ui text-xs uppercase tracking-wide font-semibold transition-colors whitespace-nowrap border-2 ${
                  showOriginal
                    ? 'border-text-primary dark:border-text-dark-primary bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark'
                    : 'border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark'
                }`}
                title="Toggle original language display / 원어 표시 전환"
              >
                원어 {showOriginal ? 'Hide' : 'Show'}
              </button>

              {/* Go Button */}
              <button
                onClick={() => handleJumpTo()}
                className="px-space-md py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark hover:bg-text-secondary dark:hover:bg-text-dark-secondary transition-colors font-ui font-semibold text-sm uppercase tracking-wide whitespace-nowrap"
              >
                Go / 이동
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-content mx-auto px-space-md py-space-lg">
        {visibleChapters.length === 0 ? (
          <div className="text-center py-space-xl border-2 border-text-tertiary dark:border-text-dark-tertiary p-space-lg bg-surface dark:bg-surface-dark transition-colors">
            <p className="font-body text-lg text-text-primary dark:text-text-dark-primary mb-space-sm">
              Enter a book and chapter above to start reading
            </p>
            <p className="font-korean text-sm text-text-secondary dark:text-text-dark-secondary">
              위에서 책과 장을 입력하여 읽기 시작하세요
            </p>
            <div className="mt-space-md">
              <h3 className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary font-semibold mb-space-sm">
                Quick Start / 빠른 시작:
              </h3>
              <div className="flex flex-wrap justify-center gap-space-xs">
                {['Genesis', 'Psalms', 'John', 'Romans'].map((bookName) => (
                  <button
                    key={bookName}
                    onClick={() => handleJumpTo(bookName, 1)}
                    className="px-space-sm py-space-xs border-2 border-text-tertiary dark:border-text-dark-tertiary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:border-text-primary dark:hover:border-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark transition-colors font-ui text-sm"
                  >
                    {bookName} 1
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Loaded Chapters */}
            {visibleChapters.map((key) => {
              const chapterData = loadedChapters.get(key);
              if (!chapterData) return null;

              const book = books.find((b) => b.name === chapterData.reference.book);

              return (
                <div
                  key={key}
                  ref={(el) => {
                    if (el) chapterRefs.current.set(key, el);
                  }}
                >
                  <ChapterView
                    reference={chapterData.reference}
                    verses={chapterData.verses}
                    selectedTranslation={selectedTranslation}
                    showOriginal={showOriginal}
                  />

                  {/* Navigation Buttons */}
                  <div className="flex justify-between items-center mb-space-lg px-space-sm">
                    <button
                      onClick={() =>
                        handleLoadAdjacentChapter(
                          chapterData.reference.book,
                          chapterData.reference.chapter - 1
                        )
                      }
                      disabled={chapterData.reference.chapter === 1}
                      className="px-space-sm py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed font-ui text-sm"
                    >
                      ← 이전 장 / Previous
                    </button>
                    <button
                      onClick={() =>
                        handleLoadAdjacentChapter(
                          chapterData.reference.book,
                          chapterData.reference.chapter + 1
                        )
                      }
                      disabled={
                        !book || chapterData.reference.chapter >= book.total_chapters
                      }
                      className="px-space-sm py-space-xs border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed font-ui text-sm"
                    >
                      다음 장 / Next →
                    </button>
                  </div>
                </div>
              );
            })}
          </>
        )}
      </main>
    </div>
  );
}

export default function BrowsePage() {
  return (
    <Suspense fallback={
      <div className="flex-1 bg-background dark:bg-background-dark transition-colors">
        <div className="max-w-content mx-auto px-space-md py-space-lg">
          <div className="text-center font-ui text-sm text-text-secondary dark:text-text-dark-secondary">Loading... / 로딩 중...</div>
        </div>
      </div>
    }>
      <BrowsePageContent />
    </Suspense>
  );
}
