'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getBooks } from '@/lib/api';
import { Book } from '@/types';

export default function BrowsePage() {
  const router = useRouter();
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTestament, setSelectedTestament] = useState<'all' | 'OT' | 'NT'>('all');
  const [selectedGenre, setSelectedGenre] = useState<string>('all');

  useEffect(() => {
    const fetchBooks = async () => {
      try {
        setLoading(true);
        const testament = selectedTestament === 'all' ? undefined : selectedTestament;
        const genre = selectedGenre === 'all' ? undefined : selectedGenre;
        const data = await getBooks(testament, genre);
        setBooks(data);
      } catch (err: any) {
        console.error('Error fetching books:', err);
        setError(err.message || 'Failed to load books');
      } finally {
        setLoading(false);
      }
    };

    fetchBooks();
  }, [selectedTestament, selectedGenre]);

  const genres = [
    'law',
    'history',
    'poetry',
    'wisdom',
    'prophecy',
    'gospel',
    'epistle',
  ];

  const otBooks = books.filter((b) => b.testament === 'OT');
  const ntBooks = books.filter((b) => b.testament === 'NT');

  const handleBookClick = (book: Book, chapter: number = 1) => {
    // Navigate to the first verse of the chapter
    router.push(`/verse/${book.name}/${chapter}/1`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Loading books...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <button
            onClick={() => router.push('/')}
            className="text-primary-600 hover:text-primary-700 font-medium mb-2 inline-flex items-center"
          >
            ← Back to Search
          </button>
          <h1 className="text-4xl font-bold text-gray-900">Browse Bible</h1>
          <p className="text-lg text-gray-600 mt-2">성경 둘러보기</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Testament Filter */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Testament</h3>
              <div className="flex gap-2">
                {['all', 'OT', 'NT'].map((testament) => (
                  <button
                    key={testament}
                    onClick={() => setSelectedTestament(testament as any)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedTestament === testament
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {testament === 'all' ? 'All' : testament === 'OT' ? 'Old Testament' : 'New Testament'}
                  </button>
                ))}
              </div>
            </div>

            {/* Genre Filter */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Genre</h3>
              <select
                value={selectedGenre}
                onChange={(e) => setSelectedGenre(e.target.value)}
                className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="all">All Genres</option>
                {genres.map((genre) => (
                  <option key={genre} value={genre}>
                    {genre.charAt(0).toUpperCase() + genre.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Stats */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              Showing <span className="font-semibold">{books.length}</span> books
              {selectedTestament !== 'all' && (
                <span>
                  {' '}
                  in <span className="font-semibold">{selectedTestament === 'OT' ? 'Old Testament' : 'New Testament'}</span>
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Books Grid */}
        {(selectedTestament === 'all' || selectedTestament === 'OT') && otBooks.length > 0 && (
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              <span className="mr-3">📜</span>
              Old Testament
              <span className="ml-3 text-sm font-normal text-gray-500">({otBooks.length} books)</span>
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {otBooks.map((book) => (
                <div
                  key={book.id}
                  className="verse-card p-5 hover:shadow-lg transition-shadow cursor-pointer group"
                  onClick={() => handleBookClick(book)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-bold text-gray-900 group-hover:text-primary-600 transition-colors">
                      {book.name}
                    </h3>
                    {book.genre && (
                      <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                        {book.genre}
                      </span>
                    )}
                  </div>
                  {book.name_korean && (
                    <p className="text-sm text-gray-600 korean-text mb-3">{book.name_korean}</p>
                  )}
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>{book.total_chapters} chapters</span>
                    <span className="text-xs text-gray-400">#{book.book_number}</span>
                  </div>
                  {/* Chapter quick links */}
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs text-gray-500 mb-2">Quick access:</p>
                    <div className="flex flex-wrap gap-1">
                      {[...Array(Math.min(5, book.total_chapters))].map((_, idx) => (
                        <button
                          key={idx}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleBookClick(book, idx + 1);
                          }}
                          className="px-2 py-1 text-xs bg-gray-100 hover:bg-primary-100 hover:text-primary-700 rounded transition-colors"
                        >
                          Ch {idx + 1}
                        </button>
                      ))}
                      {book.total_chapters > 5 && (
                        <span className="px-2 py-1 text-xs text-gray-400">...</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {(selectedTestament === 'all' || selectedTestament === 'NT') && ntBooks.length > 0 && (
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              <span className="mr-3">✝️</span>
              New Testament
              <span className="ml-3 text-sm font-normal text-gray-500">({ntBooks.length} books)</span>
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {ntBooks.map((book) => (
                <div
                  key={book.id}
                  className="verse-card p-5 hover:shadow-lg transition-shadow cursor-pointer group"
                  onClick={() => handleBookClick(book)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-bold text-gray-900 group-hover:text-primary-600 transition-colors">
                      {book.name}
                    </h3>
                    {book.genre && (
                      <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                        {book.genre}
                      </span>
                    )}
                  </div>
                  {book.name_korean && (
                    <p className="text-sm text-gray-600 korean-text mb-3">{book.name_korean}</p>
                  )}
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>{book.total_chapters} chapters</span>
                    <span className="text-xs text-gray-400">#{book.book_number}</span>
                  </div>
                  {/* Chapter quick links */}
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs text-gray-500 mb-2">Quick access:</p>
                    <div className="flex flex-wrap gap-1">
                      {[...Array(Math.min(5, book.total_chapters))].map((_, idx) => (
                        <button
                          key={idx}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleBookClick(book, idx + 1);
                          }}
                          className="px-2 py-1 text-xs bg-gray-100 hover:bg-primary-100 hover:text-primary-700 rounded transition-colors"
                        >
                          Ch {idx + 1}
                        </button>
                      ))}
                      {book.total_chapters > 5 && (
                        <span className="px-2 py-1 text-xs text-gray-400">...</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {books.length === 0 && !loading && (
          <div className="text-center py-12">
            <p className="text-gray-600 text-lg">No books found matching your filters.</p>
          </div>
        )}
      </main>
    </div>
  );
}
