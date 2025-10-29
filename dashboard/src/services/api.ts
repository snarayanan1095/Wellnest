// API service for communicating with the FastAPI backend

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Household endpoints
  async getHouseholds() {
    return this.request('/households');
  }

  async getHousehold(id: string) {
    return this.request(`/households/${id}`);
  }

  // Events endpoints
  async getEvents(householdId: string, limit: number = 50) {
    return this.request(`/events?household_id=${householdId}&limit=${limit}`);
  }

  // Alerts endpoints
  async getAlerts(householdId: string, acknowledged?: boolean) {
    const params = new URLSearchParams({ household_id: householdId });
    if (acknowledged !== undefined) {
      params.append('acknowledged', String(acknowledged));
    }
    return this.request(`/alerts?${params.toString()}`);
  }

  async acknowledgeAlert(alertId: string) {
    return this.request(`/alerts/${alertId}/acknowledge`, {
      method: 'POST',
    });
  }

  // Routine endpoints
  async getRoutine(householdId: string, date?: string) {
    const params = new URLSearchParams({ household_id: householdId });
    if (date) {
      params.append('date', date);
    }
    return this.request(`/routines?${params.toString()}`);
  }

  async getWeeklyTrends(householdId: string) {
    return this.request(`/trends/weekly?household_id=${householdId}`);
  }

  async getDayDetail(householdId: string, date: string) {
    return this.request(`/details/day?household_id=${householdId}&date=${date}`);
  }

  // Search endpoint
  async search(query: string, householdId: string) {
    return this.request(`/search?query=${encodeURIComponent(query)}&household_id=${householdId}`);
  }
}

export const apiService = new ApiService();
