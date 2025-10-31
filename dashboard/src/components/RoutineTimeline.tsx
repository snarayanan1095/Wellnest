// dashboard/src/components/RoutineTimeline.tsx
import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { RoutineService, RoutineComparison, RoutineSummary } from '../services/routine';

interface RoutineTimelineProps {
  householdId: string | null;
}

const RoutineTimeline: React.FC<RoutineTimelineProps> = ({ householdId }) => {
  const [comparison, setComparison] = useState<RoutineComparison | null>(null);
  const [summary, setSummary] = useState<RoutineSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (householdId) {
      loadRoutineData();
      // Refresh every 5 minutes
      const interval = setInterval(loadRoutineData, 5 * 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [householdId]);

  const loadRoutineData = async () => {
    if (!householdId) return;

    setLoading(true);
    setError(null);

    try {
      const [comparisonData, summaryData] = await Promise.all([
        RoutineService.getRoutineComparison(householdId),
        RoutineService.getRoutineSummary(householdId)
      ]);

      setComparison(comparisonData);
      setSummary(summaryData);
    } catch (err) {
      setError('Failed to load routine data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Convert time string to decimal hours for visualization
  const timeToDecimal = (timeStr: string): number => {
    if (!timeStr || timeStr === 'N/A') return 0;
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours + minutes / 60;
  };

  // Prepare data for bar chart
  const prepareChartData = () => {
    if (!comparison) return [];

    const metrics = comparison.metrics;

    return [
      {
        metric: 'Wake Time',
        Today: timeToDecimal(metrics.wake_up_time.today),
        Baseline: timeToDecimal(metrics.wake_up_time.baseline),
        status: metrics.wake_up_time.status
      },
      {
        metric: 'First Kitchen',
        Today: timeToDecimal(metrics.first_kitchen_time.today),
        Baseline: timeToDecimal(metrics.first_kitchen_time.baseline),
        status: metrics.first_kitchen_time.status
      },
      {
        metric: 'Active Hours',
        Today: metrics.activity_duration.today_hours,
        Baseline: metrics.activity_duration.baseline_hours,
        status: metrics.activity_duration.status
      },
      {
        metric: 'Bed Time',
        Today: timeToDecimal(metrics.bed_time.today),
        Baseline: timeToDecimal(metrics.bed_time.baseline),
        status: metrics.bed_time.status
      }
    ];
  };

  const countChartData = () => {
    if (!comparison) return [];

    const metrics = comparison.metrics;

    return [
      {
        metric: 'Bathroom Visits',
        Today: metrics.bathroom_visits.today,
        Baseline: metrics.bathroom_visits.baseline,
        status: metrics.bathroom_visits.status,
        change: metrics.bathroom_visits.percentage_change
      },
      {
        metric: 'Total Events',
        Today: metrics.total_events.today,
        Baseline: metrics.total_events.baseline,
        status: metrics.total_events.status,
        change: metrics.total_events.percentage_change
      }
    ];
  };

  const formatTimeFromDecimal = (value: number): string => {
    const hours = Math.floor(value);
    const minutes = Math.round((value - hours) * 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const isTimeMetric = ['Wake Time', 'First Kitchen', 'Bed Time'].includes(label);

      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {isTimeMetric ? formatTimeFromDecimal(entry.value) :
                            label === 'Active Hours' ? `${entry.value.toFixed(1)}h` :
                            entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (!householdId) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8 text-gray-500">
          Select a household to view routine timeline
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !comparison) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8 text-red-500">
          {error || 'No routine data available'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Routine Timeline Panel */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Routine Timeline</h2>
          <span className="text-sm text-gray-500">
            Today vs {comparison.baseline_period.days}-day baseline
          </span>
        </div>

        {/* Time-based metrics chart */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Daily Schedule</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={prepareChartData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" />
              <YAxis
                tickFormatter={(value) => formatTimeFromDecimal(value)}
                domain={[0, 24]}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="Today" fill="#3B82F6" />
              <Bar dataKey="Baseline" fill="#9CA3AF" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Count-based metrics */}
        <div className="grid grid-cols-2 gap-4 mt-6">
          {countChartData().map((item) => (
            <div key={item.metric} className={`p-4 rounded-lg ${RoutineService.getStatusBgColor(item.status)}`}>
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-gray-700">{item.metric}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{item.Today}</p>
                  <p className="text-xs text-gray-500 mt-1">Baseline: {item.Baseline}</p>
                </div>
                <div className="text-right">
                  <span className={`text-sm font-medium ${item.change > 0 ? 'text-green-600' : item.change < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                    {item.change > 0 ? '+' : ''}{item.change.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Key deviations */}
        {comparison.metrics && (
          <div className="mt-6 space-y-2">
            {Math.abs(comparison.metrics.wake_up_time.difference_minutes) > 30 && (
              <div className="flex items-center text-sm">
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  comparison.metrics.wake_up_time.status === 'alert' ? 'bg-red-500' : 'bg-yellow-500'
                }`}></div>
                <span className="text-gray-700">
                  Wake time: {comparison.metrics.wake_up_time.difference_formatted} from baseline
                </span>
              </div>
            )}
            {Math.abs(comparison.metrics.bathroom_visits.percentage_change) > 25 && (
              <div className="flex items-center text-sm">
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  comparison.metrics.bathroom_visits.status === 'alert' ? 'bg-red-500' : 'bg-yellow-500'
                }`}></div>
                <span className="text-gray-700">
                  Bathroom visits: {comparison.metrics.bathroom_visits.percentage_change > 0 ? '+' : ''}{comparison.metrics.bathroom_visits.percentage_change.toFixed(0)}% from baseline
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* AI Analysis Panel */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">AI Analysis</h2>
          {summary?.fallback && (
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">Rule-based</span>
          )}
        </div>

        {summary ? (
          <div className="space-y-4">
            <div className="text-gray-700 leading-relaxed">
              {summary.summary}
            </div>

            {summary.deviations && summary.deviations.length > 0 && (
              <div className="border-t pt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Key Observations:</h3>
                <ul className="space-y-1">
                  {summary.deviations.map((deviation, index) => (
                    <li key={index} className="flex items-start text-sm text-gray-600">
                      <span className="text-gray-400 mr-2">•</span>
                      {deviation}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="text-gray-500 text-sm">
            Loading AI analysis...
          </div>
        )}
      </div>
    </div>
  );
};

export default RoutineTimeline;