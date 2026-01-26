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
 * Parse morphology code into human-readable description
 */
const parseMorphology = (code: string, language: string): string => {
  if (!code) return '';

  if (language === 'greek') {
    // Greek morphology patterns (e.g., "V-AAI-3S")
    const parts = code.split('-');
    const descriptions: string[] = [];

    // Part of speech
    const posMap: Record<string, string> = {
      'V': 'Verb',
      'N': 'Noun',
      'A': 'Adjective',
      'P': 'Personal Pronoun',
      'R': 'Relative Pronoun',
      'D': 'Demonstrative Pronoun',
      'C': 'Conjunction',
      'T': 'Article',
      'PREP': 'Preposition',
      'ADV': 'Adverb',
      'CONJ': 'Conjunction',
      'PRT': 'Particle',
      'INJ': 'Interjection',
    };
    descriptions.push(posMap[parts[0]] || parts[0]);

    // For verbs: tense, voice, mood
    if (parts[0] === 'V' && parts[1]) {
      const tenseMap: Record<string, string> = {
        'P': 'Present', 'I': 'Imperfect', 'F': 'Future',
        'A': 'Aorist', 'X': 'Perfect', 'Y': 'Pluperfect',
      };
      const voiceMap: Record<string, string> = {
        'A': 'Active', 'M': 'Middle', 'P': 'Passive',
      };
      const moodMap: Record<string, string> = {
        'I': 'Indicative', 'S': 'Subjunctive', 'O': 'Optative',
        'M': 'Imperative', 'N': 'Infinitive', 'P': 'Participle',
      };

      const tense = tenseMap[parts[1][0]] || '';
      const voice = voiceMap[parts[1][1]] || '';
      const mood = moodMap[parts[1][2]] || '';

      if (tense) descriptions.push(tense);
      if (voice) descriptions.push(voice);
      if (mood) descriptions.push(mood);
    }

    // Person and number (e.g., "3S" = 3rd person singular)
    if (parts[2]) {
      const personMap: Record<string, string> = { '1': '1st person', '2': '2nd person', '3': '3rd person' };
      const numberMap: Record<string, string> = { 'S': 'Singular', 'P': 'Plural' };

      const person = personMap[parts[2][0]] || '';
      const number = numberMap[parts[2][1]] || '';

      if (person) descriptions.push(person);
      if (number) descriptions.push(number);
    }

    return descriptions.join(', ');
  }

  // Hebrew morphology (simpler for now)
  if (language === 'hebrew') {
    return code; // Could add Hebrew parsing logic here
  }

  return code;
};

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
  const [copied, setCopied] = useState(false);
  const [highlightedStrongs, setHighlightedStrongs] = useState<string | null>(null);

  const handleCopyText = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleWordClick = (word: OriginalWord) => {
    // Toggle selection
    const newSelectedWord = selectedWord === word ? null : word;
    setSelectedWord(newSelectedWord);

    // Highlight all words with the same Strong's number
    if (newSelectedWord?.strongs_number) {
      setHighlightedStrongs(
        highlightedStrongs === newSelectedWord.strongs_number
          ? null
          : newSelectedWord.strongs_number
      );
    } else {
      setHighlightedStrongs(null);
    }
  };

  // Count words with the same Strong's number
  const getStrongsCount = (strongsNumber: string): number => {
    return words.filter(w => w.strongs_number === strongsNumber).length;
  };

  const languageInfo = {
    greek: {
      name: 'Greek',
      nativeName: 'Ελληνικά',
      direction: 'ltr',
      color: 'text-accent-greek dark:text-accent-dark-greek',
    },
    hebrew: {
      name: 'Hebrew',
      nativeName: 'עברית',
      direction: 'rtl',
      color: 'text-accent-hebrew dark:text-accent-dark-hebrew',
    },
    aramaic: {
      name: 'Aramaic',
      nativeName: 'ܐܪܡܝܐ',
      direction: 'rtl',
      color: 'text-accent-reference dark:text-accent-dark-reference',
    },
  };

  const info = languageInfo[language];

  return (
    <div className="border-t-2 border-b-2 border-text-tertiary dark:border-text-dark-tertiary py-space-lg px-space-md my-space-md bg-surface dark:bg-surface-dark transition-colors">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-0 mb-space-md">
        <div>
          <h3 className={`font-ui text-sm uppercase tracking-wide ${info.color} font-semibold`}>
            Original {info.name}
          </h3>
          <p className="font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary mt-1">{info.nativeName}</p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Copy button */}
          <button
            onClick={handleCopyText}
            className="btn-text dark:text-text-dark-secondary dark:hover:text-text-dark-primary dark:border-text-dark-tertiary dark:hover:border-text-dark-primary"
            title="Copy original text"
          >
            {copied ? 'Copied!' : 'Copy Text'}
          </button>

          {words.length > 0 && (
            <button
              onClick={() => setShowDefinitions(!showDefinitions)}
              className="btn-text dark:text-text-dark-secondary dark:hover:text-text-dark-primary dark:border-text-dark-tertiary dark:hover:border-text-dark-primary"
            >
              {showDefinitions ? 'Hide Definitions' : 'Show Definitions'}
            </button>
          )}
        </div>
      </div>

      {/* Original Text */}
      <div className={`mb-space-sm ${info.direction === 'rtl' ? 'text-right' : 'text-left'}`}>
        <p
          className={`original-text ${info.color}`}
          dir={info.direction}
        >
          {text}
        </p>
      </div>

      {/* Transliteration */}
      {transliteration && (
        <div className="mb-space-sm pb-space-sm border-b border-border-light dark:border-border-dark-light">
          <label className="block font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-1">
            Transliteration
          </label>
          <p className="font-body text-base italic text-text-secondary dark:text-text-dark-secondary">{transliteration}</p>
        </div>
      )}

      {/* Strong's Numbers */}
      {strongs.length > 0 && (
        <div className="mb-space-sm pb-space-sm border-b border-border-light dark:border-border-dark-light">
          <label className="block font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-2">
            Strong's Concordance Numbers
          </label>
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {strongs.map((num, index) => (
              <a
                key={index}
                href={`https://www.blueletterbible.org/lexicon/${num}/kjv/tr/0-1/`}
                target="_blank"
                rel="noopener noreferrer"
                className="verse-ref dark:text-accent-dark-reference dark:hover:border-accent-dark-reference"
              >
                {num}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Interlinear Word Analysis */}
      {showInterlinear && words.length > 0 && (
        <details className="border-t border-border-light dark:border-border-dark-light">
          <summary className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary cursor-pointer py-space-sm">
            Interlinear Analysis ({words.length} words)
          </summary>

          <div className={`mt-space-sm space-y-2 ${info.direction === 'rtl' ? 'direction-rtl' : ''}`}>
            {words.map((word, index) => {
              const isSelected = selectedWord === word;
              const isHighlighted = highlightedStrongs && word.strongs_number === highlightedStrongs;
              const wordCount = word.strongs_number ? getStrongsCount(word.strongs_number) : 0;

              return (
                <div
                  key={index}
                  className={`relative p-space-sm border-2 transition-all cursor-pointer ${
                    isSelected
                      ? 'border-text-primary dark:border-text-dark-primary bg-surface dark:bg-surface-dark'
                      : isHighlighted
                      ? 'border-accent-relevance dark:border-accent-dark-relevance bg-background dark:bg-background-dark'
                      : 'border-border-light dark:border-border-dark-light hover:border-border-medium dark:hover:border-border-dark-medium bg-surface dark:bg-surface-dark'
                  }`}
                  onClick={() => handleWordClick(word)}
                >
                  <div className="flex items-start gap-3">
                    {/* Word Number */}
                    <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center font-ui text-xs font-semibold text-text-tertiary dark:text-text-dark-tertiary">
                      {word.word_order || index + 1}
                    </div>

                    <div className="flex-1 space-y-1">
                      {/* Original Word */}
                      <p
                        className={`original-text ${info.color}`}
                        dir={info.direction}
                      >
                        {word.word}
                      </p>

                      {/* Transliteration */}
                      {word.transliteration && (
                        <p className="font-body text-sm italic text-text-secondary dark:text-text-dark-secondary">{word.transliteration}</p>
                      )}

                      {/* Strong's Number and Morphology */}
                      {word.strongs_number && (
                        <div className="flex flex-wrap items-center gap-2">
                          <a
                            href={`https://www.blueletterbible.org/lexicon/${word.strongs_number}/kjv/tr/0-1/`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="verse-ref dark:text-accent-dark-reference dark:hover:border-accent-dark-reference"
                            onClick={(e) => e.stopPropagation()}
                            title="View in Blue Letter Bible"
                          >
                            {word.strongs_number}
                          </a>

                          <a
                            href={`/search?strongs=${word.strongs_number}`}
                            className="font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary border-b border-transparent hover:border-text-tertiary dark:hover:border-text-dark-tertiary"
                            onClick={(e) => e.stopPropagation()}
                            title={`Find all verses with ${word.strongs_number}`}
                          >
                            Find all
                          </a>

                          {word.morphology && (
                            <span
                              className="font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary border-b border-border-light dark:border-border-dark-light cursor-help"
                              title={parseMorphology(word.morphology, language)}
                            >
                              {word.morphology}
                            </span>
                          )}

                          {isHighlighted && wordCount > 1 && (
                            <span className="font-ui text-xs font-bold text-accent-relevance dark:text-accent-dark-relevance">
                              {wordCount}×
                            </span>
                          )}
                        </div>
                      )}

                      {/* Definition */}
                      {word.definition && (showDefinitions || selectedWord === word) && (
                        <div className="mt-2 pt-2 border-t border-border-light dark:border-border-dark-light">
                          <p className="font-body text-sm text-text-secondary dark:text-text-dark-secondary">{word.definition}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </details>
      )}

      {/* Highlight notification */}
      {highlightedStrongs && (
        <div className="mt-space-sm p-space-sm border-2 border-accent-relevance dark:border-accent-dark-relevance bg-surface dark:bg-surface-dark transition-colors">
          <p className="font-ui text-sm text-text-primary dark:text-text-dark-primary flex items-center justify-between">
            <span>
              Highlighting <strong>{highlightedStrongs}</strong> ({getStrongsCount(highlightedStrongs)} occurrence{getStrongsCount(highlightedStrongs) !== 1 ? 's' : ''})
            </span>
            <button
              onClick={() => setHighlightedStrongs(null)}
              className="font-ui text-sm text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary font-bold"
              title="Clear highlight"
            >
              ✕
            </button>
          </p>
        </div>
      )}

      {/* Help Text */}
      <div className="mt-space-sm pt-space-sm border-t border-border-light dark:border-border-dark-light">
        <p className="font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary">
          <strong>Note:</strong> Click on Strong's numbers to view full lexical entries. Click on words to highlight all occurrences of the same Strong's number.
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
  const directions = {
    greek: 'ltr',
    hebrew: 'rtl',
    aramaic: 'rtl',
  };

  const colors = {
    greek: 'text-accent-greek dark:text-accent-dark-greek',
    hebrew: 'text-accent-hebrew dark:text-accent-dark-hebrew',
    aramaic: 'text-accent-reference dark:text-accent-dark-reference',
  };

  return (
    <div className="inline-flex items-center gap-3 p-space-sm border-l-4 border-text-tertiary dark:border-text-dark-tertiary bg-surface dark:bg-surface-dark transition-colors">
      <div className="flex-1">
        <p
          className={`original-text ${colors[language]}`}
          dir={directions[language]}
        >
          {text}
        </p>
        {transliteration && (
          <p className="font-body text-sm italic text-text-tertiary dark:text-text-dark-tertiary mt-1">{transliteration}</p>
        )}
      </div>
    </div>
  );
}
