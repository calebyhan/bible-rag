'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getVerse } from '@/lib/api';
import OriginalLanguage from '@/components/OriginalLanguage';
import { OriginalLanguageData, CrossReference } from '@/types';

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
  showOriginal?: boolean;
}

interface VerseDetails {
  original?: OriginalLanguageData;
  cross_references?: CrossReference[];
  translations: Record<string, string>;
}

export default function ChapterView({
  reference,
  verses,
  selectedTranslation,
  showOriginal = true,
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
          showOriginal
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
    <div className="border border-border-light dark:border-border-dark-light p-space-lg mb-space-lg">
      {/* Chapter Header */}
      <div className="mb-space-md pb-space-sm border-b border-border-light dark:border-border-dark-light">
        <h2 className="font-heading text-4xl text-text-primary dark:text-text-dark-primary">
          {reference.book} {reference.chapter}
        </h2>
        {reference.book_korean && (
          <p className="font-korean text-xl text-text-secondary mt-space-xs">
            {reference.book_korean} {reference.chapter}장
          </p>
        )}
        <p className="font-ui text-xs uppercase tracking-wide text-text-tertiary mt-space-sm">
          Click any verse to see {showOriginal ? 'original language, ' : ''}cross-references{showOriginal ? '' : ', and more'}
        </p>
      </div>

      {/* Verses */}
      <div className="space-y-px">
        {verses.map((verse) => {
          const isExpanded = expandedVerse === verse.verse;
          const details = verseDetails[verse.verse];
          const isLoading = loadingVerse === verse.verse;

          return (
            <div key={verse.verse} id={`verse-${verse.verse}`}>
              {/* Verse Text */}
              <div
                className={`group hover:bg-background dark:hover:bg-background-dark -mx-space-sm px-space-sm py-space-sm transition-all cursor-pointer ${
                  isExpanded ? 'bg-background dark:bg-background-dark border-l-4 border-accent-scripture dark:border-accent-dark-scripture' : ''
                }`}
                onClick={() => handleVerseClick(verse.verse)}
              >
                <div className="flex items-start gap-space-sm">
                  {/* Verse Number */}
                  <span
                    className={`flex-shrink-0 font-ui text-sm font-bold mt-1 w-8 ${
                      isExpanded
                        ? 'text-accent-scripture dark:text-accent-dark-scripture'
                        : 'text-accent-scripture dark:text-accent-dark-scripture opacity-70'
                    }`}
                  >
                    {verse.verse}
                  </span>

                  {/* Verse Text */}
                  <div className="flex-1">
                    <p
                      className={`font-body text-lg leading-relaxed ${
                        selectedTranslation.includes('개역') ||
                        selectedTranslation.includes('KR')
                          ? 'font-korean'
                          : ''
                      } text-text-primary dark:text-text-dark-primary`}
                    >
                      {verse.translations[selectedTranslation] ||
                        Object.values(verse.translations)[0]}
                    </p>
                  </div>

                  {/* Expand Indicator */}
                  <span className="text-text-tertiary dark:text-text-dark-tertiary text-xs mt-1">
                    {isExpanded ? '▼' : '▶'}
                  </span>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="mt-space-xs mb-space-md ml-10 mr-space-sm p-space-md border-l-4 border-border-light dark:border-border-dark-light">
                  {isLoading ? (
                    <div className="text-center py-space-md">
                      <div className="spinner mx-auto mb-space-xs"></div>
                      <p className="font-ui text-sm text-text-secondary dark:text-text-dark-secondary">
                        Loading details...
                      </p>
                    </div>
                  ) : details ? (
                    <div className="space-y-space-md">
                      {/* View Full Details Button */}
                      <div className="flex justify-end">
                        <button
                          onClick={() => navigateToVerse(reference.book, reference.chapter, verse.verse)}
                          className="border-2 border-text-primary dark:border-text-dark-primary bg-transparent text-text-primary dark:text-text-dark-primary hover:bg-text-primary dark:hover:bg-text-dark-primary hover:text-surface dark:hover:text-surface-dark px-space-sm py-space-xs font-ui text-sm uppercase tracking-wide transition-all"
                        >
                          View Full Details →
                        </button>
                      </div>

                      {/* Original Language */}
                      {details.original && (
                        <div className="mb-space-md">
                          <OriginalLanguage
                            language={details.original.language as 'greek' | 'hebrew' | 'aramaic'}
                            text={details.original.words?.map(w => w.word).join(' ') || ''}
                            transliteration={details.original.words?.map(w => w.transliteration).filter(Boolean).join(' ')}
                            words={details.original.words}
                            strongs={details.original.words?.map(w => w.strongs).filter(Boolean) as string[]}
                            showInterlinear={true}
                          />
                        </div>
                      )}

                      {/* Cross References */}
                      {details.cross_references && details.cross_references.length > 0 && (
                        <div>
                          <h4 className="font-ui text-xs uppercase tracking-wide text-text-primary dark:text-text-dark-primary mb-space-sm border-b border-border-light dark:border-border-dark-light pb-space-xs">
                            Cross References ({details.cross_references.length})
                          </h4>
                          <div className="space-y-space-xs">
                            {details.cross_references.map((ref, idx) => (
                              <button
                                key={idx}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigateToVerse(ref.book, ref.chapter, ref.verse);
                                }}
                                className="w-full text-left p-space-sm border border-border-light dark:border-border-dark-light hover:border-text-primary dark:hover:border-text-dark-primary transition-colors cursor-pointer"
                              >
                                <div className="flex items-start justify-between gap-space-xs">
                                  <span className="font-ui text-sm text-accent-reference dark:text-accent-dark-reference hover:text-text-primary dark:hover:text-text-dark-primary border-b border-transparent hover:border-accent-reference dark:hover:border-accent-dark-reference">
                                    {ref.book} {ref.chapter}:{ref.verse} →
                                  </span>
                                  {ref.relationship && (
                                    <span className="font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary uppercase tracking-wide">
                                      {ref.relationship}
                                    </span>
                                  )}
                                </div>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Other Translations */}
                      {Object.keys(details.translations).length > 1 && (
                        <div>
                          <h4 className="font-ui text-xs uppercase tracking-wide text-text-primary dark:text-text-dark-primary mb-space-sm border-b border-border-light dark:border-border-dark-light pb-space-xs">
                            Other Translations
                          </h4>
                          <div className="space-y-space-sm">
                            {Object.entries(details.translations)
                              .filter(([abbr]) => abbr !== selectedTranslation)
                              .map(([abbr, text]) => (
                                <div
                                  key={abbr}
                                  className="p-space-sm border-l-4 border-border-light dark:border-border-dark-light"
                                >
                                  <span className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary">
                                    {abbr}
                                  </span>
                                  <p className="font-body text-base text-text-primary dark:text-text-dark-primary mt-space-xs">
                                    {text}
                                  </p>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="font-ui text-sm text-text-tertiary dark:text-text-dark-tertiary">
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
