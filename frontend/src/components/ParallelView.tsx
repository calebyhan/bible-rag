import React from 'react';
const Aromanize = require('aromanize/base');

interface Translation {
  abbreviation: string;
  text: string;
  language: string;
}

interface ParallelViewProps {
  reference: {
    book: string;
    book_korean?: string;
    chapter: number;
    verse: number;
  };
  translations: Translation[];
  layout?: 'vertical' | 'horizontal' | 'grid';
  koreanMode?: 'hangul' | 'romanization';
}

/**
 * ParallelView component displays multiple Bible translations side-by-side
 * for easy comparison and study.
 */
export default function ParallelView({
  reference,
  translations,
  layout = 'grid',
  koreanMode = 'hangul',
}: ParallelViewProps) {
  const { book, book_korean, chapter, verse } = reference;

  const transformKoreanText = (text: string, isKorean: boolean): string => {
    if (!isKorean || koreanMode === 'hangul') return text;

    if (koreanMode === 'romanization') {
      try {
        const romanized = Aromanize.romanize(text);
        return romanized;
      } catch (error) {
        console.error('Romanization failed:', error);
        return text;
      }
    }

    return text;
  };

  const getLayoutClasses = () => {
    switch (layout) {
      case 'vertical':
        return 'flex flex-col space-y-6';
      case 'horizontal':
        return 'flex flex-row space-x-6 overflow-x-auto';
      case 'grid':
      default:
        return 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6';
    }
  };

  const isKoreanTranslation = (abbrev: string) => {
    const koreanAbbrevs = ['RNKSV', 'NKRV', 'RKV', 'KRV', 'KCBS'];
    return koreanAbbrevs.includes(abbrev);
  };

  return (
    <div className="parallel-view">
      {/* Header */}
      <div className="mb-6 pb-4 border-b border-gray-200 dark:border-slate-700">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {book} {chapter}:{verse}
        </h2>
        {book_korean && (
          <p className="text-lg text-gray-700 dark:text-gray-300 korean-text mt-1">
            {book_korean} {chapter}:{verse}
          </p>
        )}
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
          Comparing {translations.length} translation{translations.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Translations */}
      <div className={getLayoutClasses()}>
        {translations.map((translation, index) => (
          <div
            key={index}
            className="parallel-translation-card bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow"
          >
            {/* Translation Header */}
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-100 dark:border-slate-700">
              <h3 className="font-bold text-primary-700 dark:text-primary-400 text-lg">
                {translation.abbreviation}
              </h3>
              <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 rounded">
                {isKoreanTranslation(translation.abbreviation) ? '한글' : 'English'}
              </span>
            </div>

            {/* Verse Text */}
            <p
              className={`leading-relaxed text-gray-800 dark:text-gray-200 ${
                isKoreanTranslation(translation.abbreviation)
                  ? 'verse-text-korean text-base'
                  : 'verse-text text-base'
              }`}
            >
              {transformKoreanText(
                translation.text,
                isKoreanTranslation(translation.abbreviation)
              )}
            </p>

            {/* Word Count */}
            <div className="mt-4 pt-3 border-t border-gray-100 dark:border-slate-700">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {translation.text.split(/\s+/).length} words
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {translations.length === 0 && (
        <div className="text-center py-12 bg-gray-50 dark:bg-slate-800 rounded-lg">
          <p className="text-gray-700 dark:text-gray-300">No translations to display</p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            Select translations from the search options
          </p>
        </div>
      )}

      {/* Layout Toggle (if needed) */}
      {translations.length > 1 && (
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-slate-700">
          <p className="text-xs text-gray-600 dark:text-gray-400 text-center">
            💡 Tip: Compare word choices, emphasis, and translation philosophy across versions
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * CompactParallelView - A more condensed version for displaying in search results
 */
export function CompactParallelView({
  reference,
  translations,
  koreanMode = 'hangul',
}: Omit<ParallelViewProps, 'layout'>) {
  const isKoreanTranslation = (abbrev: string) => {
    const koreanAbbrevs = ['RNKSV', 'NKRV', 'RKV', 'KRV', 'KCBS'];
    return koreanAbbrevs.includes(abbrev);
  };

  const transformKoreanText = (text: string, isKorean: boolean): string => {
    if (!isKorean || koreanMode === 'hangul') return text;

    if (koreanMode === 'romanization') {
      try {
        const romanized = Aromanize.romanize(text);
        return romanized;
      } catch (error) {
        console.error('Romanization failed:', error);
        return text;
      }
    }

    return text;
  };

  return (
    <div className="compact-parallel-view space-y-3">
      {translations.map((translation, index) => (
        <div key={index} className="flex gap-3">
          <div className="flex-shrink-0">
            <span className="inline-block px-2 py-1 text-xs font-semibold bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded">
              {translation.abbreviation}
            </span>
          </div>
          <p
            className={`flex-1 text-sm text-gray-800 dark:text-gray-200 ${
              isKoreanTranslation(translation.abbreviation)
                ? 'korean-text'
                : ''
            }`}
          >
            {transformKoreanText(
              translation.text,
              isKoreanTranslation(translation.abbreviation)
            )}
          </p>
        </div>
      ))}
    </div>
  );
}
