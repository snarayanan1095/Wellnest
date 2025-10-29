// Core types for the Wellnest dashboard

export interface Household {
  id: string;
  name: string;
  residents: Resident[];
  status: 'normal' | 'caution' | 'alert';
  todayScore: number;
  lastUpdate: Date;
}

export interface Resident {
  id: string;
  name: string;
  age: number;
  avatar?: string;
}

export interface Event {
  id: string;
  household_id: string;
  sensor_type: string;
  location: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export interface Alert {
  id: string;
  household_id: string;
  type: 'anomaly' | 'health' | 'safety' | 'routine';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  timestamp: Date;
  acknowledged: boolean;
  acknowledgedAt?: Date;
  acknowledgedBy?: string;
}

export interface RoutineActivity {
  activity: string;
  expectedTime: string;
  actualTime: string;
  status: 'on-time' | 'early' | 'late' | 'missed';
  deviation: number; // in minutes
}

export interface RoutineTimeline {
  date: Date;
  activities: RoutineActivity[];
  summary: string; // LLM-generated summary
  overallScore: number;
}

export interface WeeklyTrend {
  date: Date;
  score: number;
  status: 'normal' | 'caution' | 'alert';
  keyActivities: number;
  anomalies: number;
}

export interface DayDetail {
  date: Date;
  routine: RoutineActivity[];
  anomalies: Alert[];
  similarDays: {
    date: Date;
    similarity: number;
    pattern: string;
  }[];
  summary: string;
}

export interface LiveFeedItem {
  id: string;
  type: 'motion' | 'door' | 'activity' | 'alert';
  location: string;
  timestamp: Date;
  description: string;
  icon?: string;
}
