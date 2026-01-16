'use client';

import { usePathname } from 'next/navigation';
import { useEffect } from 'react';

export default function VerseLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  useEffect(() => {
    // You can add any verse-specific logic here if needed
  }, [pathname]);

  return <>{children}</>;
}
