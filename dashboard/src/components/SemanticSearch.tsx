import { useState } from 'react';
import { Search, Loader2, Calendar, MapPin, Activity } from 'lucide-react';
import { cn } from '@/utils/cn';
import { format } from 'date-fns';

interface SearchResult {
  id: string;
  type: 'event' | 'routine' | 'anomaly';
  title: string;
  description: string;
  timestamp: Date;
  location?: string;
  relevance: number;
}

interface SemanticSearchProps {
  householdId: string;
  onSearch: (query: string) => Promise<SearchResult[]>;
}

export function SemanticSearch({ householdId, onSearch }: SemanticSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const searchResults = await onSearch(query);
      setResults(searchResults);
      setShowResults(true);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const getTypeIcon = (type: SearchResult['type']) => {
    switch (type) {
      case 'event':
        return <Activity className="w-4 h-4" />;
      case 'routine':
        return <Calendar className="w-4 h-4" />;
      case 'anomaly':
        return <MapPin className="w-4 h-4" />;
    }
  };

  const getTypeColor = (type: SearchResult['type']) => {
    switch (type) {
      case 'event':
        return 'bg-blue-100 text-blue-700';
      case 'routine':
        return 'bg-green-100 text-green-700';
      case 'anomaly':
        return 'bg-red-100 text-red-700';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Semantic Search</h2>

      {/* Search Input */}
      <div className="relative">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about activities, patterns, or events... (e.g., 'When did mom last leave the house?')"
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isSearching || !query.trim()}
            className={cn(
              'px-6 py-3 bg-primary-600 text-white rounded-lg font-medium transition-all',
              'hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed',
              'flex items-center gap-2'
            )}
          >
            {isSearching ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Searching...
              </>
            ) : (
              'Search'
            )}
          </button>
        </div>

        {/* Example queries */}
        <div className="mt-2 flex flex-wrap gap-2">
          <span className="text-xs text-gray-500">Try:</span>
          {[
            'unusual activity last week',
            'morning routine patterns',
            'bathroom visits at night',
          ].map((example) => (
            <button
              key={example}
              onClick={() => setQuery(example)}
              className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {showResults && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">
              Results ({results.length})
            </h3>
            <button
              onClick={() => setShowResults(false)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Clear
            </button>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {results.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Search className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No results found</p>
                <p className="text-sm mt-1">Try a different query</p>
              </div>
            ) : (
              results.map((result) => (
                <div
                  key={result.id}
                  className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                >
                  <div className="flex items-start gap-3">
                    <div className={cn('p-2 rounded-lg', getTypeColor(result.type))}>
                      {getTypeIcon(result.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <h4 className="font-semibold text-gray-900">{result.title}</h4>
                        <div className="flex items-center gap-1 text-xs text-gray-500">
                          <div
                            className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden"
                            title={`${(result.relevance * 100).toFixed(0)}% relevant`}
                          >
                            <div
                              className="h-full bg-primary-500"
                              style={{ width: `${result.relevance * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{result.description}</p>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {format(new Date(result.timestamp), 'MMM dd, HH:mm')}
                        </span>
                        {result.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {result.location}
                          </span>
                        )}
                        <span className={cn('px-2 py-0.5 rounded capitalize', getTypeColor(result.type))}>
                          {result.type}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Info banner */}
      <div className="mt-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
        <p className="text-xs text-gray-700">
          <span className="font-semibold text-purple-900">AI-powered search:</span> Ask natural questions about activities,
          patterns, and events. The system uses semantic understanding to find relevant information.
        </p>
      </div>
    </div>
  );
}
