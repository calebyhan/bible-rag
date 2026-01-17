import type { Metadata } from 'next';
import { Noto_Sans_KR } from 'next/font/google';
import './globals.css';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import TranslationsPreloader from '@/components/TranslationsPreloader';

const notoSansKR = Noto_Sans_KR({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-noto-sans-kr',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Bible RAG - Multilingual Bible Study',
  description:
    'Semantic search across English and Korean Bible translations with original language insights',
  keywords: ['Bible', 'Study', 'Korean', 'Semantic Search', 'RAG', 'AI'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={notoSansKR.variable}>
      <body className="min-h-screen font-sans antialiased flex flex-col">
        <TranslationsPreloader />
        <Navbar />
        <div className="flex-1">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
