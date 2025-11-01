// dashboard/src/services/search.ts

const API_BASE_URL = '/api';

export interface SearchRequest {
  query: string;
  household_id: string;
  limit?: number;
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

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}

export const SearchService = {
  async performSearch(query: string, householdId: string, limit: number = 10): Promise<SearchResponse> {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        household_id: householdId,
        limit,
      }),
    });

    if (!response.ok) {
      throw new Error('Search request failed');
    }

    return response.json();
  },
};