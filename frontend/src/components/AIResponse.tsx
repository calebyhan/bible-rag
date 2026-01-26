'use client';

import InfoTooltip from './InfoTooltip';

interface AIResponseProps {
  response: string;
  isLoading?: boolean;
}

export default function AIResponse({ response, isLoading = false }: AIResponseProps) {
  if (isLoading) {
    return (
      <div className="my-space-lg py-space-md border-l-4 border-text-tertiary dark:border-text-dark-tertiary pl-space-md bg-surface dark:bg-surface-dark transition-colors">
        <div className="flex items-center gap-3">
          <div className="spinner" />
          <span className="text-text-secondary dark:text-text-dark-secondary font-body italic">Generating contextual response...</span>
        </div>
      </div>
    );
  }

  if (!response) return null;

  // Detect if response is primarily Korean
  const isKorean = /[\uac00-\ud7a3]/.test(response) &&
    (response.match(/[\uac00-\ud7a3]/g)?.length || 0) > response.length * 0.3;

  return (
    <div className="my-space-lg py-space-md border-l-4 border-text-tertiary dark:border-text-dark-tertiary pl-space-md bg-surface dark:bg-surface-dark transition-colors">
      {/* Header: minimal, typographic */}
      <div className="flex items-center gap-2 mb-space-sm">
        <span className="text-lg text-text-tertiary dark:text-text-dark-tertiary">✦</span>
        <p className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary">
          AI Commentary
        </p>
        <InfoTooltip
          title="AI-Generated Content"
          description="This response is AI-generated and may contain inaccuracies. Always verify important theological or doctrinal information with trusted sources and Scripture."
        />
      </div>

      {/* Response text: serif font for consistency */}
      <p className={`${isKorean ? 'font-korean korean-text' : 'font-body'} text-base leading-relaxed text-text-secondary dark:text-text-dark-secondary`}>
        {response}
      </p>

      {/* Disclaimer: very small, unobtrusive */}
      <p className="font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary mt-space-sm italic">
        AI-generated content. Verify with trusted sources.
      </p>
    </div>
  );
}
