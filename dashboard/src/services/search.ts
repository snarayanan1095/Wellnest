// dashboard/src/services/search.ts

const API_BASE_URL = '/api';

export interface SearchRequest {
  query: string;
  household_id: string;
  limit?: number;
  include_analysis?: boolean;
}

export interface SearchResult {
  date: string;
  score: number;
  summary_text: string;
  metadata?: {
    wake_up_time?: string;
    bed_time?: string;
    bathroom_visits?: number;
    kitchen_visits?: number;
    living_room_time?: number;
    bedroom_time?: number;
  };
}

export interface AnalysisResult {
  summary: string;
  insights: string[];
  recommendations?: string;
  confidence: number;
  analyzed_count: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  analysis?: AnalysisResult;
}

export const SearchService = {
  async performSearch(
    query: string,
    householdId: string,
    limit: number = 10,
    includeAnalysis: boolean = false
  ): Promise<SearchResponse> {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        household_id: householdId,
        limit,
        include_analysis: includeAnalysis,
      }),
    });

    if (!response.ok) {
      throw new Error('Search request failed');
    }

    return response.json();
  },
};