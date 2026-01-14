'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getVerse, searchVerses } from '@/lib/api';
import { VerseDetailResponse, SearchResult } from '@/types';

export default function VerseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [verseData, setVerseData] = useState<VerseDetailResponse | null>(null);
  const [relatedVerses, setRelatedVerses] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTranslations, setSelectedTranslations] = useState<string[]>(['NIV', '개역개정']);

  const book = params.book as string;
  const chapter = parseInt(params.chapter as string);
  const verse = parseInt(params.verse as string);

  useEffect(() => {
    const fetchVerseData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch verse in multiple translations
        const data = await getVerse(book, chapter, verse, selectedTranslations, true);
        setVerseData(data);

        // Fetch semantically related verses
        const reference = `${book} ${chapter}:${verse}`;
        const searchResults = await searchVerses({
          query: reference,
          languages: ['en', 'ko'],
          translations: selectedTranslations,
          max_results: 5,
        });

        if (searchResults.results) {
          // Filter out the current verse
          const filtered = searchResults.results.filter(
            (r) =>
              !(r.reference.book_en === book && r.reference.chapter === chapter && r.reference.verse === verse)
          );
          setRelatedVerses(filtered);
        }
      } catch (err: any) {
        console.error('Error fetching verse:', err);
        setError(err.message || 'Failed to load verse');
      } finally {
        setLoading(false);
      }
    };

    fetchVerseData();
  }, [book, chapter, verse, selectedTranslations]);

  const handleTranslationToggle = (translation: string) => {
    if (selectedTranslations.includes(translation)) {
      if (selectedTranslations.length > 1) {
        setSelectedTranslations(selectedTranslations.filter((t) => t !== translation));
      }
    } else {
      setSelectedTranslations([...selectedTranslations, translation]);
    }
  };

  const navigateToVerse = (ref: { book_en: string; chapter: number; verse: number }) => {
    router.push(`/verse/${ref.book_en}/${ref.chapter}/${ref.verse}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Loading verse...</p>
        </div>
      </div>
    );
  }

  if (error || !verseData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Verse Not Found</h2>
          <p className="text-gray-600 mb-6">{error || 'The requested verse could not be found.'}</p>
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

  const { reference, translations, original, cross_references, context } = verseData;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <button
            onClick={() => router.back()}
            className="text-primary-600 hover:text-primary-700 font-medium mb-2 inline-flex items-center"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            {reference.book} {reference.chapter}:{reference.verse}
          </h1>
          {reference.book_korean && (
            <p className="text-lg text-gray-600 korean-text mt-1">
              {reference.book_korean} {reference.chapter}:{reference.verse}
            </p>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Translation Selector */}
        <div className="mb-6 bg-white rounded-lg shadow-sm p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Translations</h3>
          <div className="flex flex-wrap gap-2">
            {['NIV', 'ESV', 'KJV', '개역개정', '개역한글'].map((trans) => (
              <button
                key={trans}
                onClick={() => handleTranslationToggle(trans)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedTranslations.includes(trans)
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {trans}
              </button>
            ))}
          </div>
        </div>

        {/* Verse Translations */}
        <div className="space-y-4 mb-8">
          {Object.entries(translations).map(([lang, text]) => (
            <div key={lang} className="verse-card p-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-primary-600 uppercase">{lang}</span>
              </div>
              <p
                className={`text-lg leading-relaxed ${
                  lang.includes('ko') || lang.includes('개역') ? 'verse-text-korean' : 'verse-text'
                }`}
              >
                {text}
              </p>
            </div>
          ))}
        </div>

        {/* Original Language */}
        {original && (
          <div className="verse-card p-6 mb-8">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
              <span className="mr-2">📖</span>
              Original Language ({original.language === 'greek' ? 'Greek' : 'Hebrew'})
            </h3>
            <div className="space-y-4">
              <p className="text-2xl font-serif text-gray-900 mb-4">{original.text}</p>
              {original.transliteration && (
                <div>
                  <span className="text-sm font-semibold text-gray-600">Transliteration:</span>
                  <p className="text-lg text-gray-800 italic mt-1">{original.transliteration}</p>
                </div>
              )}
              {original.strongs && original.strongs.length > 0 && (
                <div>
                  <span className="text-sm font-semibold text-gray-600">Strong's Numbers:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {original.strongs.map((num) => (
                      <span key={num} className="badge bg-purple-100 text-purple-800">
                        {num}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Context (Previous/Next verses) */}
        {context && (context.previous || context.next) && (
          <div className="verse-card p-6 mb-8">
            <h3 className="text-lg font-bold text-gray-800 mb-4">Context</h3>
            <div className="space-y-4">
              {context.previous && (
                <div className="border-l-4 border-gray-300 pl-4">
                  <button
                    onClick={() => navigateToVerse({
                      book_en: reference.book,
                      chapter: reference.chapter,
                      verse: reference.verse - 1,
                    })}
                    className="text-sm font-semibold text-gray-600 hover:text-primary-600 mb-1"
                  >
                    {reference.book} {reference.chapter}:{reference.verse - 1}
                  </button>
                  <p className="text-gray-700">{context.previous}</p>
                </div>
              )}
              {context.next && (
                <div className="border-l-4 border-gray-300 pl-4">
                  <button
                    onClick={() => navigateToVerse({
                      book_en: reference.book,
                      chapter: reference.chapter,
                      verse: reference.verse + 1,
                    })}
                    className="text-sm font-semibold text-gray-600 hover:text-primary-600 mb-1"
                  >
                    {reference.book} {reference.chapter}:{reference.verse + 1}
                  </button>
                  <p className="text-gray-700">{context.next}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Cross References */}
        {cross_references && cross_references.length > 0 && (
          <div className="verse-card p-6 mb-8">
            <h3 className="text-lg font-bold text-gray-800 mb-4">Cross References</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {cross_references.map((ref, idx) => (
                <button
                  key={idx}
                  onClick={() => navigateToVerse(ref.reference)}
                  className="text-left p-4 border border-gray-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-primary-700">
                      {ref.reference.book} {ref.reference.chapter}:{ref.reference.verse}
                    </span>
                    {ref.relationship_type && (
                      <span className="text-xs px-2 py-1 bg-gray-100 rounded text-gray-600">
                        {ref.relationship_type}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-2">{ref.text}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Related Verses */}
        {relatedVerses.length > 0 && (
          <div className="verse-card p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">Related Verses</h3>
            <div className="space-y-4">
              {relatedVerses.map((verse, idx) => (
                <button
                  key={idx}
                  onClick={() => navigateToVerse(verse.reference)}
                  className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-primary-700">
                      {verse.reference.book} {verse.reference.chapter}:{verse.reference.verse}
                    </span>
                    <span className="text-sm text-gray-500">
                      {Math.round(verse.relevance_score * 100)}% relevant
                    </span>
                  </div>
                  {verse.translations.en && (
                    <p className="text-sm text-gray-700">{verse.translations.en}</p>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
