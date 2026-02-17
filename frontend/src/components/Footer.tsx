export default function Footer() {
  return (
    <footer className="border-t border-border-light dark:border-border-dark-light py-space-lg bg-surface dark:bg-surface-dark transition-colors">
      <div className="max-w-content mx-auto px-6 text-center">
        <p className="font-ui text-xs tracking-wide text-text-tertiary dark:text-text-dark-tertiary mb-2">
          Bible RAG • Multilingual Bible Study Platform
        </p>
        <p className="text-center font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary mt-2">
          Powered by multilingual semantic search and AI insights
        </p>
        <p className="font-ui text-xs text-text-tertiary dark:text-text-dark-tertiary mt-4">
          By Caleb Han •{' '}
          <a
            href="https://github.com/calebyhan/bible-rag"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-text-primary dark:hover:text-text-dark-primary transition-colors"
          >
            View on GitHub
          </a>
        </p>
      </div>
    </footer>
  );
}
