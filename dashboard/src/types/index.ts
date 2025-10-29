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

export interface LiveFeedItem {
  id: string;
  type: 'motion' | 'door' | 'activity' | 'alert';
  location: string;
  timestamp: Date;
  description: string;
}
