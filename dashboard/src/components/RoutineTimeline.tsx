import { Clock, CheckCircle, AlertCircle, XCircle, Sparkles } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { RoutineTimeline as RoutineTimelineType } from '@/types';
import { format } from 'date-fns';

interface RoutineTimelineProps {
  timeline: RoutineTimelineType;
}

export function RoutineTimeline({ timeline }: RoutineTimelineProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'on-time':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'early':
        return <Clock className="w-5 h-5 text-blue-600" />;
      case 'late':
        return <AlertCircle className="w-5 h-5 text-orange-600" />;
      case 'missed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'on-time':
        return 'bg-green-50 border-green-200';
      case 'early':
        return 'bg-blue-50 border-blue-200';
      case 'late':
        return 'bg-orange-50 border-orange-200';
      case 'missed':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getDeviationText = (deviation: number) => {
    if (deviation === 0) return 'On time';
    const absDeviation = Math.abs(deviation);
    const direction = deviation > 0 ? 'late' : 'early';
    const hours = Math.floor(absDeviation / 60);
    const minutes = absDeviation % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${direction}`;
    }
    return `${minutes}m ${direction}`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Routine Timeline</h2>
          <p className="text-sm text-gray-500">{format(timeline.date, 'EEEE, MMM dd, yyyy')}</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-600">Today's Score</div>
          <div className={cn('text-3xl font-bold', getScoreColor(timeline.overallScore))}>
            {timeline.overallScore}
          </div>
        </div>
      </div>

      {/* LLM Summary */}
      {timeline.summary && (
        <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
          <div className="flex items-start gap-2">
            <Sparkles className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-sm font-semibold text-purple-900 mb-1">AI Insights</div>
              <p className="text-sm text-gray-700">{timeline.summary}</p>
            </div>
          </div>
        </div>
      )}

      {/* Timeline */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {timeline.activities.map((activity, index) => (
          <div
            key={index}
            className={cn(
              'relative flex items-start gap-4 p-4 rounded-lg border transition-all hover:shadow-md',
              getStatusColor(activity.status)
            )}
          >
            {/* Timeline connector */}
            {index < timeline.activities.length - 1 && (
              <div className="absolute left-6 top-14 w-0.5 h-8 bg-gray-300" />
            )}

            {/* Status icon */}
            <div className="flex-shrink-0 z-10 bg-white rounded-full p-1">
              {getStatusIcon(activity.status)}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 mb-1">{activity.activity}</h3>
              <div className="flex flex-wrap items-center gap-3 text-sm">
                <div className="flex items-center gap-1 text-gray-600">
                  <Clock className="w-4 h-4" />
                  <span className="font-medium">Expected:</span>
                  <span>{activity.expectedTime}</span>
                </div>
                <div className="flex items-center gap-1 text-gray-900">
                  <span className="font-medium">Actual:</span>
                  <span>{activity.actualTime || 'Not yet'}</span>
                </div>
              </div>
              {activity.actualTime && activity.deviation !== 0 && (
                <div className="mt-2 inline-flex items-center gap-1 px-2 py-1 bg-white bg-opacity-70 rounded text-xs font-medium">
                  {getDeviationText(activity.deviation)}
                </div>
              )}
            </div>

            {/* Status badge */}
            <div className="flex-shrink-0">
              <span className={cn(
                'px-2 py-1 rounded text-xs font-semibold capitalize',
                activity.status === 'on-time' && 'bg-green-200 text-green-800',
                activity.status === 'early' && 'bg-blue-200 text-blue-800',
                activity.status === 'late' && 'bg-orange-200 text-orange-800',
                activity.status === 'missed' && 'bg-red-200 text-red-800'
              )}>
                {activity.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Summary stats */}
      <div className="mt-6 pt-4 border-t grid grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {timeline.activities.filter(a => a.status === 'on-time').length}
          </div>
          <div className="text-xs text-gray-600">On Time</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">
            {timeline.activities.filter(a => a.status === 'early').length}
          </div>
          <div className="text-xs text-gray-600">Early</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {timeline.activities.filter(a => a.status === 'late').length}
          </div>
          <div className="text-xs text-gray-600">Late</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">
            {timeline.activities.filter(a => a.status === 'missed').length}
          </div>
          <div className="text-xs text-gray-600">Missed</div>
        </div>
      </div>
    </div>
  );
}
