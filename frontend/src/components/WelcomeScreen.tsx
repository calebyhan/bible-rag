'use client';

interface WelcomeScreenProps {
  onExampleClick: (query: string) => void;
}

const EXAMPLE_QUERIES = [
  'love and forgiveness',
  '사랑에 대한 예수님의 말씀',
  'faith in difficult times',
  '기도에 관한 구절',
];

export default function WelcomeScreen({ onExampleClick }: WelcomeScreenProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4">
      <div className="text-center mb-8 pt-12">
        <h1 className="font-serif text-4xl sm:text-5xl md:text-6xl tracking-tight text-text-primary dark:text-text-dark-primary mb-4">
          Bible RAG
        </h1>
        <p className="font-serif text-lg sm:text-xl text-text-secondary dark:text-text-dark-secondary mb-2">
          Semantic search across English and Korean translations
        </p>
        <p className="font-korean text-base sm:text-lg text-text-tertiary dark:text-text-dark-tertiary">
          다국어 의미 검색
        </p>
      </div>

      <div className="text-center">
        <p className="font-ui text-xs uppercase tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-3">
          Try searching:
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          {EXAMPLE_QUERIES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => onExampleClick(example)}
              className="font-ui text-sm text-text-secondary dark:text-text-dark-secondary hover:text-text-primary dark:hover:text-text-dark-primary transition-colors border-b border-transparent hover:border-text-secondary dark:hover:border-text-dark-secondary px-2 py-1"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
