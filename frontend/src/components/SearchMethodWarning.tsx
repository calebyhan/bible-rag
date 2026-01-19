'use client';

import { useState, useEffect } from 'react';

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

  useEffect(() => {
    // Check if user has already dismissed this warning in this session
    if (typeof window !== 'undefined') {
      const seen = sessionStorage.getItem('search-warning-seen');
      setHasSeenWarning(seen === 'true');
    }
  }, []);

  useEffect(() => {
    // Show warning if we're using Gemini embeddings (production) instead of multilingual-e5
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
                Limited Search Functionality
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">제한된 검색 기능</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-5 space-y-4">
          <div className="space-y-2">
            <p className="text-gray-700 dark:text-gray-200">
              This production environment uses <strong>Gemini embeddings</strong> instead of the
              multilingual-e5 model. As a result:
            </p>
            <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-300 text-sm ml-2">
              <li>
                <strong>Semantic search is not available</strong> - meaning-based queries won't work
              </li>
              <li>
                <strong>Full-text search is used instead</strong> - only keyword matching is available
              </li>
              <li>Search quality and relevance may be lower than expected</li>
            </ul>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
            <p className="text-sm text-blue-800 dark:text-blue-200 font-medium mb-2">
              To enable semantic search:
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              Go to <strong>Settings</strong> and configure your Gemini and Groq API keys. This will
              enable AI-powered semantic search and contextual responses.
            </p>
          </div>

          <div className="space-y-2 pt-2">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              이 프로덕션 환경은 multilingual-e5 대신 <strong>Gemini 임베딩</strong>을 사용합니다.
              결과적으로 의미 기반 검색이 불가능하며, 키워드 검색만 가능합니다.
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              의미 검색을 활성화하려면 <strong>설정</strong>에서 API 키를 구성하세요.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="bg-gray-50 dark:bg-slate-900/50 px-6 py-4 rounded-b-xl flex gap-3 justify-end border-t border-gray-200 dark:border-slate-700">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
          >
            Close / 닫기
          </button>
        </div>
      </div>
    </div>
  );
}
