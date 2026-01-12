'use client';

interface AIResponseProps {
  response: string;
  isLoading?: boolean;
}

export default function AIResponse({ response, isLoading = false }: AIResponseProps) {
  if (isLoading) {
    return (
      <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-6 mb-6">
        <div className="flex items-center gap-3">
          <div className="spinner" />
          <span className="text-gray-600">Generating contextual response...</span>
        </div>
      </div>
    );
  }

  if (!response) return null;

  // Detect if response is primarily Korean
  const isKorean = /[\uac00-\ud7a3]/.test(response) &&
    (response.match(/[\uac00-\ud7a3]/g)?.length || 0) > response.length * 0.3;

  return (
    <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-6 mb-6">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
          <svg
            className="w-5 h-5 text-primary-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
        </div>
        <div className="flex-1">
          <h4 className="text-sm font-medium text-primary-700 mb-2">AI Insight</h4>
          <p className={`text-gray-700 ${isKorean ? 'korean-text' : ''}`}>
            {response}
          </p>
        </div>
      </div>
    </div>
  );
}
