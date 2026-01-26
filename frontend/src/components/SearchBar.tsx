'use client';

import { useState, FormEvent, useEffect } from 'react';
import { getTranslations } from '@/lib/api';

interface SearchBarProps {
  onSearch: (query: string, translations: string[], defaultTranslation: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  initialQuery?: string;
  initialTranslations?: string[];
  initialDefaultTranslation?: string;
}

interface Translation {
  abbrev: string;
  name: string;
  language: string;
}

export default function SearchBar({
  onSearch,
  isLoading = false,
  placeholder = 'Search the Bible...',
  initialQuery = '',
  initialTranslations = ['NIV', 'KRV'],
  initialDefaultTranslation = 'NIV',
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
  const [selectedTranslations, setSelectedTranslations] = useState<string[]>(initialTranslations);
  const [defaultTranslation, setDefaultTranslation] = useState<string>(initialDefaultTranslation);
  const [showFilters, setShowFilters] = useState(false);
  const [translations, setTranslations] = useState<Translation[]>([]);
  const [translationsLoading, setTranslationsLoading] = useState(true);

  useEffect(() => {
    const fetchTranslations = async () => {
      try {
        const response = await getTranslations();
        const mappedTranslations = response.translations
          .filter(t => !t.is_original_language)
          .map(t => ({
            abbrev: t.abbreviation,
            name: t.name,
            language: t.language_code,
          }));

        const uniqueTranslations = mappedTranslations.filter(
          (trans, index, self) =>
            index === self.findIndex(t => t.abbrev === trans.abbrev)
        );

        setTranslations(uniqueTranslations);
      } catch (error) {
        console.error('Failed to fetch translations:', error);
        setTranslations([
          { abbrev: 'NIV', name: 'New International Version', language: 'en' },
          { abbrev: 'ESV', name: 'English Standard Version', language: 'en' },
          { abbrev: 'KJV', name: 'King James Version', language: 'en' },
          { abbrev: 'KRV', name: '개역한글', language: 'ko' },
          { abbrev: 'NKRV', name: '개역개정', language: 'ko' },
        ]);
      } finally {
        setTranslationsLoading(false);
      }
    };

    fetchTranslations();
  }, []);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), selectedTranslations, defaultTranslation);
    }
  };

  const toggleTranslation = (abbrev: string, isDoubleClick: boolean = false) => {
    const isSelected = selectedTranslations.includes(abbrev);
    const isDefault = abbrev === defaultTranslation;

    if (isDoubleClick) {
      setDefaultTranslation(abbrev);
      if (!isSelected) {
        setSelectedTranslations((prev) => [...prev, abbrev]);
      }
      return;
    }

    if (isSelected) {
      if (selectedTranslations.length === 1) return;
      if (isDefault) return;
      setSelectedTranslations((prev) => prev.filter((t) => t !== abbrev));
    } else {
      setSelectedTranslations((prev) => [...prev, abbrev]);
    }
  };

  return (
    <div className="w-full max-w-content mx-auto">
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className="search-input pr-32 dark:bg-background-dark dark:text-text-dark-primary dark:border-text-dark-primary dark:placeholder:text-text-dark-tertiary"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 btn-primary text-xs dark:bg-text-dark-primary dark:text-background-dark dark:border-text-dark-primary dark:hover:bg-background-dark dark:hover:text-text-dark-primary"
          >
            {isLoading ? (
              <span className="spinner" />
            ) : (
              <span>Search</span>
            )}
          </button>
        </div>

        {/* Translation filter toggle */}
        <div className="mt-4 flex justify-center">
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="btn-text dark:text-text-dark-secondary dark:hover:text-text-dark-primary dark:border-text-dark-tertiary dark:hover:border-text-dark-primary"
          >
            {showFilters ? '▾' : '▸'} Translations
          </button>
        </div>

        {/* Translation filters - underlined text buttons */}
        {showFilters && (
          <div className="mt-3 space-y-2">
            {translationsLoading ? (
              <div className="text-center text-text-tertiary dark:text-text-dark-tertiary text-sm">Loading translations...</div>
            ) : (
              <div className="flex flex-wrap justify-center gap-4">
                {translations.map((trans) => {
                  const isSelected = selectedTranslations.includes(trans.abbrev);
                  const isDefault = trans.abbrev === defaultTranslation;

                  return (
                    <button
                      key={trans.abbrev}
                      type="button"
                      onClick={() => toggleTranslation(trans.abbrev, false)}
                      onDoubleClick={() => toggleTranslation(trans.abbrev, true)}
                      className={`font-ui text-sm transition-colors ${
                        isSelected
                          ? 'text-text-primary dark:text-text-dark-primary border-b-2 border-accent-scripture dark:border-accent-dark-scripture'
                          : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-secondary dark:hover:text-text-dark-secondary border-b-2 border-transparent'
                      } ${isDefault ? 'font-bold' : 'font-normal'}`}
                      title={isDefault ? `${trans.name} (Default)` : trans.name}
                    >
                      {isDefault && <span className="text-accent-scripture dark:text-accent-dark-scripture mr-1">★</span>}
                      {trans.name}
                    </button>
                  );
                })}
              </div>
            )}
            <p className="text-xs text-center text-text-tertiary dark:text-text-dark-tertiary font-ui">
              Click to select/deselect • Double-click to set as default (★)
            </p>
          </div>
        )}
      </form>

      {/* Example queries */}
      <div className="mt-space-md text-center text-sm text-text-secondary dark:text-text-dark-secondary">
        <p className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-2">Try searching:</p>
        <div className="mt-2 flex flex-wrap justify-center gap-3">
          {[
            'love and forgiveness',
            '사랑에 대한 예수님의 말씀',
            'faith in difficult times',
            '기도에 관한 구절',
          ].map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => setQuery(example)}
              className="font-ui text-sm text-text-secondary dark:text-text-dark-secondary hover:text-text-primary dark:hover:text-text-dark-primary transition-colors border-b border-transparent hover:border-text-secondary dark:hover:border-text-dark-secondary"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
