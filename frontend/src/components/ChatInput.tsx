'use client';

import { useState, useEffect, useRef, FormEvent, KeyboardEvent } from 'react';
import { getTranslations } from '@/lib/api';

interface ChatInputProps {
  onSend: (query: string) => void;
  isLoading: boolean;
  selectedTranslations: string[];
  defaultTranslation: string;
  onTranslationsChange: (translations: string[]) => void;
  onDefaultTranslationChange: (translation: string) => void;
}

interface TranslationOption {
  abbrev: string;
  name: string;
  language: string;
}

export default function ChatInput({
  onSend,
  isLoading,
  selectedTranslations,
  defaultTranslation,
  onTranslationsChange,
  onDefaultTranslationChange,
}: ChatInputProps) {
  const [query, setQuery] = useState('');
  const [showTranslations, setShowTranslations] = useState(false);
  const [translations, setTranslations] = useState<TranslationOption[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchTranslations = async () => {
      try {
        const response = await getTranslations();
        const mapped = response.translations
          .filter((t) => !t.is_original_language)
          .map((t) => ({
            abbrev: t.abbreviation,
            name: t.name,
            language: t.language_code,
          }));
        const unique = mapped.filter(
          (trans, index, self) =>
            index === self.findIndex((t) => t.abbrev === trans.abbrev)
        );
        setTranslations(unique);
      } catch {
        setTranslations([
          { abbrev: 'NIV', name: 'New International Version', language: 'en' },
          { abbrev: 'ESV', name: 'English Standard Version', language: 'en' },
          { abbrev: 'KJV', name: 'King James Version', language: 'en' },
          { abbrev: 'KRV', name: '개역한글', language: 'ko' },
          { abbrev: 'NKRV', name: '개역개정', language: 'ko' },
        ]);
      }
    };
    fetchTranslations();
  }, []);

  // Close popover on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setShowTranslations(false);
      }
    };
    if (showTranslations) {
      document.addEventListener('mousedown', handleClick);
      return () => document.removeEventListener('mousedown', handleClick);
    }
  }, [showTranslations]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [query]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSend(query.trim());
      setQuery('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent);
    }
  };

  const toggleTranslation = (abbrev: string, isDoubleClick: boolean = false) => {
    if (isDoubleClick) {
      onDefaultTranslationChange(abbrev);
      if (!selectedTranslations.includes(abbrev)) {
        onTranslationsChange([...selectedTranslations, abbrev]);
      }
      return;
    }

    const isSelected = selectedTranslations.includes(abbrev);
    const isDefault = abbrev === defaultTranslation;

    if (isSelected) {
      if (selectedTranslations.length === 1) return;
      if (isDefault) return;
      onTranslationsChange(selectedTranslations.filter((t) => t !== abbrev));
    } else {
      onTranslationsChange([...selectedTranslations, abbrev]);
    }
  };

  return (
    <div className="border-t border-border-light dark:border-border-dark bg-surface dark:bg-surface-dark transition-colors">
      <div className="max-w-[1000px] mx-auto px-4 py-3">
        {/* Translation popover */}
        {showTranslations && (
          <div
            ref={popoverRef}
            className="mb-3 p-3 border border-border-light dark:border-border-dark bg-background dark:bg-background-dark rounded-lg"
          >
            <div className="flex flex-wrap gap-3">
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
            <p className="text-xs text-center text-text-tertiary dark:text-text-dark-tertiary font-ui mt-2">
              Click to select/deselect · Double-click to set as default (★)
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          {/* Translation toggle button */}
          <button
            type="button"
            onClick={() => setShowTranslations(!showTranslations)}
            className="shrink-0 mb-0.5 font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary transition-colors px-2 py-2 border border-border-light dark:border-border-dark rounded-lg"
            title="Select translations"
          >
            {selectedTranslations.join(', ')}
          </button>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the Bible..."
            rows={1}
            disabled={isLoading}
            className="flex-1 resize-none overflow-y-auto font-body text-sm bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary border border-border-light dark:border-border-dark rounded-lg px-3 py-2 placeholder:text-text-tertiary dark:placeholder:text-text-dark-tertiary focus:outline-none focus:border-text-primary dark:focus:border-text-dark-primary transition-colors"
            style={{ maxHeight: '120px' }}
          />

          {/* Send button */}
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="shrink-0 mb-0.5 btn-primary text-xs px-4 py-2 dark:bg-text-dark-primary dark:text-background-dark dark:border-text-dark-primary dark:hover:bg-background-dark dark:hover:text-text-dark-primary disabled:opacity-40"
          >
            {isLoading ? <span className="spinner w-4 h-4" /> : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
}
