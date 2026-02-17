import type { Metadata } from 'next';
import { Crimson_Pro, Crimson_Text, Noto_Serif_KR } from 'next/font/google';
import './globals.css';
import Navbar from '@/components/Navbar';
import TranslationsPreloader from '@/components/TranslationsPreloader';
import Footer from '@/components/Footer';

const crimsonPro = Crimson_Pro({
  subsets: ['latin'],
  weight: ['400', '600', '700'],
  variable: '--font-crimson-pro',
  display: 'swap',
});

const crimsonText = Crimson_Text({
  subsets: ['latin'],
  weight: ['400', '600', '700'],
  variable: '--font-crimson-text',
  display: 'swap',
});

const notoSerifKR = Noto_Serif_KR({
  subsets: ['latin'],
  weight: ['400', '600', '700'],
  variable: '--font-noto-serif-kr',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Bible RAG - Multilingual Bible Study',
  description:
    'Semantic search across English and Korean Bible translations with original language insights',
  keywords: ['Bible', 'Study', 'Korean', 'Semantic Search', 'RAG', 'AI'],
  icons: {
    icon: '/icon',
    apple: '/apple-icon',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${crimsonPro.variable} ${crimsonText.variable} ${notoSerifKR.variable}`}>
      <body className="min-h-screen font-body antialiased flex flex-col bg-background dark:bg-background-dark text-text-primary dark:text-text-dark-primary transition-colors">
        <TranslationsPreloader />
        <Navbar />
        <div className="flex-1 flex flex-col">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
