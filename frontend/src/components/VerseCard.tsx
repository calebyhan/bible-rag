'use client';

import { useState } from 'react';
import Link from 'next/link';
import { SearchResult } from '@/types';

interface VerseCardProps {
  result: SearchResult;
  showAllTranslations?: boolean;
  defaultTranslation?: string;
}

export default function VerseCard({ result, showAllTranslations = false, defaultTranslation }: VerseCardProps) {
  const initialTranslation =
    defaultTranslation && result.translations[defaultTranslation]
      ? defaultTranslation
      : Object.keys(result.translations)[0] || '';

  const [activeTranslation, setActiveTranslation] = useState<string>(initialTranslation);
  const [showCrossRefs, setShowCrossRefs] = useState(false);

  const { reference, translations, relevance_score, cross_references } = result;

  const relevancePercent = Math.round(relevance_score * 100);
  const isKorean = (text: string) => /[\uac00-\ud7a3]/.test(text);
  const verseUrl = `/verse/${encodeURIComponent(reference.book)}/${reference.chapter}/${reference.verse}`;

  return (
    <div className="verse-card">
      {/* Reference as large typographic element */}
      <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between mb-space-sm gap-2">
        <div className="flex items-baseline gap-2">
          <Link href={verseUrl} className="group flex items-baseline gap-2">
            <span className="font-ui text-xs sm:text-sm uppercase tracking-wide text-accent-scripture dark:text-accent-dark-scripture hover:text-text-primary dark:hover:text-text-dark-primary transition-colors">
              {reference.book}
            </span>
            <span className="font-serif text-2xl sm:text-3xl md:text-4xl font-light text-accent-scripture dark:text-accent-dark-scripture group-hover:text-text-primary dark:group-hover:text-text-dark-primary transition-colors">
              {reference.chapter}:{reference.verse}
            </span>
          </Link>
        </div>

        {/* Testament and relevance */}
        <div className="flex sm:flex-col items-center sm:items-end gap-2 sm:gap-1">
          <span className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary">
            {reference.testament === 'OT' ? 'OT' : 'NT'}
          </span>
          <span className="font-ui text-xs text-text-secondary dark:text-text-dark-secondary">
            <span className="hidden sm:inline">Relevance: </span><span className="font-medium">{relevancePercent}%</span>
          </span>
        </div>
      </div>

      {/* Korean reference */}
      {reference.book_korean && (
        <Link href={verseUrl}>
          <p className="font-korean text-sm text-text-secondary dark:text-text-dark-secondary mb-space-md hover:text-text-primary dark:hover:text-text-dark-primary transition-colors">
            {reference.book_korean} {reference.chapter}:{reference.verse}
          </p>
        </Link>
      )}

      {/* Translation selector - underlined text tabs */}
      {Object.keys(translations).length > 1 && !showAllTranslations && (
        <div className="flex gap-4 mb-space-sm border-b border-border-light dark:border-border-dark-light pb-2">
          {Object.keys(translations).map((trans) => (
            <button
              key={trans}
              onClick={() => setActiveTranslation(trans)}
              className={`translation-tab dark:text-text-dark-tertiary dark:hover:text-text-dark-primary dark:border-transparent ${
                activeTranslation === trans ? 'translation-tab-active dark:text-text-dark-primary dark:border-text-dark-primary' : ''
              }`}
            >
              {trans}
            </button>
          ))}
        </div>
      )}

      {/* Verse text - THE HERO */}
      {showAllTranslations ? (
        <div className="space-y-space-md">
          {Object.entries(translations).map(([trans, text]) => (
            <div key={trans} className="border-l-4 border-border-light dark:border-border-dark-light pl-space-md">
              <span className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary block mb-2">
                {trans}
              </span>
              <p className={`${isKorean(text) ? 'verse-text-korean korean-text dark:text-text-dark-primary' : 'verse-text dark:text-text-dark-primary'}`}>
                {text}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className={`${
            isKorean(translations[activeTranslation] || '')
              ? 'verse-text-korean korean-text dark:text-text-dark-primary'
              : 'verse-text dark:text-text-dark-primary'
          } mb-space-sm`}
        >
          {translations[activeTranslation]}
        </p>
      )}

      {/* Cross-references - comma-separated links */}
      {cross_references && cross_references.length > 0 && (
        <div className="mt-space-md pt-space-md border-t border-border-light dark:border-border-dark-light">
          <button
            onClick={() => setShowCrossRefs(!showCrossRefs)}
            className="btn-text dark:text-text-dark-secondary dark:hover:text-text-dark-primary dark:border-text-dark-tertiary dark:hover:border-text-dark-primary mb-2"
          >
            {showCrossRefs ? '▾' : '▸'} See also ({cross_references.length})
          </button>

          {showCrossRefs && (
            <div className="flex flex-wrap gap-x-3 gap-y-1">
              {cross_references.map((ref, idx) => {
                const crossRefUrl = `/verse/${encodeURIComponent(ref.book)}/${ref.chapter}/${ref.verse}`;
                return (
                  <span key={idx}>
                    <Link
                      href={crossRefUrl}
                      className="verse-ref dark:text-accent-dark-reference dark:hover:border-accent-dark-reference"
                    >
                      {ref.book} {ref.chapter}:{ref.verse}
                    </Link>
                    {idx < cross_references.length - 1 && (
                      <span className="text-text-tertiary dark:text-text-dark-tertiary">, </span>
                    )}
                  </span>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
