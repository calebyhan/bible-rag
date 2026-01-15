'use client';

import { useState, useEffect } from 'react';
import ParallelView from '@/components/ParallelView';
import KoreanToggle, { KoreanDisplayMode } from '@/components/KoreanToggle';
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
  const [layout, setLayout] = useState<'vertical' | 'horizontal' | 'grid'>('grid');

  // State for Korean display mode
  const [koreanMode, setKoreanMode] = useState<KoreanDisplayMode>('hangul');

  // Load translations and books on mount
  useEffect(() => {
    loadTranslationsAndBooks();
  }, []);

  // Load verse when selection changes
  useEffect(() => {
    loadVerse();
  }, [verseSelection, selectedTranslations]);

  const loadTranslationsAndBooks = async () => {
    try {
      const [translationsRes, booksRes] = await Promise.all([
        getTranslations(),
        getBooks(),
      ]);

      setAvailableTranslations(translationsRes.translations);
      setBooks(booksRes.books);

      // Set default translations if available
      const englishTranslations = translationsRes.translations
        .filter(t => t.language_code === 'en')
        .slice(0, 3)
        .map(t => t.abbreviation);

      if (englishTranslations.length > 0) {
        setSelectedTranslations(englishTranslations);
      }
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
        false // Don't need original language for comparison
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
    setSelectedTranslations(prev =>
      prev.includes(abbreviation)
        ? prev.filter(t => t !== abbreviation)
        : [...prev, abbreviation]
    );
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
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-br from-primary-600 via-primary-700 to-blue-800 text-white">
        <div className="container mx-auto px-4 py-8">
          {/* Navigation */}
          <div className="flex justify-between items-center mb-6">
            <a
              href="/"
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition-colors"
            >
              ← Back to Search
            </a>
            <div className="flex gap-2">
              <a
                href="/browse"
                className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition-colors"
              >
                📖 Browse
              </a>
              <a
                href="/themes"
                className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition-colors"
              >
                🔍 Themes
              </a>
            </div>
          </div>

          <h1 className="text-3xl md:text-4xl font-bold mb-2">Verse Comparison</h1>
          <p className="text-primary-100">
            Compare Bible translations side-by-side • 성경 번역본 비교
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          {/* Verse Selector */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            {/* Book selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Book</label>
              <select
                value={verseSelection.book}
                onChange={(e) => handleBookChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {books.map(book => (
                  <option key={book.id} value={book.name}>
                    {book.name} ({book.testament})
                  </option>
                ))}
              </select>
            </div>

            {/* Chapter selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Chapter</label>
              <input
                type="number"
                min="1"
                max={getMaxChapter()}
                value={verseSelection.chapter}
                onChange={(e) => setVerseSelection(prev => ({
                  ...prev,
                  chapter: Math.max(1, Math.min(getMaxChapter(), parseInt(e.target.value) || 1))
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* Verse selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Verse</label>
              <input
                type="number"
                min="1"
                max="200"
                value={verseSelection.verse}
                onChange={(e) => setVerseSelection(prev => ({
                  ...prev,
                  verse: Math.max(1, parseInt(e.target.value) || 1)
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* Quick reference input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Quick Reference</label>
              <input
                type="text"
                placeholder="e.g., John 3:16"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
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
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Translations ({selectedTranslations.length} selected)
            </label>
            <div className="flex flex-wrap gap-2">
              {availableTranslations.map(trans => (
                <button
                  key={trans.id}
                  onClick={() => handleTranslationToggle(trans.abbreviation)}
                  className={`
                    px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                    ${selectedTranslations.includes(trans.abbreviation)
                      ? 'bg-primary-500 text-white shadow-sm'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                  `}
                >
                  {trans.abbreviation}
                  <span className="ml-1 text-xs opacity-75">
                    ({trans.language_code === 'ko' ? '한' : 'en'})
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Layout and display controls */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            {/* Layout selector */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Layout:</label>
              <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-1">
                {(['grid', 'vertical', 'horizontal'] as const).map(l => (
                  <button
                    key={l}
                    onClick={() => setLayout(l)}
                    className={`
                      px-3 py-1 text-sm rounded-md transition-all
                      ${layout === l
                        ? 'bg-white text-primary-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                      }
                    `}
                  >
                    {l === 'grid' && '📱 Grid'}
                    {l === 'vertical' && '📄 Vertical'}
                    {l === 'horizontal' && '↔️ Horizontal'}
                  </button>
                ))}
              </div>
            </div>

            {/* Korean toggle */}
            <KoreanToggle onModeChange={setKoreanMode} defaultMode={koreanMode} />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8">
        {error && (
          <div className="max-w-4xl mx-auto mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {isLoading && (
          <div className="text-center py-12">
            <div className="spinner mx-auto mb-4"></div>
            <p className="text-gray-600">Loading verse...</p>
          </div>
        )}

        {!isLoading && !error && verseData && selectedTranslations.length > 0 && (
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
          />
        )}

        {!isLoading && !error && selectedTranslations.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow-sm">
            <p className="text-gray-600">Please select at least one translation to compare.</p>
          </div>
        )}

        {/* Verse context navigation */}
        {verseData?.context && (
          <div className="mt-8 max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Context Navigation</h3>
              <div className="grid md:grid-cols-2 gap-4">
                {verseData.context.previous && (
                  <button
                    onClick={() => setVerseSelection(prev => ({
                      ...prev,
                      verse: prev.verse - 1
                    }))}
                    className="text-left p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="text-sm font-medium text-gray-500 mb-1">← Previous Verse</div>
                    <div className="text-sm text-gray-700">
                      {verseSelection.chapter}:{verseSelection.verse - 1}
                    </div>
                    <p className="text-xs text-gray-600 mt-2 line-clamp-2">
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
                    className="text-left p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="text-sm font-medium text-gray-500 mb-1">Next Verse →</div>
                    <div className="text-sm text-gray-700">
                      {verseSelection.chapter}:{verseSelection.verse + 1}
                    </div>
                    <p className="text-xs text-gray-600 mt-2 line-clamp-2">
                      {verseData.context.next.text}
                    </p>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tips */}
        <div className="mt-8 max-w-4xl mx-auto">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 mb-2">💡 Comparison Tips</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Compare word choices and emphasis across different translations</li>
              <li>• Notice how translators handle the same original text differently</li>
              <li>• Use the layout toggle to find your preferred viewing style</li>
              <li>• Try comparing English and Korean translations together</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-200 mt-12 py-8">
        <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
          <p>Bible RAG - Verse Comparison Tool</p>
          <p className="mt-1">Compare translations to deepen your understanding</p>
        </div>
      </footer>
    </main>
  );
}
