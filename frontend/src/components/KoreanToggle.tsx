'use client';

import { useState } from 'react';

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
      <div className="inline-flex border-2 border-text-primary dark:border-text-dark-primary">
        {modes.map((m) => (
          <button
            key={m.value}
            onClick={() => handleModeChange(m.value)}
            className={`
              px-space-sm py-space-xs font-ui text-sm font-semibold uppercase tracking-wide transition-all
              flex items-center gap-2 min-w-[80px] justify-center border-r-2 last:border-r-0 border-text-primary dark:border-text-dark-primary
              ${
                mode === m.value
                  ? 'bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark'
                  : 'bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark'
              }
            `}
            aria-label={`Switch to ${m.label} mode`}
            aria-pressed={mode === m.value}
          >
            <span className="text-base font-bold">{m.icon}</span>
            <span className="text-xs">{m.label}</span>
          </button>
        ))}
      </div>

      {/* Optional: Display current mode description */}
      <div className="mt-space-xs font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary text-center">
        {mode === 'hangul' && 'Standard Korean script'}
        {mode === 'romanization' && 'Latin alphabet transliteration'}
      </div>
    </div>
  );
}
