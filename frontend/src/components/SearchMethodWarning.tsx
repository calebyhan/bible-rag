'use client';

import { useState, useEffect } from 'react';
import { checkHealth } from '@/lib/api';

interface SearchMethodWarningProps {
  searchMetadata?: {
    embedding_model?: string;
    cached?: boolean;
    error?: string;
  };
}

export default function SearchMethodWarning({ searchMetadata }: SearchMethodWarningProps) {
  const [showWarning, setShowWarning] = useState(false);
  const [hasSeenWarning, setHasSeenWarning] = useState(false);
  const [isProduction, setIsProduction] = useState(false);

  useEffect(() => {
    // Check if user has already dismissed this warning in this session
    if (typeof window !== 'undefined') {
      const seen = sessionStorage.getItem('search-warning-seen');
      setHasSeenWarning(seen === 'true');
    }

    // Detect production by checking API URL (localhost = development)
    const checkEnvironment = async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const isLocalhost = apiUrl.includes('localhost') || apiUrl.includes('127.0.0.1');

      // If not localhost, we're in production
      if (!isLocalhost) {
        setIsProduction(true);
        if (!sessionStorage.getItem('search-warning-seen')) {
          setShowWarning(true);
        }
        return;
      }

      // If localhost, try health check to verify
      // If health check fails (backend down), assume production as safety measure
      try {
        const health = await checkHealth();
        // Backend is up - check if it's using Gemini embeddings mode
        const isProd = health.services?.embedding_mode === 'gemini';
        setIsProduction(isProd);

        if (isProd && !sessionStorage.getItem('search-warning-seen')) {
          setShowWarning(true);
        }
      } catch (error) {
        // Backend is down - assume production and show warning
        console.warn('Backend health check failed, assuming production environment:', error);
        setIsProduction(true);
        if (!sessionStorage.getItem('search-warning-seen')) {
          setShowWarning(true);
        }
      }
    };

    checkEnvironment();
  }, []);

  useEffect(() => {
    // Also show warning if we get search results with Gemini embeddings
    if (
      searchMetadata &&
      !hasSeenWarning &&
      searchMetadata.embedding_model &&
      searchMetadata.embedding_model.toLowerCase().includes('gemini')
    ) {
      setShowWarning(true);
    }
  }, [searchMetadata, hasSeenWarning]);

  const handleClose = () => {
    setShowWarning(false);
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('search-warning-seen', 'true');
      setHasSeenWarning(true);
    }
  };

  if (!showWarning) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="max-w-lg mx-4 bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-amber-200 dark:border-amber-700">
        {/* Warning Icon Header */}
        <div className="bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-700 px-6 py-4 rounded-t-xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-100 dark:bg-amber-800 rounded-full flex items-center justify-center">
              <svg
                className="w-6 h-6 text-amber-600 dark:text-amber-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Production Version Notice
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">프로덕션 버전 알림</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-5 space-y-4">
          <div className="space-y-2">
            <p className="text-gray-700 dark:text-gray-200">
              You're using the <strong>production version</strong> of Bible RAG. Please note:
            </p>
            <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-300 text-sm ml-2">
              <li>
                This version is <strong>not the most actively maintained</strong> (blame free hosting limitations 😔)
              </li>
              <li>
                Processing will be <strong>significantly slower</strong> than local instances
              </li>
              <li>
                Limited resources may result in longer wait times
              </li>
              <li>
                <strong>Semantic search is not available</strong> - only keyword matching works
              </li>
            </ul>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
            <p className="text-sm text-blue-800 dark:text-blue-200 font-medium mb-2">
              For the best performance and accuracy:
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">
              We recommend running Bible RAG locally for full semantic search capabilities and faster performance.
            </p>
            <a
              href="https://github.com/calebyhan/bible-rag"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              View on GitHub
            </a>
          </div>

          <div className="space-y-2 pt-2 border-t border-gray-200 dark:border-slate-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <strong>프로덕션 버전</strong>을 사용하고 있습니다. 무료 호스팅 제한으로 인해 처리 속도가 느리고 의미 기반 검색이 불가능합니다.
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              최상의 성능을 위해 로컬에서 실행하는 것을 권장합니다.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="bg-gray-50 dark:bg-slate-900/50 px-6 py-4 rounded-b-xl flex gap-3 justify-end border-t border-gray-200 dark:border-slate-700">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
          >
            Got it, continue anyway
          </button>
        </div>
      </div>
    </div>
  );
}
