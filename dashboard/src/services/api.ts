// API Service for Dashboard

const API_BASE_URL = '/api';

export interface Resident {
  id: string;
  name: string;
  age: number;
}

export interface Household {
  _id: string;
  name: string;
  residents: Resident[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface HouseholdListItem {
  _id: string;
  name: string;
  residents: Resident[];
  status: string;
  last_update: string;
}

export interface WeeklyTrend {
  date: string;
  score: number;
  status: string;
  key_activities: number;
  anomalies: number;
}

// Fetch all households
export async function fetchHouseholds(): Promise<HouseholdListItem[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/households`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching households:', error);
    throw error;
  }
}

// Fetch specific household details
export async function fetchHousehold(householdId: string): Promise<Household> {
  try {
    const response = await fetch(`${API_BASE_URL}/households/${householdId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error fetching household ${householdId}:`, error);
    throw error;
  }
}

// Fetch weekly trends for score
export async function fetchWeeklyTrends(householdId: string): Promise<WeeklyTrend[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/trends/weekly?household_id=${householdId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching weekly trends:', error);
    throw error;
  }
}

// Calculate score change from weekly trends
export function calculateScoreChange(trends: WeeklyTrend[]): number {
  if (trends.length < 2) return 0;
  const today = trends[trends.length - 1].score;
  const yesterday = trends[trends.length - 2].score;
  return Math.round(today - yesterday);
}