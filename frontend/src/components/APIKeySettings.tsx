'use client';

import { useState, useEffect, useRef } from 'react';
import {
  getGeminiApiKey,
  setGeminiApiKey,
  removeGeminiApiKey,
  getGroqApiKey,
  setGroqApiKey,
  removeGroqApiKey,
} from '@/lib/api';

interface APIKeySettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function APIKeySettings({ isOpen, onClose }: APIKeySettingsProps) {
  const [geminiKey, setGeminiKeyState] = useState('');
  const [groqKey, setGroqKeyState] = useState('');
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [showGroqKey, setShowGroqKey] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const modalRef = useRef<HTMLDivElement>(null);

  // Load existing keys on mount
  useEffect(() => {
    if (isOpen) {
      const existingGeminiKey = getGeminiApiKey();
      const existingGroqKey = getGroqApiKey();

      if (existingGeminiKey) {
        setGeminiKeyState(existingGeminiKey);
      }
      if (existingGroqKey) {
        setGroqKeyState(existingGroqKey);
      }
    }
  }, [isOpen]);

  // Close modal when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  const handleSave = () => {
    setSaveStatus('saving');

    // Save Gemini key
    if (geminiKey.trim()) {
      setGeminiApiKey(geminiKey.trim());
    } else {
      removeGeminiApiKey();
    }

    // Save Groq key
    if (groqKey.trim()) {
      setGroqApiKey(groqKey.trim());
    } else {
      removeGroqApiKey();
    }

    setSaveStatus('saved');
    setTimeout(() => {
      setSaveStatus('idle');
      onClose();
    }, 1000);
  };

  const handleClear = () => {
    removeGeminiApiKey();
    removeGroqApiKey();
    setGeminiKeyState('');
    setGroqKeyState('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/90 dark:bg-background-dark/90">
      <div ref={modalRef} className="bg-surface dark:bg-surface-dark border-2 border-text-primary dark:border-text-dark-primary max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto transition-colors">
        {/* Header */}
        <div className="flex items-center justify-between p-space-md border-b border-border-light dark:border-border-dark-light">
          <h2 className="font-heading text-2xl font-semibold text-text-primary dark:text-text-dark-primary">
            API Key Settings
          </h2>
          <button
            onClick={onClose}
            className="text-text-primary dark:text-text-dark-primary hover:text-text-scripture dark:hover:text-accent-dark-scripture"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-space-md space-y-space-md">
          {/* Info message */}
          <div className="border-l-4 border-border-light dark:border-border-dark-light pl-space-sm py-space-xs">
            <p className="font-body text-sm text-text-secondary dark:text-text-dark-secondary italic">
              <strong className="text-text-primary dark:text-text-dark-primary not-italic">Optional:</strong> Provide your own API keys for AI features. Keys are stored locally in your browser and sent securely with each request.
            </p>
          </div>

          {/* Groq API Key - PRIMARY */}
          <div>
            <label htmlFor="groq-key" className="block font-ui text-sm uppercase tracking-wide font-semibold text-text-primary dark:text-text-dark-primary mb-space-xs">
              Groq API Key (Primary)
            </label>
            <div className="relative">
              <input
                id="groq-key"
                type={showGroqKey ? 'text' : 'password'}
                value={groqKey}
                onChange={(e) => setGroqKeyState(e.target.value)}
                placeholder="gsk_..."
                className="w-full px-space-sm py-space-xs pr-12 border-2 border-text-primary dark:border-text-dark-primary bg-surface dark:bg-surface-dark text-text-primary dark:text-text-dark-primary font-body text-sm focus:outline-none focus:border-accent-scripture dark:focus:border-accent-dark-scripture transition-colors placeholder:italic placeholder:text-text-tertiary dark:placeholder:text-text-dark-tertiary"
              />
              <button
                type="button"
                onClick={() => setShowGroqKey(!showGroqKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary"
              >
                {showGroqKey ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            <p className="mt-space-xs font-ui text-xs text-text-secondary dark:text-text-dark-secondary">
              Get your free API key at{' '}
              <a
                href="https://console.groq.com/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="verse-ref"
              >
                Groq Console
              </a>
            </p>
          </div>

          {/* Gemini API Key - FALLBACK */}
          <div>
            <label htmlFor="gemini-key" className="block font-ui text-sm uppercase tracking-wide font-semibold text-text-primary dark:text-text-dark-primary mb-space-xs">
              Google Gemini API Key (Fallback)
            </label>
            <div className="relative">
              <input
                id="gemini-key"
                type={showGeminiKey ? 'text' : 'password'}
                value={geminiKey}
                onChange={(e) => setGeminiKeyState(e.target.value)}
                placeholder="AIza..."
                className="w-full px-space-sm py-space-xs pr-12 border-2 border-text-primary dark:border-text-dark-primary bg-surface dark:bg-surface-dark text-text-primary dark:text-text-dark-primary font-body text-sm focus:outline-none focus:border-accent-scripture dark:focus:border-accent-dark-scripture transition-colors placeholder:italic placeholder:text-text-tertiary dark:placeholder:text-text-dark-tertiary"
              />
              <button
                type="button"
                onClick={() => setShowGeminiKey(!showGeminiKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary"
              >
                {showGeminiKey ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            <p className="mt-space-xs font-ui text-xs text-text-secondary dark:text-text-dark-secondary">
              Get your free API key at{' '}
              <a
                href="https://aistudio.google.com/apikey"
                target="_blank"
                rel="noopener noreferrer"
                className="verse-ref"
              >
                Google AI Studio
              </a>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-space-md border-t border-border-light dark:border-border-dark-light transition-colors">
          <button
            onClick={handleClear}
            className="px-space-sm py-space-xs font-ui text-sm uppercase tracking-wide text-text-secondary dark:text-text-dark-secondary hover:text-text-primary dark:hover:text-text-dark-primary border-b border-transparent hover:border-text-primary dark:hover:border-text-dark-primary transition-colors"
          >
            Clear All Keys
          </button>

          <div className="flex gap-space-sm">
            <button
              onClick={onClose}
              className="px-space-sm py-space-xs font-ui text-sm uppercase tracking-wide border-2 border-text-primary dark:border-text-dark-primary bg-transparent text-text-primary dark:text-text-dark-primary hover:bg-text-primary dark:hover:bg-text-dark-primary hover:text-surface dark:hover:text-surface-dark transition-all"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saveStatus === 'saving'}
              className={`px-space-sm py-space-xs font-ui text-sm uppercase tracking-wide border-2 transition-all ${
                saveStatus === 'saving'
                  ? 'border-text-tertiary dark:border-text-dark-tertiary bg-transparent text-text-tertiary dark:text-text-dark-tertiary cursor-not-allowed'
                  : 'border-text-primary dark:border-text-dark-primary bg-text-primary dark:bg-text-dark-primary text-surface dark:text-surface-dark hover:bg-transparent hover:text-text-primary dark:hover:text-text-dark-primary'
              }`}
            >
              {saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'Saved!' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
