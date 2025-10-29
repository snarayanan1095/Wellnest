import { useState } from 'react';
import { Calendar, Clock, AlertTriangle, TrendingUp, X, Sparkles } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { DayDetail } from '@/types';
import { format } from 'date-fns';

interface DayDetailViewProps {
  dayDetail: DayDetail | null;
  onClose: () => void;
}

export function DayDetailView({ dayDetail, onClose }: DayDetailViewProps) {
  const [activeTab, setActiveTab] = useState<'routine' | 'anomalies' | 'similar'>('routine');

  if (!dayDetail) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'on-time':
        return 'text-green-600';
      case 'early':
        return 'text-blue-600';
      case 'late':
        return 'text-orange-600';
      case 'missed':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Day Details</h2>
            <p className="text-sm text-gray-500 flex items-center gap-2 mt-1">
              <Calendar className="w-4 h-4" />
              {format(dayDetail.date, 'EEEE, MMMM dd, yyyy')}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        {/* AI Summary */}
        {dayDetail.summary && (
          <div className="p-6 bg-gradient-to-r from-purple-50 to-blue-50 border-b">
            <div className="flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-semibold text-purple-900 mb-1">AI Summary</div>
                <p className="text-sm text-gray-700">{dayDetail.summary}</p>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 px-6 pt-4 border-b">
          <button
            onClick={() => setActiveTab('routine')}
            className={cn(
              'px-4 py-2 font-medium transition-colors border-b-2',
              activeTab === 'routine'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            Routine ({dayDetail.routine.length})
          </button>
          <button
            onClick={() => setActiveTab('anomalies')}
            className={cn(
              'px-4 py-2 font-medium transition-colors border-b-2',
              activeTab === 'anomalies'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            Anomalies ({dayDetail.anomalies.length})
          </button>
          <button
            onClick={() => setActiveTab('similar')}
            className={cn(
              'px-4 py-2 font-medium transition-colors border-b-2',
              activeTab === 'similar'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            Similar Days ({dayDetail.similarDays.length})
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Routine Tab */}
          {activeTab === 'routine' && (
            <div className="space-y-3">
              {dayDetail.routine.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No routine data available</p>
                </div>
              ) : (
                dayDetail.routine.map((activity, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900">{activity.activity}</h4>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                        <span>Expected: {activity.expectedTime}</span>
                        <span>Actual: {activity.actualTime || 'N/A'}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {activity.deviation !== 0 && (
                        <span className="text-sm text-gray-600">
                          {activity.deviation > 0 ? '+' : ''}{activity.deviation}m
                        </span>
                      )}
                      <span className={cn('font-semibold capitalize', getStatusColor(activity.status))}>
                        {activity.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Anomalies Tab */}
          {activeTab === 'anomalies' && (
            <div className="space-y-3">
              {dayDetail.anomalies.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <AlertTriangle className="w-12 h-12 mx-auto mb-2 opacity-50 text-green-500" />
                  <p>No anomalies detected</p>
                </div>
              ) : (
                dayDetail.anomalies.map((anomaly) => (
                  <div
                    key={anomaly.id}
                    className="p-4 bg-red-50 rounded-lg border border-red-200"
                  >
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900">{anomaly.title}</h4>
                        <p className="text-sm text-gray-700 mt-1">{anomaly.description}</p>
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-600">
                          <span>{format(new Date(anomaly.timestamp), 'HH:mm')}</span>
                          <span className="px-2 py-0.5 bg-red-200 text-red-800 rounded capitalize">
                            {anomaly.severity}
                          </span>
                          <span className="px-2 py-0.5 bg-white rounded capitalize">
                            {anomaly.type}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Similar Days Tab */}
          {activeTab === 'similar' && (
            <div className="space-y-3">
              {dayDetail.similarDays.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <TrendingUp className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No similar days found</p>
                </div>
              ) : (
                dayDetail.similarDays.map((day, index) => (
                  <div
                    key={index}
                    className="p-4 bg-blue-50 rounded-lg border border-blue-200"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold text-gray-900">
                          {format(new Date(day.date), 'EEEE, MMM dd, yyyy')}
                        </h4>
                        <p className="text-sm text-gray-700 mt-1">
                          Pattern: <span className="font-medium">{day.pattern}</span>
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-blue-600">
                          {(day.similarity * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-gray-600">similarity</div>
                      </div>
                    </div>
                    <div className="mt-2 bg-blue-200 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-blue-600 h-full transition-all"
                        style={{ width: `${day.similarity * 100}%` }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
