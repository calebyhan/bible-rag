'use client';

import { useState } from 'react';
import { ChatMessage, ChatMessageAssistant, SearchResponse } from '@/types';
import VerseCard from './VerseCard';

interface ChatMessageBubbleProps {
  message: ChatMessage;
  userQuery?: string;
  defaultTranslation?: string;
}

function VerseResultsDropdown({ results, defaultTranslation }: { results: SearchResponse; defaultTranslation: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [showLanguage, setShowLanguage] = useState<'default' | 'all'>('default');
  const { results: verses, search_metadata, query_time_ms } = results;

  if (verses.length === 0) return null;

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary hover:text-text-secondary dark:hover:text-text-dark-secondary transition-colors"
      >
        <span className="transition-transform inline-block" style={{ transform: isOpen ? 'rotate(90deg)' : 'rotate(0deg)' }}>
          ▸
        </span>
        <span>
          {search_metadata.total_results} verse{search_metadata.total_results !== 1 ? 's' : ''} found
        </span>
        <span className="text-text-tertiary dark:text-text-dark-tertiary">
          · {query_time_ms}ms
          {search_metadata.cached && ' · cached'}
        </span>
      </button>

      {isOpen && (
        <div className="mt-3">
          {/* Language toggle */}
          <div className="flex items-center gap-2 mb-3">
            <button
              onClick={() => setShowLanguage('default')}
              className={`font-ui text-xs uppercase tracking-wide transition-colors pb-0.5 ${
                showLanguage === 'default'
                  ? 'text-text-primary dark:text-text-dark-primary border-b border-text-primary dark:border-text-dark-primary'
                  : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-secondary dark:hover:text-text-dark-secondary border-b border-transparent'
              }`}
            >
              Default
            </button>
            <button
              onClick={() => setShowLanguage('all')}
              className={`font-ui text-xs uppercase tracking-wide transition-colors pb-0.5 ${
                showLanguage === 'all'
                  ? 'text-text-primary dark:text-text-dark-primary border-b border-text-primary dark:border-text-dark-primary'
                  : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-secondary dark:hover:text-text-dark-secondary border-b border-transparent'
              }`}
            >
              All
            </button>
          </div>

          <div className="space-y-3">
            {verses.map((verse, index) => (
              <VerseCard
                key={`${verse.reference.book}-${verse.reference.chapter}-${verse.reference.verse}`}
                result={verse}
                showAllTranslations={showLanguage === 'all'}
                defaultTranslation={defaultTranslation}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ChatMessageBubble({ message, userQuery, defaultTranslation = 'NIV' }: ChatMessageBubbleProps) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[80%] bg-surface dark:bg-surface-dark border border-border-light dark:border-border-dark px-4 py-3 rounded-lg">
          <p className="font-body text-text-primary dark:text-text-dark-primary">
            {message.content}
          </p>
          <div className="mt-1 flex gap-2">
            {message.translations.map((t) => (
              <span
                key={t}
                className={`font-ui text-[10px] uppercase tracking-wide ${
                  t === message.defaultTranslation
                    ? 'text-accent-scripture dark:text-accent-dark-scripture font-bold'
                    : 'text-text-tertiary dark:text-text-dark-tertiary'
                }`}
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Assistant message
  const msg = message as ChatMessageAssistant;

  // Detect if AI text is primarily Korean
  const isKorean = msg.aiText &&
    /[\uac00-\ud7a3]/.test(msg.aiText) &&
    (msg.aiText.match(/[\uac00-\ud7a3]/g)?.length || 0) > msg.aiText.length * 0.3;

  return (
    <div className="flex justify-start mb-6">
      <div className="w-full max-w-[90%]">
        {/* Error */}
        {msg.error && (
          <div className="mb-3 p-3 border border-error dark:border-error-dark bg-surface dark:bg-surface-dark rounded-lg">
            <p className="font-ui text-xs font-medium text-error dark:text-error-dark uppercase tracking-wide">Error / 오류</p>
            <p className="font-body text-sm text-text-secondary dark:text-text-dark-secondary mt-1">{msg.error}</p>
          </div>
        )}

        {/* Loading spinner */}
        {msg.isStreaming && !msg.aiText && !msg.results && (
          <div className="py-2">
            <div className="flex items-center gap-3">
              <div className="spinner w-4 h-4" />
              <span className="text-text-tertiary dark:text-text-dark-tertiary font-body italic text-sm">
                Searching the Scriptures...
              </span>
            </div>
          </div>
        )}

        {/* AI text as plain chat text */}
        {msg.aiText && (
          <p className={`${isKorean ? 'font-korean korean-text' : 'font-body'} text-base leading-relaxed text-text-primary dark:text-text-dark-primary`}>
            {msg.aiText}
          </p>
        )}

        {/* Streaming indicator after text */}
        {msg.isStreaming && msg.aiText && (
          <span className="inline-block w-1.5 h-4 bg-text-tertiary dark:bg-text-dark-tertiary animate-pulse ml-0.5 align-text-bottom" />
        )}

        {/* Verse results as collapsible dropdown */}
        {msg.results && (
          <VerseResultsDropdown
            results={msg.results}
            defaultTranslation={defaultTranslation}
          />
        )}
      </div>
    </div>
  );
}
