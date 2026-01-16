'use client';

import { useState } from 'react';

interface InfoTooltipProps {
  title: string;
  description: string;
}

export default function InfoTooltip({ title, description }: InfoTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        type="button"
        className="ml-2 inline-flex items-center justify-center w-5 h-5 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 bg-gray-100 dark:bg-slate-700 rounded-full transition-colors"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        aria-label={`Information about ${title}`}
      >
        i
      </button>

      {isVisible && (
        <div className="absolute z-50 left-0 mt-2 w-72 p-3 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg shadow-lg">
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">{title}</p>
          <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">{description}</p>
        </div>
      )}
    </div>
  );
}
