'use client';

import { useEffect } from 'react';
import { preloadTranslations } from '@/lib/api';

/**
 * Invisible component that preloads translations data into cache
 * as soon as the app mounts. This ensures translations are ready
 * before any page needs them.
 */
export default function TranslationsPreloader() {
  useEffect(() => {
    preloadTranslations();
  }, []);

  return null;
}
