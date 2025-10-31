// dashboard/src/services/alerts.ts
const API_BASE_URL = '/api';

export interface Alert {
  alert_id: string;
  household_id: string;
  type: string;
  severity: 'high' | 'medium' | 'low';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  created_at: string;
}

export interface AlertCounts {
  high: number;
  medium: number;
  low: number;
  total: number;
}

export class AlertService {
  static async getAlerts(
    householdId: string,
    options: {
      limit?: number;
      severity?: string;
      acknowledged?: boolean;
      hours?: number;
    } = {}
  ): Promise<Alert[]> {
    const params = new URLSearchParams();
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.severity) params.append('severity', options.severity);
    if (options.acknowledged !== undefined) params.append('acknowledged', options.acknowledged.toString());
    if (options.hours) params.append('hours', options.hours.toString());

    const response = await fetch(`${API_BASE_URL}/alerts/${householdId}?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch alerts: ${response.statusText}`);
    }
    return response.json();
  }

  static async getAlertCounts(householdId: string, hours: number = 24): Promise<AlertCounts> {
    const response = await fetch(`${API_BASE_URL}/alerts/${householdId}/count?hours=${hours}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch alert counts: ${response.statusText}`);
    }
    return response.json();
  }

  static async acknowledgeAlert(alertId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/alerts/${alertId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ acknowledged: true }),
    });
    if (!response.ok) {
      throw new Error(`Failed to acknowledge alert: ${response.statusText}`);
    }
  }

  static formatTimeAgo(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffMins > 0) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    return 'Just now';
  }

  static getSeverityColor(severity: 'high' | 'medium' | 'low'): {
    border: string;
    bg: string;
    text: string;
    icon: string;
  } {
    switch (severity) {
      case 'high':
        return {
          border: 'border-red-500',
          bg: 'bg-red-50',
          text: 'text-red-800',
          icon: 'text-red-400',
        };
      case 'medium':
        return {
          border: 'border-yellow-500',
          bg: 'bg-yellow-50',
          text: 'text-yellow-800',
          icon: 'text-yellow-400',
        };
      case 'low':
        return {
          border: 'border-blue-500',
          bg: 'bg-blue-50',
          text: 'text-blue-800',
          icon: 'text-blue-400',
        };
    }
  }
}