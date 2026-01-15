'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { getBooks, getChapter, getTranslations } from '@/lib/api';
import { Book } from '@/types';
import ChapterView from '@/components/ChapterView';

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

export default function BrowsePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [books, setBooks] = useState<Book[]>([]);
  const [translations, setTranslations] = useState<any[]>([]);
  const [selectedTranslation, setSelectedTranslation] = useState<string>('NIV');
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

  const chapterRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const bookInputRef = useRef<HTMLDivElement>(null);

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

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (bookInputRef.current && !bookInputRef.current.contains(event.target as Node)) {
        setShowBookDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadChapter = async (bookName: string, chapter: number) => {
    const key = `${bookName}-${chapter}`;
    if (loadedChapters.has(key)) {
      // Already loaded, just scroll to it
      scrollToChapter(key);
      return;
    }

    try {
      const chapterData = await getChapter(bookName, chapter, [selectedTranslation], false);
      setLoadedChapters((prev) => new Map(prev).set(key, chapterData));
      setVisibleChapters((prev) => [...prev, key]);
      // Scroll after a brief delay to ensure DOM is updated
      setTimeout(() => scrollToChapter(key), 100);
    } catch (err: any) {
      console.error('Error loading chapter:', err);
      setError(`Failed to load ${bookName} ${chapter}`);
    }
  };

  const scrollToChapter = (key: string) => {
    const element = chapterRefs.current.get(key);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleBookSelect = (book: Book) => {
    setSearchBook(book.name);
    setShowBookDropdown(false);
  };

  const handleJumpTo = async (bookName?: string, chapterNum?: number) => {
    // Use provided values or state values
    const targetBook = bookName || searchBook;
    const targetChapter = chapterNum || (searchChapter ? parseInt(searchChapter) : null);

    if (!targetBook || !targetChapter) {
      alert('Please select a book and chapter');
      return;
    }

    const book = books.find(
      (b) =>
        b.name.toLowerCase() === targetBook.toLowerCase() ||
        b.name_korean === targetBook ||
        b.abbreviation?.toLowerCase() === targetBook.toLowerCase()
    );

    if (!book) {
      alert('Book not found');
      return;
    }

    if (isNaN(targetChapter) || targetChapter < 1 || targetChapter > book.total_chapters) {
      alert(`Invalid chapter. ${book.name} has ${book.total_chapters} chapters.`);
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
          verseElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
          verseElement.classList.add('bg-yellow-100', 'dark:bg-yellow-900/30');
          setTimeout(
            () =>
              verseElement.classList.remove('bg-yellow-100', 'dark:bg-yellow-900/30'),
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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-700 dark:text-gray-300">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">Error</h2>
          <p className="text-gray-700 dark:text-gray-300 mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Sticky Header with Navigation */}
      <header className="sticky top-0 z-50 bg-white dark:bg-slate-800 shadow-md border-b dark:border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4">
            {/* Top row: Title and buttons */}
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Browse Bible
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">성경 둘러보기</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => router.push('/')}
                  className="px-4 py-2 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-900 dark:text-gray-100 rounded-lg text-sm font-medium transition-colors"
                >
                  ← Home
                </button>
              </div>
            </div>

            {/* Navigation Bar */}
            <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end">
              {/* Book Input */}
              <div className="flex-1 relative" ref={bookInputRef}>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Book
                </label>
                <input
                  type="text"
                  value={searchBook}
                  onChange={(e) => {
                    setSearchBook(e.target.value);
                    setShowBookDropdown(true);
                  }}
                  onFocus={() => setShowBookDropdown(true)}
                  placeholder="Genesis, 창세기, Gen..."
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />

                {/* Book Dropdown */}
                {showBookDropdown && (filteredOTBooks.length > 0 || filteredNTBooks.length > 0) && (
                  <div className="absolute z-50 mt-1 w-full max-w-3xl bg-white dark:bg-slate-800 rounded-lg shadow-2xl border border-gray-200 dark:border-slate-600 max-h-96 overflow-y-auto">
                    {/* Old Testament */}
                    {filteredOTBooks.length > 0 && (
                      <div className="p-3">
                        <h3 className="text-xs font-bold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-2 px-2">
                          Old Testament
                        </h3>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-1">
                          {filteredOTBooks.map((book) => (
                            <button
                              key={book.id}
                              onClick={() => handleBookSelect(book)}
                              className="text-left px-3 py-2 rounded hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors group"
                            >
                              <div className="font-medium text-sm text-gray-900 dark:text-gray-100 group-hover:text-primary-700 dark:group-hover:text-primary-300">
                                {book.name}
                              </div>
                              <div className="text-xs text-gray-500 dark:text-gray-400 korean-text">
                                {book.name_korean}
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Divider */}
                    {filteredOTBooks.length > 0 && filteredNTBooks.length > 0 && (
                      <div className="border-t border-gray-200 dark:border-slate-700"></div>
                    )}

                    {/* New Testament */}
                    {filteredNTBooks.length > 0 && (
                      <div className="p-3">
                        <h3 className="text-xs font-bold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-2 px-2">
                          New Testament
                        </h3>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-1">
                          {filteredNTBooks.map((book) => (
                            <button
                              key={book.id}
                              onClick={() => handleBookSelect(book)}
                              className="text-left px-3 py-2 rounded hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors group"
                            >
                              <div className="font-medium text-sm text-gray-900 dark:text-gray-100 group-hover:text-primary-700 dark:group-hover:text-primary-300">
                                {book.name}
                              </div>
                              <div className="text-xs text-gray-500 dark:text-gray-400 korean-text">
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
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Chapter
                </label>
                <input
                  type="number"
                  value={searchChapter}
                  onChange={(e) => setSearchChapter(e.target.value)}
                  placeholder="1"
                  min="1"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              {/* Verse Input (Optional) */}
              <div className="w-24">
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Verse (opt)
                </label>
                <input
                  type="number"
                  value={searchVerse}
                  onChange={(e) => setSearchVerse(e.target.value)}
                  placeholder="1"
                  min="1"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              {/* Translation Selector */}
              <div className="w-32">
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Translation
                </label>
                <select
                  value={selectedTranslation}
                  onChange={(e) => setSelectedTranslation(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {translations.map((t) => (
                    <option key={t.id} value={t.abbreviation}>
                      {t.abbreviation}
                    </option>
                  ))}
                </select>
              </div>

              {/* Go Button */}
              <button
                onClick={handleJumpTo}
                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium text-sm whitespace-nowrap"
              >
                Go
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {visibleChapters.length === 0 ? (
          <div className="text-center py-12 verse-card">
            <p className="text-lg text-gray-700 dark:text-gray-300 mb-4">
              Enter a book and chapter above to start reading
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              위에서 책과 장을 입력하여 읽기 시작하세요
            </p>
            <div className="mt-8">
              <h3 className="text-md font-semibold text-gray-800 dark:text-gray-200 mb-3">
                Quick Start:
              </h3>
              <div className="flex flex-wrap justify-center gap-2">
                {['Genesis', 'Psalms', 'John', 'Romans'].map((bookName) => (
                  <button
                    key={bookName}
                    onClick={() => handleJumpTo(bookName, 1)}
                    className="px-4 py-2 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-lg hover:bg-primary-200 dark:hover:bg-primary-900/50 transition-colors"
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
                  />

                  {/* Navigation Buttons */}
                  <div className="flex justify-between items-center mb-8 px-4">
                    <button
                      onClick={() =>
                        handleLoadAdjacentChapter(
                          chapterData.reference.book,
                          chapterData.reference.chapter - 1
                        )
                      }
                      disabled={chapterData.reference.chapter === 1}
                      className="px-4 py-2 bg-gray-200 dark:bg-slate-700 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      ← Previous Chapter
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
                      className="px-4 py-2 bg-gray-200 dark:bg-slate-700 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next Chapter →
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
