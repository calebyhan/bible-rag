'use client';

import { useState, useEffect } from 'react';

export default function DarkModeToggle() {
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Load saved preference on mount
  useEffect(() => {
    setMounted(true);
    const savedMode = localStorage.getItem('darkMode');
    // Default to light mode unless explicitly set to dark
    const prefersDark = savedMode === 'true';

    setIsDark(prefersDark);
    if (prefersDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    const newMode = !isDark;
    setIsDark(newMode);
    localStorage.setItem('darkMode', String(newMode));

    if (newMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <button
        className="w-10 h-10 flex items-center justify-center font-ui text-xs uppercase tracking-wide font-semibold transition-colors border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark"
        disabled
      >
        <span className="opacity-0">☀</span>
      </button>
    );
  }

  return (
    <button
      onClick={toggleDarkMode}
      className="w-10 h-10 flex items-center justify-center font-ui text-xs uppercase tracking-wide font-semibold transition-colors border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? '☀' : '☾'}
    </button>
  );
}
