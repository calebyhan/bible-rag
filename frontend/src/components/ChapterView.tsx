'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getVerse } from '@/lib/api';

interface Verse {
  verse: number;
  translations: Record<string, string>;
  original?: {
    language: string;
    words: Array<{
      word: string;
      transliteration: string;
      strongs: string;
      definition: string;
    }>;
  };
}

interface ChapterViewProps {
  reference: {
    book: string;
    book_korean?: string;
    chapter: number;
    testament: string;
  };
  verses: Verse[];
  selectedTranslation: string;
}

interface VerseDetails {
  original?: {
    language: string;
    text: string;
    words: Array<{
      word: string;
      transliteration: string;
      strongs: string;
      morphology: string;
      definition: string;
    }>;
  };
  cross_references?: Array<{
    book: string;
    chapter: number;
    verse: number;
    text: string;
    relationship: string;
  }>;
  translations: Record<string, string>;
}

export default function ChapterView({
  reference,
  verses,
  selectedTranslation,
}: ChapterViewProps) {
  const router = useRouter();
  const [expandedVerse, setExpandedVerse] = useState<number | null>(null);
  const [verseDetails, setVerseDetails] = useState<Record<number, VerseDetails>>({});
  const [loadingVerse, setLoadingVerse] = useState<number | null>(null);

  const handleVerseClick = async (verseNum: number) => {
    if (expandedVerse === verseNum) {
      // Collapse if already expanded
      setExpandedVerse(null);
      return;
    }

    setExpandedVerse(verseNum);

    // Load details if not already loaded
    if (!verseDetails[verseNum]) {
      setLoadingVerse(verseNum);
      try {
        const details = await getVerse(
          reference.book,
          reference.chapter,
          verseNum,
          [selectedTranslation],
          true
        );
        setVerseDetails((prev) => ({
          ...prev,
          [verseNum]: details,
        }));
      } catch (error) {
        console.error('Error loading verse details:', error);
      } finally {
        setLoadingVerse(null);
      }
    }
  };

  const navigateToVerse = (book: string, chapter: number, verse: number) => {
    router.push(`/verse/${encodeURIComponent(book)}/${chapter}/${verse}`);
  };

  return (
    <div className="verse-card p-6 mb-6">
      {/* Chapter Header */}
      <div className="mb-6 pb-4 border-b border-gray-200 dark:border-slate-700">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
          {reference.book} {reference.chapter}
        </h2>
        {reference.book_korean && (
          <p className="text-lg text-gray-600 dark:text-gray-400 korean-text mt-1">
            {reference.book_korean} {reference.chapter}장
          </p>
        )}
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          Click any verse to see cross-references and original language
        </p>
      </div>

      {/* Verses */}
      <div className="space-y-1">
        {verses.map((verse) => {
          const isExpanded = expandedVerse === verse.verse;
          const details = verseDetails[verse.verse];
          const isLoading = loadingVerse === verse.verse;

          return (
            <div key={verse.verse} id={`verse-${verse.verse}`}>
              {/* Verse Text */}
              <div
                className={`group hover:bg-gray-50 dark:hover:bg-slate-800/50 -mx-4 px-4 py-2 rounded-lg transition-all cursor-pointer ${
                  isExpanded ? 'bg-primary-50 dark:bg-primary-900/20' : ''
                }`}
                onClick={() => handleVerseClick(verse.verse)}
              >
                <div className="flex items-start gap-3">
                  {/* Verse Number */}
                  <span
                    className={`flex-shrink-0 text-sm font-bold mt-1 w-8 ${
                      isExpanded
                        ? 'text-primary-700 dark:text-primary-300'
                        : 'text-primary-600 dark:text-primary-400'
                    }`}
                  >
                    {verse.verse}
                  </span>

                  {/* Verse Text */}
                  <div className="flex-1">
                    <p
                      className={`text-base leading-relaxed ${
                        selectedTranslation.includes('개역') ||
                        selectedTranslation.includes('KR')
                          ? 'korean-text'
                          : ''
                      } text-gray-800 dark:text-gray-200`}
                    >
                      {verse.translations[selectedTranslation] ||
                        Object.values(verse.translations)[0]}
                    </p>
                  </div>

                  {/* Expand Indicator */}
                  <span className="text-gray-400 dark:text-gray-500 text-xs mt-1">
                    {isExpanded ? '▼' : '▶'}
                  </span>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="mt-2 mb-4 ml-11 mr-4 p-4 bg-gray-50 dark:bg-slate-800/50 rounded-lg border-l-4 border-primary-500">
                  {isLoading ? (
                    <div className="text-center py-4">
                      <div className="spinner mx-auto mb-2"></div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Loading details...
                      </p>
                    </div>
                  ) : details ? (
                    <div className="space-y-4">
                      {/* View Full Details Button */}
                      <div className="flex justify-end">
                        <button
                          onClick={() => navigateToVerse(reference.book, reference.chapter, verse.verse)}
                          className="text-sm px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
                        >
                          <span>📖</span>
                          View Full Details
                        </button>
                      </div>
                      {/* Original Language */}
                      {details.original && (
                        <div>
                          <h4 className="text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                            <span>📜</span>
                            Original Language ({details.original.language === 'greek' ? 'Greek' : 'Hebrew'})
                          </h4>
                          <div className="text-lg mb-3 font-serif text-gray-900 dark:text-gray-100">
                            {details.original.text}
                          </div>
                          <div className="space-y-2">
                            {details.original.words.map((word, idx) => (
                              <div
                                key={idx}
                                className="p-2 bg-white dark:bg-slate-700 rounded text-sm"
                              >
                                <div className="flex items-start gap-2">
                                  <span className="font-bold text-primary-600 dark:text-primary-400">
                                    {word.word}
                                  </span>
                                  {word.transliteration && (
                                    <span className="text-gray-600 dark:text-gray-400 italic">
                                      {word.transliteration}
                                    </span>
                                  )}
                                  {word.strongs && (
                                    <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
                                      {word.strongs}
                                    </span>
                                  )}
                                </div>
                                {word.definition && (
                                  <p className="text-gray-700 dark:text-gray-300 mt-1">
                                    {word.definition}
                                  </p>
                                )}
                                {word.morphology && (
                                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    {word.morphology}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Cross References */}
                      {details.cross_references && details.cross_references.length > 0 && (
                        <div>
                          <h4 className="text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                            <span>🔗</span>
                            Cross References ({details.cross_references.length})
                          </h4>
                          <div className="space-y-2">
                            {details.cross_references.map((ref, idx) => (
                              <button
                                key={idx}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigateToVerse(ref.book, ref.chapter, ref.verse);
                                }}
                                className="w-full text-left p-3 bg-white dark:bg-slate-700 rounded hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors cursor-pointer"
                              >
                                <div className="flex items-start justify-between gap-2 mb-1">
                                  <span className="font-semibold text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300">
                                    {ref.book} {ref.chapter}:{ref.verse} →
                                  </span>
                                  {ref.relationship && (
                                    <span className="text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded">
                                      {ref.relationship}
                                    </span>
                                  )}
                                </div>
                                <p className="text-sm text-gray-700 dark:text-gray-300">
                                  {ref.text}
                                </p>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Other Translations */}
                      {Object.keys(details.translations).length > 1 && (
                        <div>
                          <h4 className="text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                            <span>🌐</span>
                            Other Translations
                          </h4>
                          <div className="space-y-2">
                            {Object.entries(details.translations)
                              .filter(([abbr]) => abbr !== selectedTranslation)
                              .map(([abbr, text]) => (
                                <div
                                  key={abbr}
                                  className="p-2 bg-white dark:bg-slate-700 rounded"
                                >
                                  <span className="text-xs font-semibold text-gray-600 dark:text-gray-400">
                                    {abbr}
                                  </span>
                                  <p className="text-sm text-gray-800 dark:text-gray-200 mt-1">
                                    {text}
                                  </p>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      No additional details available
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
