import { useState } from 'react';
import { AlertCircle, CheckCircle, Clock, AlertTriangle, Shield, Activity as ActivityIcon } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { Alert } from '@/types';
import { format } from 'date-fns';

interface AlertCenterProps {
  alerts: Alert[];
  onAcknowledge: (alertId: string) => void;
}

export function AlertCenter({ alerts, onAcknowledge }: AlertCenterProps) {
  const [activeTab, setActiveTab] = useState<'active' | 'past'>('active');

  const activeAlerts = alerts.filter(alert => !alert.acknowledged);
  const pastAlerts = alerts.filter(alert => alert.acknowledged);

  const getSeverityColor = (severity: Alert['severity']) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-300';
    }
  };

  const getSeverityBadge = (severity: Alert['severity']) => {
    const colors = {
      critical: 'bg-red-500',
      high: 'bg-orange-500',
      medium: 'bg-yellow-500',
      low: 'bg-blue-500',
    };

    return (
      <span className={cn('px-2 py-1 rounded text-xs font-semibold text-white', colors[severity])}>
        {severity.toUpperCase()}
      </span>
    );
  };

  const getTypeIcon = (type: Alert['type']) => {
    switch (type) {
      case 'anomaly':
        return <AlertCircle className="w-5 h-5" />;
      case 'health':
        return <ActivityIcon className="w-5 h-5" />;
      case 'safety':
        return <Shield className="w-5 h-5" />;
      case 'routine':
        return <Clock className="w-5 h-5" />;
    }
  };

  const renderAlert = (alert: Alert, isPast: boolean = false) => (
    <div
      key={alert.id}
      className={cn(
        'border rounded-lg p-4 transition-all hover:shadow-md',
        getSeverityColor(alert.severity),
        isPast && 'opacity-60'
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          <div className="flex-shrink-0 mt-1">
            {getTypeIcon(alert.type)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h3 className="font-semibold text-gray-900">{alert.title}</h3>
              {getSeverityBadge(alert.severity)}
            </div>
            <p className="text-sm text-gray-700 mb-2">{alert.description}</p>
            <div className="flex items-center gap-4 text-xs text-gray-600">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {format(new Date(alert.timestamp), 'MMM dd, HH:mm')}
              </span>
              <span className="px-2 py-0.5 bg-white bg-opacity-50 rounded">
                {alert.type}
              </span>
            </div>
            {isPast && alert.acknowledgedAt && (
              <div className="mt-2 text-xs text-gray-600 flex items-center gap-1">
                <CheckCircle className="w-3 h-3 text-green-600" />
                Acknowledged {format(new Date(alert.acknowledgedAt), 'MMM dd, HH:mm')}
                {alert.acknowledgedBy && ` by ${alert.acknowledgedBy}`}
              </div>
            )}
          </div>
        </div>
        {!isPast && (
          <button
            onClick={() => onAcknowledge(alert.id)}
            className="flex-shrink-0 px-4 py-2 bg-white bg-opacity-80 hover:bg-opacity-100 rounded-lg text-sm font-medium transition-all hover:shadow"
          >
            Acknowledge
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Alert Center</h2>
        {activeAlerts.length > 0 && (
          <div className="flex items-center gap-2 bg-red-100 text-red-800 px-3 py-1 rounded-full">
            <AlertTriangle className="w-4 h-4" />
            <span className="font-semibold">{activeAlerts.length}</span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4 border-b">
        <button
          onClick={() => setActiveTab('active')}
          className={cn(
            'px-4 py-2 font-medium transition-colors border-b-2',
            activeTab === 'active'
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          )}
        >
          Active ({activeAlerts.length})
        </button>
        <button
          onClick={() => setActiveTab('past')}
          className={cn(
            'px-4 py-2 font-medium transition-colors border-b-2',
            activeTab === 'past'
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          )}
        >
          Past ({pastAlerts.length})
        </button>
      </div>

      {/* Alert List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {activeTab === 'active' ? (
          activeAlerts.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <CheckCircle className="w-12 h-12 mx-auto mb-2 opacity-50 text-green-500" />
              <p>No active alerts</p>
            </div>
          ) : (
            activeAlerts.map(alert => renderAlert(alert))
          )
        ) : (
          pastAlerts.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <AlertCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No past alerts</p>
            </div>
          ) : (
            pastAlerts.map(alert => renderAlert(alert, true))
          )
        )}
      </div>
    </div>
  );
}
