'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';
import APIKeySettings from './APIKeySettings';
import DarkModeToggle from './DarkModeToggle';

interface NavbarProps {
  showBackButton?: boolean;
  backButtonText?: string;
  onBackClick?: () => void;
}

export default function Navbar({ showBackButton = false, backButtonText = 'Back', onBackClick }: NavbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [showSettings, setShowSettings] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleBackClick = () => {
    if (onBackClick) {
      onBackClick();
    } else {
      router.back();
    }
  };

  const isActive = (path: string) => {
    return pathname === path;
  };

  return (
    <nav className="border-b-2 border-text-primary dark:border-text-dark-primary bg-surface dark:bg-surface-dark py-4 transition-colors">
      <div className="max-w-screen-xl mx-auto px-4 sm:px-6">
        <div className="flex justify-between items-center">
          {/* Left side: Back button and Logo */}
          <div className="flex items-center gap-3 sm:gap-6">
            {showBackButton && (
              <button
                onClick={handleBackClick}
                className="font-ui text-sm text-text-secondary dark:text-text-dark-secondary hover:text-text-primary dark:hover:text-text-dark-primary transition-colors"
              >
                ← {backButtonText}
              </button>
            )}

            <Link
              href="/"
              className="font-serif text-xl sm:text-2xl text-text-primary dark:text-text-dark-primary hover:text-accent-scripture dark:hover:text-accent-dark-scripture transition-colors"
            >
              Bible RAG
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            <Link
              href="/"
              className={`font-ui text-sm uppercase tracking-wide pb-1 transition-colors ${
                isActive('/')
                  ? 'text-text-primary dark:text-text-dark-primary border-b-2 border-accent-scripture dark:border-accent-dark-scripture'
                  : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary border-b-2 border-transparent'
              }`}
            >
              Search
            </Link>

            <Link
              href="/browse"
              className={`font-ui text-sm uppercase tracking-wide pb-1 transition-colors ${
                isActive('/browse')
                  ? 'text-text-primary dark:text-text-dark-primary border-b-2 border-accent-scripture dark:border-accent-dark-scripture'
                  : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary border-b-2 border-transparent'
              }`}
            >
              Browse
            </Link>

            <Link
              href="/compare"
              className={`font-ui text-sm uppercase tracking-wide pb-1 transition-colors ${
                isActive('/compare')
                  ? 'text-text-primary dark:text-text-dark-primary border-b-2 border-accent-scripture dark:border-accent-dark-scripture'
                  : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary border-b-2 border-transparent'
              }`}
            >
              Compare
            </Link>

            <Link
              href="/themes"
              className={`font-ui text-sm uppercase tracking-wide pb-1 transition-colors ${
                isActive('/themes')
                  ? 'text-text-primary dark:text-text-dark-primary border-b-2 border-accent-scripture dark:border-accent-dark-scripture'
                  : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary border-b-2 border-transparent'
              }`}
            >
              Themes
            </Link>

            {/* Settings button */}
            <button
              onClick={() => setShowSettings(true)}
              className="w-10 h-10 flex items-center justify-center font-ui text-xs uppercase tracking-wide font-semibold transition-colors border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark"
              aria-label="API Key Settings"
              title="API Key Settings"
            >
              <span className="inline-block scale-150">⚙</span>
            </button>

            {/* Dark Mode Toggle */}
            <DarkModeToggle />
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center gap-3">
            <button
              onClick={() => setShowSettings(true)}
              className="w-10 h-10 flex items-center justify-center font-ui text-xs uppercase tracking-wide font-semibold transition-colors border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark"
              aria-label="API Key Settings"
              title="API Key Settings"
            >
              <span className="inline-block scale-150">⚙</span>
            </button>

            <DarkModeToggle />

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="w-10 h-10 flex items-center justify-center border-2 border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark transition-colors"
              aria-label="Toggle menu"
            >
              <span className="text-lg">{mobileMenuOpen ? '✕' : '☰'}</span>
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden mt-4 pt-4 border-t-2 border-text-tertiary dark:border-text-dark-tertiary">
            <div className="flex flex-col gap-4">
              <Link
                href="/"
                onClick={() => setMobileMenuOpen(false)}
                className={`font-ui text-sm uppercase tracking-wide pb-2 transition-colors ${
                  isActive('/')
                    ? 'text-text-primary dark:text-text-dark-primary border-b-2 border-accent-scripture dark:border-accent-dark-scripture'
                    : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary border-b-2 border-transparent'
                }`}
              >
                Search
              </Link>

              <Link
                href="/browse"
                onClick={() => setMobileMenuOpen(false)}
                className={`font-ui text-sm uppercase tracking-wide pb-2 transition-colors ${
                  isActive('/browse')
                    ? 'text-text-primary dark:text-text-dark-primary border-b-2 border-accent-scripture dark:border-accent-dark-scripture'
                    : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary border-b-2 border-transparent'
                }`}
              >
                Browse
              </Link>

              <Link
                href="/compare"
                onClick={() => setMobileMenuOpen(false)}
                className={`font-ui text-sm uppercase tracking-wide pb-2 transition-colors ${
                  isActive('/compare')
                    ? 'text-text-primary dark:text-text-dark-primary border-b-2 border-accent-scripture dark:border-accent-dark-scripture'
                    : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary border-b-2 border-transparent'
                }`}
              >
                Compare
              </Link>

              <Link
                href="/themes"
                onClick={() => setMobileMenuOpen(false)}
                className={`font-ui text-sm uppercase tracking-wide pb-2 transition-colors ${
                  isActive('/themes')
                    ? 'text-text-primary dark:text-text-dark-primary border-b-2 border-accent-scripture dark:border-accent-dark-scripture'
                    : 'text-text-tertiary dark:text-text-dark-tertiary hover:text-text-primary dark:hover:text-text-dark-primary border-b-2 border-transparent'
                }`}
              >
                Themes
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Settings Modal */}
      <APIKeySettings isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </nav>
  );
}
