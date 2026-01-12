'use client';

import { useState } from 'react';
import { SearchResult } from '@/types';

interface VerseCardProps {
  result: SearchResult;
  showAllTranslations?: boolean;
}

export default function VerseCard({ result, showAllTranslations = false }: VerseCardProps) {
  const [activeTranslation, setActiveTranslation] = useState<string>(
    Object.keys(result.translations)[0] || ''
  );
  const [showCrossRefs, setShowCrossRefs] = useState(false);

  const { reference, translations, relevance_score, cross_references } = result;

  // Format relevance score as percentage
  const relevancePercent = Math.round(relevance_score * 100);

  // Determine if text is Korean
  const isKorean = (text: string) => /[\uac00-\ud7a3]/.test(text);

  return (
    <div className="verse-card">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {reference.book} {reference.chapter}:{reference.verse}
          </h3>
          {reference.book_korean && (
            <p className="text-sm text-gray-500 korean-text">
              {reference.book_korean} {reference.chapter}:{reference.verse}
            </p>
          )}
        </div>

        {/* Testament badge and relevance */}
        <div className="flex items-center gap-2">
          <span className={`badge ${reference.testament === 'OT' ? 'badge-ot' : 'badge-nt'}`}>
            {reference.testament}
          </span>
          <span className="text-sm text-gray-500">{relevancePercent}%</span>
        </div>
      </div>

      {/* Relevance bar */}
      <div className="relevance-bar mb-4">
        <div className="relevance-fill" style={{ width: `${relevancePercent}%` }} />
      </div>

      {/* Translation tabs */}
      {Object.keys(translations).length > 1 && !showAllTranslations && (
        <div className="flex border-b border-gray-200 mb-4">
          {Object.keys(translations).map((trans) => (
            <button
              key={trans}
              onClick={() => setActiveTranslation(trans)}
              className={`translation-tab ${
                activeTranslation === trans ? 'translation-tab-active' : ''
              }`}
            >
              {trans}
            </button>
          ))}
        </div>
      )}

      {/* Verse text */}
      {showAllTranslations ? (
        <div className="space-y-4">
          {Object.entries(translations).map(([trans, text]) => (
            <div key={trans} className="border-l-4 border-primary-200 pl-4">
              <span className="text-xs font-medium text-primary-600 block mb-1">{trans}</span>
              <p className={isKorean(text) ? 'verse-text-korean korean-text' : 'verse-text'}>
                {text}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p
          className={
            isKorean(translations[activeTranslation] || '')
              ? 'verse-text-korean korean-text'
              : 'verse-text'
          }
        >
          {translations[activeTranslation]}
        </p>
      )}

      {/* Cross-references */}
      {cross_references && cross_references.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <button
            onClick={() => setShowCrossRefs(!showCrossRefs)}
            className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
          >
            <span>Cross-references ({cross_references.length})</span>
            <svg
              className={`w-4 h-4 transition-transform ${showCrossRefs ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showCrossRefs && (
            <div className="mt-2 flex flex-wrap gap-2">
              {cross_references.map((ref, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700 hover:bg-gray-200 cursor-pointer"
                >
                  {ref.book} {ref.chapter}:{ref.verse}
                  <span className="ml-1 text-gray-400">({ref.relationship})</span>
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
