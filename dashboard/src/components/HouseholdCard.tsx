import { Home, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { Household } from '@/types';

interface HouseholdCardProps {
  household: Household;
  onClick?: () => void;
}

export function HouseholdCard({ household, onClick }: HouseholdCardProps) {
  const statusColors = {
    normal: 'bg-success text-success-dark',
    caution: 'bg-warning text-warning-dark',
    alert: 'bg-danger text-danger-dark',
  };

  const statusLabels = {
    normal: 'All Good',
    caution: 'Needs Attention',
    alert: 'Alert',
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-success-dark';
    if (score >= 60) return 'text-warning-dark';
    return 'text-danger-dark';
  };

  const getScoreTrend = (score: number) => {
    // Placeholder logic - in real app, compare with previous day
    if (score >= 80) return <TrendingUp className="w-4 h-4 text-success-dark" />;
    if (score >= 60) return <Activity className="w-4 h-4 text-warning-dark" />;
    return <TrendingDown className="w-4 h-4 text-danger-dark" />;
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        'bg-white rounded-lg shadow-md p-6 cursor-pointer transition-all hover:shadow-lg',
        'border-l-4',
        household.status === 'normal' && 'border-success',
        household.status === 'caution' && 'border-warning',
        household.status === 'alert' && 'border-danger'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="bg-primary-100 p-3 rounded-full">
            <Home className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{household.name}</h3>
            <p className="text-sm text-gray-500">
              {household.residents.length} {household.residents.length === 1 ? 'resident' : 'residents'}
            </p>
          </div>
        </div>
        <span
          className={cn(
            'px-3 py-1 rounded-full text-xs font-semibold',
            statusColors[household.status]
          )}
        >
          {statusLabels[household.status]}
        </span>
      </div>

      {/* Residents */}
      <div className="mb-4">
        <div className="flex items-center gap-2 flex-wrap">
          {household.residents.map((resident) => (
            <div
              key={resident.id}
              className="flex items-center gap-2 bg-gray-50 px-3 py-1 rounded-full"
            >
              {resident.avatar ? (
                <img
                  src={resident.avatar}
                  alt={resident.name}
                  className="w-6 h-6 rounded-full"
                />
              ) : (
                <div className="w-6 h-6 rounded-full bg-primary-200 flex items-center justify-center text-xs font-semibold text-primary-700">
                  {resident.name.charAt(0)}
                </div>
              )}
              <span className="text-sm text-gray-700">{resident.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Today's Score */}
      <div className="border-t pt-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Today's Score</span>
          <div className="flex items-center gap-2">
            {getScoreTrend(household.todayScore)}
            <span className={cn('text-2xl font-bold', getScoreColor(household.todayScore))}>
              {household.todayScore}
            </span>
            <span className="text-sm text-gray-400">/100</span>
          </div>
        </div>
        <div className="mt-2 bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={cn(
              'h-full transition-all duration-500',
              household.todayScore >= 80 && 'bg-success',
              household.todayScore >= 60 && household.todayScore < 80 && 'bg-warning',
              household.todayScore < 60 && 'bg-danger'
            )}
            style={{ width: `${household.todayScore}%` }}
          />
        </div>
      </div>

      {/* Last Update */}
      <div className="mt-3 text-xs text-gray-400">
        Last updated: {new Date(household.lastUpdate).toLocaleTimeString()}
      </div>
    </div>
  );
}
