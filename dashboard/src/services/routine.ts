// dashboard/src/services/routine.ts

const API_BASE_URL = '/api';

export interface RoutineComparison {
  date: string;
  household_id: string;
  metrics: {
    wake_up_time: TimeMetric;
    bed_time: TimeMetric;
    first_kitchen_time: TimeMetric;
    bathroom_visits: CountMetric;
    total_events: CountMetric;
    activity_duration: DurationMetric;
  };
  baseline_period: {
    days: number;
    start_date: string;
    end_date: string;
  };
  summary_text: string;
}

export interface TimeMetric {
  today: string;
  baseline: string;
  difference_minutes: number;
  difference_formatted: string;
  status: 'normal' | 'warning' | 'alert';
}

export interface CountMetric {
  today: number;
  baseline: number;
  difference: number;
  percentage_change: number;
  status: 'normal' | 'warning' | 'alert';
}

export interface DurationMetric {
  today_minutes: number;
  baseline_minutes: number;
  today_hours: number;
  baseline_hours: number;
  difference_hours: number;
  status: 'normal' | 'warning' | 'alert';
}

export interface RoutineSummary {
  household_id: string;
  date: string;
  summary: string;
  deviations: string[];
  comparison_data?: RoutineComparison;
  fallback?: boolean;
}

export const RoutineService = {
  async getRoutineComparison(householdId: string): Promise<RoutineComparison> {
    const response = await fetch(`${API_BASE_URL}/routine-comparison/${householdId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch routine comparison');
    }
    return response.json();
  },

  async getRoutineSummary(householdId: string): Promise<RoutineSummary> {
    const response = await fetch(`${API_BASE_URL}/routine-summary/${householdId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch routine summary');
    }
    return response.json();
  },

  getStatusColor(status: 'normal' | 'warning' | 'alert'): string {
    switch (status) {
      case 'normal':
        return 'text-green-600';
      case 'warning':
        return 'text-yellow-600';
      case 'alert':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  },

  getStatusBgColor(status: 'normal' | 'warning' | 'alert'): string {
    switch (status) {
      case 'normal':
        return 'bg-green-50';
      case 'warning':
        return 'bg-yellow-50';
      case 'alert':
        return 'bg-red-50';
      default:
        return 'bg-gray-50';
    }
  }
};