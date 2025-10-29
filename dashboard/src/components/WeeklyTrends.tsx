import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { cn } from '@/utils/cn';
import type { WeeklyTrend } from '@/types';
import { format } from 'date-fns';

interface WeeklyTrendsProps {
  trends: WeeklyTrend[];
}

export function WeeklyTrends({ trends }: WeeklyTrendsProps) {
  // Prepare chart data
  const chartData = trends.map(trend => ({
    date: format(new Date(trend.date), 'EEE'),
    score: trend.score,
    activities: trend.keyActivities,
    anomalies: trend.anomalies,
  }));

  // Calculate week stats
  const avgScore = trends.reduce((sum, t) => sum + t.score, 0) / trends.length;
  const totalAnomalies = trends.reduce((sum, t) => sum + t.anomalies, 0);
  const normalDays = trends.filter(t => t.status === 'normal').length;
  const trend = trends.length >= 2 ? trends[trends.length - 1].score - trends[0].score : 0;

  const getStatusColor = (status: WeeklyTrend['status']) => {
    switch (status) {
      case 'normal':
        return 'bg-green-500';
      case 'caution':
        return 'bg-yellow-500';
      case 'alert':
        return 'bg-red-500';
    }
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-semibold text-gray-900">{payload[0].payload.date}</p>
          <p className="text-sm text-gray-600">Score: {payload[0].value}</p>
          <p className="text-sm text-gray-600">Activities: {payload[0].payload.activities}</p>
          <p className="text-sm text-gray-600">Anomalies: {payload[0].payload.anomalies}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Weekly Trends</h2>
        <div className="flex items-center gap-2">
          {trend >= 0 ? (
            <TrendingUp className="w-5 h-5 text-green-600" />
          ) : (
            <TrendingDown className="w-5 h-5 text-red-600" />
          )}
          <span className={cn(
            'font-semibold',
            trend >= 0 ? 'text-green-600' : 'text-red-600'
          )}>
            {trend > 0 ? '+' : ''}{trend.toFixed(1)}
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="mb-6">
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              stroke="#9ca3af"
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 12 }}
              stroke="#9ca3af"
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="score"
              stroke="#0ea5e9"
              strokeWidth={3}
              fill="url(#scoreGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Day indicators with color coding */}
      <div className="flex justify-between items-center mb-6 gap-2">
        {trends.map((trend, index) => (
          <div key={index} className="flex-1 text-center">
            <div className="text-xs text-gray-600 mb-1">
              {format(new Date(trend.date), 'EEE')}
            </div>
            <div className="relative">
              <div
                className={cn(
                  'w-full h-2 rounded-full',
                  getStatusColor(trend.status)
                )}
              />
              <div className="text-xs font-semibold text-gray-900 mt-1">
                {trend.score}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t">
        <div className="text-center">
          <div className="text-2xl font-bold text-primary-600">
            {avgScore.toFixed(0)}
          </div>
          <div className="text-xs text-gray-600">Avg Score</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {normalDays}/{trends.length}
          </div>
          <div className="text-xs text-gray-600">Normal Days</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {totalAnomalies}
          </div>
          <div className="text-xs text-gray-600">Anomalies</div>
        </div>
      </div>

      {/* Pattern insights */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <div className="flex items-start gap-2">
          <Activity className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-gray-700">
            {normalDays === trends.length
              ? 'Excellent! All days this week were normal.'
              : `${normalDays} out of ${trends.length} days were within normal range.`}
            {totalAnomalies > 0 && ` ${totalAnomalies} anomalies detected this week.`}
          </p>
        </div>
      </div>
    </div>
  );
}
