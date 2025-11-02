// dashboard/src/components/SearchBar.tsx
import React, { useState, useRef, useEffect } from 'react';
import {
  SearchService,
  type SearchResponse,
  type SearchResult,
  type AnalysisResult
} from '../services/search';

interface SearchBarProps {
  householdId: string | null;
}

const SearchBar: React.FC<SearchBarProps> = ({ householdId }) => {
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [includeAnalysis, setIncludeAnalysis] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Close results when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    if (!householdId) {
      setError('Please select a household to search within.');
      return;
    }

    setSearching(true);
    setError(null);
    setShowResults(true);

    try {
      // Single unified search call with optional analysis
      const result = await SearchService.performSearch(query, householdId, 10, includeAnalysis);
      setSearchResults(result);
    } catch (err) {
      setError('Failed to perform search. Please try again.');
      console.error('Search error:', err);
    } finally {
      setSearching(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowResults(false);
      setQuery('');
    }
  };

  // Helper component to render a search result card
  const ResultCard: React.FC<{ result: SearchResult }> = ({ result }) => {
    const matchPercentage = Math.round(result.score * 100);

    return (
      <div className="border border-gray-200 rounded-lg p-4 mb-3 hover:shadow-md transition-shadow">
        <div className="flex justify-between items-start mb-2">
          <div className="flex items-center">
            <span className="text-sm font-medium text-gray-900">📅 {result.date}</span>
            <span className="ml-2 px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-700">
              {matchPercentage}% match
            </span>
          </div>
        </div>

        <div className="text-sm text-gray-700 mb-2">
          {result.summary_text}
        </div>

        {result.metadata && (
          <div className="grid grid-cols-2 gap-2 mb-2">
            {result.metadata.wake_up_time && (
              <div className="text-xs text-gray-600">
                ⏰ Wake: {result.metadata.wake_up_time}
              </div>
            )}
            {result.metadata.bed_time && (
              <div className="text-xs text-gray-600">
                🛏️ Bed: {result.metadata.bed_time}
              </div>
            )}
            {result.metadata.bathroom_visits !== undefined && (
              <div className="text-xs text-gray-600">
                🚿 Bathroom: {result.metadata.bathroom_visits}x
              </div>
            )}
            {result.metadata.kitchen_visits !== undefined && (
              <div className="text-xs text-gray-600">
                🍳 Kitchen: {result.metadata.kitchen_visits}x
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // Helper component to render AI analysis
  const AnalysisCard: React.FC<{ analysis: AnalysisResult }> = ({ analysis }) => {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-start mb-3">
          <span className="text-blue-600 mr-2">🤖</span>
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">AI Analysis</h4>
            <p className="text-sm text-gray-700 mb-3">{analysis.summary}</p>

            {analysis.insights && analysis.insights.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-semibold text-gray-600 mb-1">Key Insights:</p>
                <ul className="list-disc list-inside text-xs text-gray-600 space-y-1">
                  {analysis.insights.map((insight, index) => (
                    <li key={index}>{insight}</li>
                  ))}
                </ul>
              </div>
            )}

            {analysis.recommendations && (
              <div className="mt-3 p-2 bg-blue-100 rounded">
                <p className="text-xs font-semibold text-blue-800 mb-1">Recommended Action:</p>
                <p className="text-xs text-blue-700">{analysis.recommendations}</p>
              </div>
            )}

            <div className="mt-2 flex items-center text-xs text-gray-500">
              <span>Analyzed {analysis.analyzed_count} results</span>
              <span className="mx-2">•</span>
              <span>Confidence: {Math.round(analysis.confidence * 100)}%</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div ref={searchRef} className="relative w-full max-w-2xl">
      <form onSubmit={handleSearch} className="relative">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => searchResults && setShowResults(true)}
            placeholder="Ask about routines, alerts, or resident status..."
            className="w-full px-4 py-2 pr-10 text-sm text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={searching}
          />
          <button
            type="submit"
            disabled={searching || !query.trim()}
            className="absolute right-0 top-0 h-full px-3 text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            {searching ? (
              <svg className="w-5 h-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            )}
          </button>
        </div>

        {/* AI Analysis Toggle */}
        <div className="mt-2 flex items-center">
          <input
            type="checkbox"
            id="include-analysis"
            checked={includeAnalysis}
            onChange={(e) => setIncludeAnalysis(e.target.checked)}
            className="mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="include-analysis" className="text-sm text-gray-600">
            Include AI Analysis (adds 2-3 seconds)
          </label>
        </div>
      </form>

      {/* Search Results Dropdown */}
      {showResults && (searchResults || error || searching) && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
          <div className="p-4">
            {searching && (
              <div className="flex items-center text-sm text-gray-500">
                <svg className="w-4 h-4 mr-2 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Searching...
              </div>
            )}

            {error && (
              <div className="text-sm text-red-600">
                {error}
              </div>
            )}

            {/* Display search results */}
            {searchResults && !searching && (
              <div>
                {/* Display AI Analysis if available */}
                {searchResults.analysis && (
                  <AnalysisCard analysis={searchResults.analysis} />
                )}

                {searchResults.results.length > 0 ? (
                  <>
                    <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                      Found {searchResults.results.length} matching results
                    </div>
                    <div>
                      {searchResults.results.map((result, index) => (
                        <ResultCard key={index} result={result} />
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="text-sm text-gray-600">
                    No matching results found for your query.
                  </div>
                )}

                <div className="pt-2 mt-2 border-t border-gray-100">
                  <div className="text-xs text-gray-400">
                    Query: "{searchResults.query}"
                    {householdId && (
                      <span className="ml-2">• Household: {householdId}</span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {searchResults && (
            <div className="px-4 py-2 bg-gray-50 border-t border-gray-100 text-right">
              <button
                onClick={() => {
                  setShowResults(false);
                  setQuery('');
                  setSearchResults(null);
                }}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;