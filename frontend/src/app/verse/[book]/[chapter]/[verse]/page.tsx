'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getVerse, searchVerses, getTranslations } from '@/lib/api';
import { VerseDetailResponse, SearchResult } from '@/types';
import InfoTooltip from '@/components/InfoTooltip';
import OriginalLanguage from '@/components/OriginalLanguage';

export default function VerseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [verseData, setVerseData] = useState<VerseDetailResponse | null>(null);
  const [relatedVerses, setRelatedVerses] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingRelated, setLoadingRelated] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTranslations, setSelectedTranslations] = useState<string[]>(['NIV', 'KRV']);
  const [showOriginal, setShowOriginal] = useState(false);
  const [availableTranslations, setAvailableTranslations] = useState<Array<{abbreviation: string; name: string}>>([]);
  const [translationsLoading, setTranslationsLoading] = useState(true);

  // Translation label mapping for display
  const translationLabels: Record<string, string> = {
    'NIV': 'NIV',
    'ESV': 'ESV',
    'KJV': 'KJV',
    'NKRV': '개역개정',
    'KRV': '개역한글',
    'RKV': '개역성경',
    'RNKSV': '새번역',
    'NASB': 'NASB',
    'NKJV': 'NKJV',
    'NLT': 'NLT',
    'WEB': 'WEB',
    'KCBS': '공동번역',
  };

  const book = decodeURIComponent(params.book as string);
  const chapter = parseInt(params.chapter as string);
  const verse = parseInt(params.verse as string);

  // Fetch available translations on mount
  useEffect(() => {
    const fetchTranslations = async () => {
      try {
        const response = await getTranslations();
        const nonOriginalTranslations = response.translations
          .filter(t => !t.is_original_language)
          .map(t => ({
            abbreviation: t.abbreviation,
            name: t.name,
          }));

        // Remove duplicates based on abbreviation
        const uniqueTranslations = nonOriginalTranslations.filter(
          (trans, index, self) =>
            index === self.findIndex(t => t.abbreviation === trans.abbreviation)
        );

        setAvailableTranslations(uniqueTranslations);
      } catch (error) {
        console.error('Failed to fetch translations:', error);
        // Fallback to common translations
        setAvailableTranslations([
          { abbreviation: 'NIV', name: 'New International Version' },
          { abbreviation: 'ESV', name: 'English Standard Version' },
          { abbreviation: 'KJV', name: 'King James Version' },
          { abbreviation: 'KRV', name: '개역한글' },
          { abbreviation: 'NKRV', name: '개역개정' },
        ]);
      } finally {
        setTranslationsLoading(false);
      }
    };

    fetchTranslations();
  }, []);

  // Fetch main verse data (fast - loads immediately)
  useEffect(() => {
    const fetchVerseData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch verse WITHOUT cross-references (faster initial load)
        const data = await getVerse(book, chapter, verse, selectedTranslations, showOriginal);
        setVerseData(data);
      } catch (err: any) {
        console.error('Error fetching verse:', err);
        setError(err.message || 'Failed to load verse');
      } finally {
        setLoading(false);
      }
    };

    fetchVerseData();
  }, [book, chapter, verse, selectedTranslations, showOriginal]);

  // Fetch related verses after main verse loads (lazy hydration)
  useEffect(() => {
    if (!verseData) return;

    const fetchRelatedVerses = async () => {
      try {
        setLoadingRelated(true);
        const reference = `${book} ${chapter}:${verse}`;
        const searchResults = await searchVerses({
          query: reference,
          languages: ['en', 'ko'],
          translations: selectedTranslations,
          max_results: 5,
        });

        if (searchResults.results) {
          // Filter out the current verse
          const filtered = searchResults.results.filter(
            (r) =>
              !(r.reference.book === book && r.reference.chapter === chapter && r.reference.verse === verse)
          );
          setRelatedVerses(filtered);
        }
      } catch (err: any) {
        console.error('Error fetching related verses:', err);
      } finally {
        setLoadingRelated(false);
      }
    };

    fetchRelatedVerses();
  }, [verseData, book, chapter, verse, selectedTranslations]);

  const handleTranslationToggle = (translation: string) => {
    if (selectedTranslations.includes(translation)) {
      if (selectedTranslations.length > 1) {
        setSelectedTranslations(selectedTranslations.filter((t) => t !== translation));
      }
    } else {
      setSelectedTranslations([...selectedTranslations, translation]);
    }
  };

  const navigateToVerse = (ref: { book: string; chapter: number; verse: number }) => {
    router.push(`/verse/${encodeURIComponent(ref.book)}/${ref.chapter}/${ref.verse}`);
  };

  const handleBack = () => {
    // Use router.back() which Next.js handles properly
    // If there's no previous page, Next.js will keep you on current page
    // We add a home link as alternative
    router.back();
  };

  if (loading) {
    return (
      <div className="flex-1 bg-background dark:bg-background-dark flex items-center justify-center transition-colors">
        <div className="text-center">
          <div className="inline-block w-12 h-12 border-4 border-text-tertiary dark:border-text-dark-tertiary border-t-text-primary dark:border-t-text-dark-primary animate-spin mb-space-md"></div>
          <p className="font-body text-base text-text-primary dark:text-text-dark-primary">Loading verse...</p>
        </div>
      </div>
    );
  }

  if (error || !verseData) {
    return (
      <div className="flex-1 bg-background dark:bg-background-dark flex items-center justify-center transition-colors">
        <div className="text-center max-w-md">
          <h2 className="font-heading text-3xl font-bold text-text-primary dark:text-text-dark-primary mb-space-md">Verse Not Found</h2>
          <p className="font-body text-base text-text-secondary dark:text-text-dark-secondary mb-space-lg">{error || 'The requested verse could not be found.'}</p>
          <button
            onClick={() => router.push('/')}
            className="px-space-md py-space-sm font-ui text-sm uppercase tracking-wide font-semibold border-2 border-text-primary dark:border-text-dark-primary bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark hover:bg-background dark:hover:bg-background-dark hover:text-text-primary dark:hover:text-text-dark-primary transition-all"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  const { reference, translations, original, cross_references, context } = verseData;

  return (
    <div className="bg-background dark:bg-background-dark transition-colors">
      {/* Header */}
      <header className="bg-surface dark:bg-surface-dark border-b-2 border-text-tertiary dark:border-text-dark-tertiary transition-colors">
        <div className="max-w-content mx-auto px-space-md py-space-md sm:px-space-lg lg:px-space-xl">
          <div className="flex items-center gap-space-sm mb-space-sm">
            <button
              onClick={handleBack}
              className="font-ui text-sm uppercase tracking-wide text-text-primary dark:text-text-dark-primary hover:text-text-scripture dark:hover:text-accent-dark-scripture font-semibold pb-1 border-b-2 border-transparent hover:border-text-scripture dark:hover:border-accent-dark-scripture transition-colors inline-flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back
            </button>
          </div>
          <h1 className="font-heading text-2xl sm:text-3xl md:text-4xl font-bold text-text-primary dark:text-text-dark-primary">
            {reference.book} {reference.chapter}:{reference.verse}
          </h1>
          {reference.book_korean && (
            <p className="font-korean text-lg sm:text-xl text-text-secondary dark:text-text-dark-secondary mt-space-xs">
              {reference.book_korean} {reference.chapter}:{reference.verse}
            </p>
          )}
        </div>
      </header>

      <main className="max-w-content mx-auto px-space-md py-space-lg sm:px-space-lg lg:px-space-xl">
        {/* Translation Selector */}
        <div className="mb-space-lg bg-surface dark:bg-surface-dark border-2 border-text-tertiary dark:border-text-dark-tertiary p-space-md transition-colors">
          <div className="flex items-center justify-between mb-space-sm">
            <h3 className="font-ui text-sm uppercase tracking-wide font-semibold text-text-primary dark:text-text-dark-primary">
              Translations ({Object.keys(translations).length} loaded)
            </h3>

            {/* Original Language Toggle */}
            <div className="inline-flex items-center gap-2">
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className={`inline-flex items-center gap-2 px-space-sm py-space-xs font-ui text-sm uppercase tracking-wide font-semibold transition-all border-2 ${
                  showOriginal
                    ? 'border-text-primary dark:border-text-dark-primary bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark'
                    : 'border-text-primary dark:border-text-dark-primary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark'
                }`}
              >
                <span>{showOriginal ? 'Hide' : 'Show'} Original</span>
              </button>
              <InfoTooltip
                title="Original Language"
                description="View the original Greek (NT) or Hebrew (OT) text with transliteration, Strong's concordance numbers, and word-by-word definitions."
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {translationsLoading ? (
              <div className="font-ui text-sm text-text-tertiary dark:text-text-dark-tertiary">Loading translations...</div>
            ) : (
              availableTranslations.map(({ abbreviation, name }) => (
                <button
                  key={abbreviation}
                  onClick={() => handleTranslationToggle(abbreviation)}
                  className={`px-space-sm py-space-xs font-ui text-sm font-semibold transition-all border-2 ${
                    selectedTranslations.includes(abbreviation)
                      ? 'border-text-primary dark:border-text-dark-primary bg-text-primary dark:bg-text-dark-primary text-background dark:text-background-dark'
                      : 'border-text-tertiary dark:border-text-dark-tertiary bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary hover:border-text-primary dark:hover:border-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark'
                  }`}
                >
                  {name}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Verse Translations */}
        <div className="space-y-space-md mb-space-lg">
          {Object.keys(translations).length === 0 && (
            <div className="bg-surface dark:bg-surface-dark border-2 border-text-tertiary dark:border-text-dark-tertiary p-space-lg text-center font-body text-base text-text-tertiary dark:text-text-dark-tertiary transition-colors">
              No translations available for the selected options.
            </div>
          )}
          {Object.entries(translations).map(([lang, text]) => (
            <div key={lang} className="bg-surface dark:bg-surface-dark border-l-4 border-text-scripture dark:border-accent-dark-scripture p-space-lg transition-colors">
              <div className="flex items-center justify-between mb-space-sm border-b border-border-light dark:border-border-dark-light pb-space-xs">
                <span className="font-ui text-xs uppercase tracking-wide font-semibold text-text-primary dark:text-text-dark-primary">
                  {translationLabels[lang] || lang}
                </span>
              </div>
              <p
                className={`text-lg sm:text-xl leading-relaxed text-text-primary dark:text-text-dark-primary ${
                  lang === 'NKRV' || lang === 'KRV' || lang === 'RKV' || lang === 'RNKSV' || lang === 'KCBS' || lang.includes('개역') ? 'font-korean' : 'font-body'
                }`}
              >
                {text}
              </p>
            </div>
          ))}
        </div>

        {/* Original Language */}
        {original && showOriginal && (
          <div className="mb-space-lg">
            <OriginalLanguage
              language={original.language as 'greek' | 'hebrew' | 'aramaic'}
              text={original.words?.map(w => w.word).join(' ') || ''}
              transliteration={original.words?.map(w => w.transliteration).filter(Boolean).join(' ') || ''}
              words={original.words || []}
              strongs={original.words?.map(w => w.strongs).filter(Boolean) as string[] || []}
              showInterlinear={true}
            />
          </div>
        )}

        {/* Context (Previous/Next verses) */}
        {context && (context.previous || context.next) && (
          <div className="bg-surface dark:bg-surface-dark border-2 border-text-tertiary dark:border-text-dark-tertiary p-space-md mb-space-lg transition-colors">
            <h3 className="font-heading text-lg sm:text-xl font-bold text-text-primary dark:text-text-dark-primary mb-space-md flex items-center gap-2">
              Context
              <InfoTooltip
                title="Context"
                description="Shows the verses immediately before and after this verse to help you understand the surrounding narrative and flow of thought."
              />
            </h3>
            <div className="space-y-space-md">
              {context.previous && (
                <div className="border-l-4 border-text-tertiary dark:border-text-dark-tertiary pl-space-md">
                  <button
                    onClick={() => navigateToVerse({
                      book: reference.book,
                      chapter: context.previous!.chapter,
                      verse: context.previous!.verse,
                    })}
                    className="verse-ref mb-space-xs inline-block"
                  >
                    {reference.book} {context.previous.chapter}:{context.previous.verse}
                  </button>
                  <p className="font-body text-base text-text-primary dark:text-text-dark-primary">{context.previous.text}</p>
                </div>
              )}
              {context.next && (
                <div className="border-l-4 border-text-tertiary dark:border-text-dark-tertiary pl-space-md">
                  <button
                    onClick={() => navigateToVerse({
                      book: reference.book,
                      chapter: context.next!.chapter,
                      verse: context.next!.verse,
                    })}
                    className="verse-ref mb-space-xs inline-block"
                  >
                    {reference.book} {context.next.chapter}:{context.next.verse}
                  </button>
                  <p className="font-body text-base text-text-primary dark:text-text-dark-primary">{context.next.text}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Cross References */}
        {cross_references && cross_references.length > 0 && (
          <div className="bg-surface dark:bg-surface-dark border-2 border-text-tertiary dark:border-text-dark-tertiary p-space-md mb-space-lg transition-colors">
            <h3 className="font-heading text-lg sm:text-xl font-bold text-text-primary dark:text-text-dark-primary mb-space-md flex items-center gap-2">
              Cross References ({cross_references.length})
              <InfoTooltip
                title="Cross References"
                description="Biblically-linked verses that have explicit connections such as parallel passages, prophecy fulfillments, direct quotations, or thematic allusions referenced by biblical scholars."
              />
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-space-sm">
              {cross_references.map((ref, idx) => (
                <button
                  key={idx}
                  onClick={() => navigateToVerse({
                    book: ref.book,
                    chapter: ref.chapter,
                    verse: ref.verse,
                  })}
                  className="text-left p-space-sm border-2 border-text-tertiary dark:border-text-dark-tertiary hover:border-text-primary dark:hover:border-text-dark-primary hover:bg-surface dark:hover:bg-surface-dark transition-all"
                >
                  <div className="flex items-center justify-between mb-space-xs">
                    <span className="verse-ref inline-block">
                      {ref.book} {ref.chapter}:{ref.verse}
                    </span>
                    {ref.relationship && (
                      <span className="font-ui text-xs uppercase tracking-wide px-space-xs py-1 bg-surface dark:bg-surface-dark border border-border-light dark:border-border-dark-light text-text-secondary dark:text-text-dark-secondary">
                        {ref.relationship}
                      </span>
                    )}
                  </div>
                  {ref.book_korean && (
                    <p className="font-korean text-xs text-text-secondary dark:text-text-dark-secondary">{ref.book_korean}</p>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Related Verses - Lazy Hydrated */}
        <div className="bg-surface dark:bg-surface-dark border-2 border-text-tertiary dark:border-text-dark-tertiary p-space-md transition-colors">
          <h3 className="font-heading text-lg sm:text-xl font-bold text-text-primary dark:text-text-dark-primary mb-space-md flex items-center gap-2">
            Related Verses {relatedVerses.length > 0 && `(${relatedVerses.length})`}
            <InfoTooltip
              title="Related Verses"
              description="Semantically similar verses discovered through AI-powered meaning analysis. These verses share similar themes, concepts, or messages even if they don't use the same words."
            />
          </h3>
          {loadingRelated ? (
            <div className="text-center py-space-lg">
              <div className="inline-block w-12 h-12 border-4 border-text-tertiary dark:border-text-dark-tertiary border-t-text-primary dark:border-t-text-dark-primary animate-spin mb-space-sm"></div>
              <p className="font-ui text-sm text-text-tertiary dark:text-text-dark-tertiary">Finding related verses...</p>
            </div>
          ) : relatedVerses.length > 0 ? (
            <div className="space-y-space-sm">
              {relatedVerses.map((verse, idx) => (
                <button
                  key={idx}
                  onClick={() => navigateToVerse(verse.reference)}
                  className="w-full text-left p-space-sm border-2 border-text-tertiary dark:border-text-dark-tertiary hover:border-text-primary dark:hover:border-text-dark-primary hover:bg-background dark:hover:bg-background-dark transition-all"
                >
                  <div className="flex items-center justify-between mb-space-xs">
                    <span className="verse-ref inline-block">
                      {verse.reference.book} {verse.reference.chapter}:{verse.reference.verse}
                    </span>
                    <span className="font-ui text-sm text-text-tertiary dark:text-text-dark-tertiary">
                      {Math.round(verse.relevance_score * 100)}% relevant
                    </span>
                  </div>
                  {verse.translations.en && (
                    <p className="font-body text-sm text-text-primary dark:text-text-dark-primary">{verse.translations.en}</p>
                  )}
                </button>
              ))}
            </div>
          ) : (
            <p className="text-center font-body text-base text-text-tertiary dark:text-text-dark-tertiary py-space-md">
              No related verses found.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
