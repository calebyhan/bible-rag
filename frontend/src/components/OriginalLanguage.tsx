import React, { useState } from 'react';

interface OriginalWord {
  word: string;
  strongs_number?: string;
  transliteration?: string;
  morphology?: string;
  definition?: string;
  word_order?: number;
}

interface OriginalLanguageProps {
  language: 'greek' | 'hebrew' | 'aramaic';
  text: string;
  transliteration?: string;
  words?: OriginalWord[];
  strongs?: string[];
  showInterlinear?: boolean;
}

/**
 * OriginalLanguage component displays Greek, Hebrew, or Aramaic text
 * with transliteration, Strong's numbers, and interlinear analysis.
 */
export default function OriginalLanguage({
  language,
  text,
  transliteration,
  words = [],
  strongs = [],
  showInterlinear = true,
}: OriginalLanguageProps) {
  const [selectedWord, setSelectedWord] = useState<OriginalWord | null>(null);
  const [showDefinitions, setShowDefinitions] = useState(false);

  const languageInfo = {
    greek: {
      name: 'Greek',
      nativeName: 'Ελληνικά',
      fontClass: 'font-serif',
      icon: '🇬🇷',
      direction: 'ltr',
    },
    hebrew: {
      name: 'Hebrew',
      nativeName: 'עברית',
      fontClass: 'font-serif',
      icon: '🇮🇱',
      direction: 'rtl',
    },
    aramaic: {
      name: 'Aramaic',
      nativeName: 'ܐܪܡܝܐ',
      fontClass: 'font-serif',
      icon: '📜',
      direction: 'rtl',
    },
  };

  const info = languageInfo[language];

  return (
    <div className="original-language-display bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg p-6 border border-amber-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <span>{info.icon}</span>
          <span>Original {info.name}</span>
          <span className="text-sm font-normal text-gray-600">({info.nativeName})</span>
        </h3>

        {words.length > 0 && (
          <button
            onClick={() => setShowDefinitions(!showDefinitions)}
            className="text-sm px-3 py-1 bg-amber-200 hover:bg-amber-300 text-amber-900 rounded-lg transition-colors"
          >
            {showDefinitions ? 'Hide Definitions' : 'Show Definitions'}
          </button>
        )}
      </div>

      {/* Original Text */}
      <div className={`mb-6 ${info.direction === 'rtl' ? 'text-right' : 'text-left'}`}>
        <p
          className={`text-3xl leading-relaxed ${info.fontClass} text-gray-900`}
          dir={info.direction}
        >
          {text}
        </p>
      </div>

      {/* Transliteration */}
      {transliteration && (
        <div className="mb-6 pb-6 border-b border-amber-200">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Transliteration
          </label>
          <p className="text-lg italic text-gray-800">{transliteration}</p>
        </div>
      )}

      {/* Strong's Numbers */}
      {strongs.length > 0 && (
        <div className="mb-6 pb-6 border-b border-amber-200">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Strong's Concordance Numbers
          </label>
          <div className="flex flex-wrap gap-2">
            {strongs.map((num, index) => (
              <a
                key={index}
                href={`https://www.blueletterbible.org/lexicon/${num}/kjv/tr/0-1/`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-purple-100 hover:bg-purple-200 text-purple-800 rounded-lg text-sm font-medium transition-colors"
              >
                <span>{num}</span>
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Interlinear Word Analysis */}
      {showInterlinear && words.length > 0 && (
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Interlinear Analysis
          </label>

          <div className={`grid gap-3 ${info.direction === 'rtl' ? 'direction-rtl' : ''}`}>
            {words.map((word, index) => (
              <div
                key={index}
                className={`p-4 bg-white rounded-lg border ${
                  selectedWord === word ? 'border-primary-500 ring-2 ring-primary-200' : 'border-gray-200'
                } hover:border-primary-300 transition-all cursor-pointer`}
                onClick={() => setSelectedWord(selectedWord === word ? null : word)}
              >
                <div className="flex items-start gap-4">
                  {/* Word Number */}
                  <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-semibold text-gray-600">
                    {word.word_order || index + 1}
                  </div>

                  <div className="flex-1 space-y-2">
                    {/* Original Word */}
                    <p
                      className={`text-2xl ${info.fontClass} text-gray-900`}
                      dir={info.direction}
                    >
                      {word.word}
                    </p>

                    {/* Transliteration */}
                    {word.transliteration && (
                      <p className="text-sm italic text-gray-700">{word.transliteration}</p>
                    )}

                    {/* Strong's Number */}
                    {word.strongs_number && (
                      <div className="flex items-center gap-2">
                        <a
                          href={`https://www.blueletterbible.org/lexicon/${word.strongs_number}/kjv/tr/0-1/`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 hover:bg-purple-200 text-purple-800 rounded text-xs font-medium transition-colors"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {word.strongs_number}
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>

                        {word.morphology && (
                          <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                            {word.morphology}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Definition (shown when showDefinitions is true or word is selected) */}
                    {word.definition && (showDefinitions || selectedWord === word) && (
                      <div className="mt-2 pt-2 border-t border-gray-100">
                        <p className="text-sm text-gray-700">{word.definition}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="mt-6 pt-6 border-t border-amber-200">
        <p className="text-xs text-gray-600">
          💡 <strong>Tip:</strong> Click on Strong's numbers to view full lexical entries at Blue Letter Bible.
          {words.length > 0 && ' Click on words to see their definitions.'}
        </p>
      </div>
    </div>
  );
}

/**
 * CompactOriginalLanguage - A condensed version for inline display
 */
export function CompactOriginalLanguage({
  language,
  text,
  transliteration,
}: Pick<OriginalLanguageProps, 'language' | 'text' | 'transliteration'>) {
  const icons = {
    greek: '🇬🇷',
    hebrew: '🇮🇱',
    aramaic: '📜',
  };

  const directions = {
    greek: 'ltr',
    hebrew: 'rtl',
    aramaic: 'rtl',
  };

  return (
    <div className="compact-original-language inline-flex items-center gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
      <span className="text-lg">{icons[language]}</span>
      <div className="flex-1">
        <p
          className="font-serif text-lg text-gray-900"
          dir={directions[language]}
        >
          {text}
        </p>
        {transliteration && (
          <p className="text-sm italic text-gray-600 mt-1">{transliteration}</p>
        )}
      </div>
    </div>
  );
}
