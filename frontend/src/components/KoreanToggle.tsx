'use client';

import { useState } from 'react';
const Aromanize = require('aromanize/base');

export type KoreanDisplayMode = 'hangul' | 'romanization';

interface KoreanToggleProps {
  onModeChange?: (mode: KoreanDisplayMode) => void;
  defaultMode?: KoreanDisplayMode;
  className?: string;
}

/**
 * KoreanToggle component provides a toggle interface for switching between
 * different Korean text display modes:
 * - Hangul (한글): Standard Korean script
 * - Hanja (漢字): Chinese characters with Korean pronunciation
 * - Romanization (로마자): Latin alphabet transliteration
 */
export default function KoreanToggle({
  onModeChange,
  defaultMode = 'hangul',
  className = '',
}: KoreanToggleProps) {
  const [mode, setMode] = useState<KoreanDisplayMode>(defaultMode);

  const handleModeChange = (newMode: KoreanDisplayMode) => {
    setMode(newMode);
    if (onModeChange) {
      onModeChange(newMode);
    }
  };

  const modes: { value: KoreanDisplayMode; label: string; icon: string }[] = [
    { value: 'hangul', label: '한글', icon: '가' },
    { value: 'romanization', label: 'ABC', icon: 'A' },
  ];

  return (
    <div className={`korean-toggle ${className}`}>
      <div className="inline-flex rounded-lg border border-gray-200 bg-white p-1 shadow-sm">
        {modes.map((m) => (
          <button
            key={m.value}
            onClick={() => handleModeChange(m.value)}
            className={`
              px-3 py-2 text-sm font-medium rounded-md transition-all duration-200
              flex items-center gap-2 min-w-[80px] justify-center
              ${
                mode === m.value
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'text-gray-700 hover:bg-gray-100'
              }
            `}
            aria-label={`Switch to ${m.label} mode`}
            aria-pressed={mode === m.value}
          >
            <span className="text-lg">{m.icon}</span>
            <span className="text-xs">{m.label}</span>
          </button>
        ))}
      </div>

      {/* Optional: Display current mode description */}
      <div className="mt-2 text-xs text-gray-500 text-center">
        {mode === 'hangul' && 'Standard Korean script'}
        {mode === 'romanization' && 'Latin alphabet transliteration'}
      </div>
    </div>
  );
}

/**
 * Compact version of KoreanToggle for inline use in cards/headers
 */
export function CompactKoreanToggle({
  onModeChange,
  defaultMode = 'hangul',
  className = '',
}: KoreanToggleProps) {
  const [mode, setMode] = useState<KoreanDisplayMode>(defaultMode);

  const handleModeChange = (newMode: KoreanDisplayMode) => {
    setMode(newMode);
    if (onModeChange) {
      onModeChange(newMode);
    }
  };

  const modes: { value: KoreanDisplayMode; icon: string; tooltip: string }[] = [
    { value: 'hangul', icon: '가', tooltip: 'Hangul (한글)' },
    { value: 'romanization', icon: 'A', tooltip: 'Romanization' },
  ];

  return (
    <div className={`inline-flex gap-1 ${className}`}>
      {modes.map((m) => (
        <button
          key={m.value}
          onClick={() => handleModeChange(m.value)}
          title={m.tooltip}
          className={`
            w-8 h-8 rounded-md text-sm font-medium transition-all duration-200
            flex items-center justify-center
            ${
              mode === m.value
                ? 'bg-primary-500 text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }
          `}
          aria-label={`Switch to ${m.tooltip}`}
          aria-pressed={mode === m.value}
        >
          {m.icon}
        </button>
      ))}
    </div>
  );
}

/**
 * Hook for managing Korean text transformation based on display mode
 */
export function useKoreanText() {
  const [mode, setMode] = useState<KoreanDisplayMode>('hangul');

  /**
   * Transform Korean text based on the current display mode
   */
  const transformText = (text: string): string => {
    if (!text) return text;

    switch (mode) {
      case 'hangul':
        return text; // Original Korean text

      case 'romanization':
        // Use aromanize library for Revised Romanization
        try {
          return Aromanize.romanize(text);
        } catch (error) {
          console.error('Romanization error:', error);
          return text; // Fallback to original on error
        }

      default:
        return text;
    }
  };

  return {
    mode,
    setMode,
    transformText,
  };
}
