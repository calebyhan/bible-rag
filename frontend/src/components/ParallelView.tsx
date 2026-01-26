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

  const isKoreanTranslation = (abbrev: string) => {
    const koreanAbbrevs = ['RNKSV', 'NKRV', 'RKV', 'KRV', 'KCBS'];
    return koreanAbbrevs.includes(abbrev);
  };

  return (
    <div className="parallel-view max-w-content mx-auto">
      {/* Header */}
      <div className="mb-space-md pb-space-sm border-b-2 border-text-tertiary dark:border-text-dark-tertiary">
        <div className="flex items-baseline gap-3">
          <h2 className="font-heading text-3xl text-text-primary dark:text-text-dark-primary">
            {book} {chapter}:{verse}
          </h2>
          {book_korean && (
            <p className="font-korean text-lg text-text-secondary dark:text-text-dark-secondary">
              {book_korean} {chapter}:{verse}
            </p>
          )}
        </div>
        <p className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mt-space-xs">
          {translations.length} Translation{translations.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Translations - Dynamic Layout */}
      <div className={`mt-space-md ${
        layout === 'vertical' ? 'space-y-space-md' :
        layout === 'horizontal' ? 'flex gap-space-md overflow-x-auto' :
        'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-space-md'
      }`}>
        {translations.map((translation, index) => (
          <div
            key={index}
            className={`border-l-4 border-text-tertiary dark:border-text-dark-tertiary pl-space-md pr-space-md py-space-sm bg-surface dark:bg-surface-dark transition-colors ${
              layout === 'horizontal' ? 'min-w-[400px] flex-shrink-0' : ''
            }`}
          >
            {/* Translation Header */}
            <div className="flex items-baseline justify-between mb-space-sm pb-space-xs border-b border-border-light dark:border-border-dark-light">
              <h3 className="font-ui text-xs uppercase tracking-wide text-text-primary dark:text-text-dark-primary font-semibold">
                {translation.abbreviation}
              </h3>
              <span className="font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary">
                {isKoreanTranslation(translation.abbreviation) ? 'Korean' : 'English'}
              </span>
            </div>

            {/* Verse Text */}
            <p
              className={`font-body text-lg leading-relaxed text-text-primary dark:text-text-dark-primary ${
                isKoreanTranslation(translation.abbreviation)
                  ? 'font-korean'
                  : ''
              }`}
            >
              {transformKoreanText(
                translation.text,
                isKoreanTranslation(translation.abbreviation)
              )}
            </p>

            {/* Word Count */}
            <div className="mt-space-sm pt-space-xs border-t border-border-light dark:border-border-dark-light">
              <p className="font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary">
                {translation.text.split(/\s+/).length} words
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {translations.length === 0 && (
        <div className="text-center py-space-lg border-2 border-border-light dark:border-border-dark-light bg-background dark:bg-background-dark transition-colors">
          <p className="font-body text-text-primary dark:text-text-dark-primary">No translations to display</p>
          <p className="font-ui text-sm text-text-tertiary dark:text-text-dark-tertiary mt-space-xs">
            Select translations from the search options
          </p>
        </div>
      )}

      {/* Help Text */}
      {translations.length > 1 && (
        <div className="mt-space-lg pt-space-md border-t border-border-light dark:border-border-dark-light">
          <p className="font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary text-center">
            Compare word choices, emphasis, and translation philosophy across versions
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
    <div className="compact-parallel-view space-y-space-sm">
      {translations.map((translation, index) => (
        <div key={index} className="flex gap-space-sm items-start">
          <div className="flex-shrink-0">
            <span className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary font-semibold border-b border-text-tertiary dark:border-text-dark-tertiary pb-px">
              {translation.abbreviation}
            </span>
          </div>
          <p
            className={`flex-1 font-body text-sm text-text-primary dark:text-text-dark-primary ${
              isKoreanTranslation(translation.abbreviation)
                ? 'font-korean'
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
