'use client';

import { useState, FormEvent } from 'react';

interface SearchBarProps {
  onSearch: (query: string, translations: string[], defaultTranslation: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

const TRANSLATIONS = [
  { abbrev: 'NIV', name: 'NIV', language: 'en' },
  { abbrev: 'ESV', name: 'ESV', language: 'en' },
  { abbrev: 'NASB', name: 'NASB', language: 'en' },
  { abbrev: 'KJV', name: 'KJV', language: 'en' },
  { abbrev: 'NLT', name: 'NLT', language: 'en' },
  { abbrev: 'RKV', name: '개역개정', language: 'ko' },
  { abbrev: 'KRV', name: '개역한글', language: 'ko' },
  { abbrev: 'NKRV', name: '새번역', language: 'ko' },
];

export default function SearchBar({
  onSearch,
  isLoading = false,
  placeholder = 'Search the Bible...',
}: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [selectedTranslations, setSelectedTranslations] = useState<string[]>(['NIV', 'RKV']);
  const [defaultTranslation, setDefaultTranslation] = useState<string>('NIV');
  const [showFilters, setShowFilters] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), selectedTranslations, defaultTranslation);
    }
  };

  const toggleTranslation = (abbrev: string, isDoubleClick: boolean = false) => {
    const isSelected = selectedTranslations.includes(abbrev);
    const isDefault = abbrev === defaultTranslation;

    // Double-click: always set as default
    if (isDoubleClick) {
      setDefaultTranslation(abbrev);
      // Ensure it's selected
      if (!isSelected) {
        setSelectedTranslations((prev) => [...prev, abbrev]);
      }
      return;
    }

    // Single-click: toggle selection (but can't deselect the default)
    if (isSelected) {
      // Can't deselect if it's the only one
      if (selectedTranslations.length === 1) return;

      // Can't deselect if it's the default - must double-click another first
      if (isDefault) return;

      // Deselect it
      setSelectedTranslations((prev) => prev.filter((t) => t !== abbrev));
    } else {
      // Select it
      setSelectedTranslations((prev) => [...prev, abbrev]);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className="search-input pr-24"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2 bg-primary-600 text-white rounded-full hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
            className="text-sm text-gray-200 hover:text-white flex items-center gap-1"
          >
            <span>Translations</span>
            <svg
              className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        {/* Translation filters */}
        {showFilters && (
          <div className="mt-3 space-y-2">
            <div className="flex flex-wrap justify-center gap-2">
              {TRANSLATIONS.map((trans) => {
                const isSelected = selectedTranslations.includes(trans.abbrev);
                const isDefault = trans.abbrev === defaultTranslation;

                return (
                  <button
                    key={trans.abbrev}
                    type="button"
                    onClick={() => toggleTranslation(trans.abbrev, false)}
                    onDoubleClick={() => toggleTranslation(trans.abbrev, true)}
                    className={`px-3 py-1.5 rounded-full text-sm transition-colors flex items-center gap-1 ${
                      isSelected
                        ? 'bg-primary-100 text-primary-700 border-2 border-primary-300'
                        : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                    } ${isDefault ? 'ring-2 ring-yellow-400' : ''}`}
                    title={isDefault ? `${trans.name} (Default)` : trans.name}
                  >
                    {isDefault && <span className="text-yellow-500">★</span>}
                    {trans.name}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-center text-gray-300">
              Click to select/deselect • Double-click to set as default (★) • Default can't be deselected
            </p>
          </div>
        )}
      </form>

      {/* Example queries */}
      <div className="mt-6 text-center text-sm text-gray-200">
        <p>Try searching:</p>
        <div className="mt-2 flex flex-wrap justify-center gap-2">
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
              className="px-3 py-1 bg-white/20 rounded-full text-white hover:bg-white/30 transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
