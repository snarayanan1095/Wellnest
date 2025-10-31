import { useState, useEffect } from 'react';
import {
  fetchHouseholds,
  fetchHousehold,
  fetchWeeklyTrends,
  calculateScoreChange,
  type HouseholdListItem,
  type Household
} from './services/api';

function App() {
  // State for household selection
  const [households, setHouseholds] = useState<HouseholdListItem[]>([]);
  const [selectedHouseholdId, setSelectedHouseholdId] = useState<string>('');
  const [selectedHousehold, setSelectedHousehold] = useState<Household | null>(null);

  // State for overview data
  const [activeMembers, setActiveMembers] = useState<number>(0);
  const [totalMembers, setTotalMembers] = useState<number>(0);
  const [status, setStatus] = useState<string>('LOADING');
  const [score, setScore] = useState<number>(0);
  const [scoreChange, setScoreChange] = useState<number>(0);

  // Loading and error states
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all households on mount
  useEffect(() => {
    loadHouseholds();
  }, []);

  // Fetch household details when selection changes
  useEffect(() => {
    if (selectedHouseholdId) {
      loadHouseholdData(selectedHouseholdId);
      // Set up auto-refresh every 30 seconds
      const interval = setInterval(() => {
        loadHouseholdData(selectedHouseholdId);
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [selectedHouseholdId]);

  const loadHouseholds = async () => {
    try {
      const data = await fetchHouseholds();
      setHouseholds(data);
      // Auto-select first household if available
      if (data.length > 0) {
        setSelectedHouseholdId(data[0]._id);
      }
    } catch (err) {
      setError('Failed to load households');
      console.error(err);
    }
  };

  const loadHouseholdData = async (householdId: string) => {
    try {
      setLoading(true);

      // Fetch household details
      const household = await fetchHousehold(householdId);
      setSelectedHousehold(household);

      // Set member counts
      const total = household.residents.length;
      setTotalMembers(total);

      // For now, assume all members are active if status is 'active'
      // In a real app, you'd check recent events per member
      setActiveMembers(household.status === 'active' ? total : 0);

      // Set status from household
      const statusMap: Record<string, string> = {
        'active': 'GOOD',
        'normal': 'GOOD',
        'warning': 'WARNING',
        'critical': 'CRITICAL',
        'inactive': 'INACTIVE'
      };
      setStatus(statusMap[household.status] || household.status.toUpperCase());

      // Fetch weekly trends for score
      try {
        const trends = await fetchWeeklyTrends(householdId);
        if (trends.length > 0) {
          const latestScore = trends[trends.length - 1].score;
          setScore(Math.round(latestScore));
          setScoreChange(calculateScoreChange(trends));
        }
      } catch (err) {
        console.warn('Could not fetch trends, using default score');
        setScore(85);
        setScoreChange(0);
      }

      setError(null);
    } catch (err) {
      setError('Failed to load household data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'GOOD': return 'text-green-600';
      case 'WARNING': return 'text-yellow-600';
      case 'CRITICAL': return 'text-red-600';
      case 'INACTIVE': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Panel - Wellnest Header with Dropdown */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto py-6 px-6">
          <div className="flex items-center justify-between">
            <div className="text-center flex-1">
              <h1 className="text-3xl font-bold text-gray-900">WELLNEST</h1>
              <p className="text-sm text-gray-600 mt-1">Real-time household health & activity tracking</p>
            </div>

            {/* Household Selector */}
            <div className="ml-8">
              <select
                value={selectedHouseholdId}
                onChange={(e) => setSelectedHouseholdId(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="" disabled>Select Household</option>
                {households.map(household => (
                  <option key={household._id} value={household._id}>
                    {household.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Household Overview Panel */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-8">
            Household Overview
            {selectedHousehold && (
              <span className="text-lg font-normal text-gray-600 ml-3">
                - {selectedHousehold.name}
              </span>
            )}
          </h2>

          {loading ? (
            <div className="text-center py-8">
              <div className="text-gray-500">Loading household data...</div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {/* Active Members Card */}
              <div className="bg-gray-50 rounded-lg p-6 border border-gray-100">
                <div className="text-center">
                  <div className="text-gray-600 text-sm font-medium mb-3">Active Members</div>
                  <div className="flex items-baseline justify-center">
                    <span className="text-5xl font-bold text-gray-900">{activeMembers}</span>
                    <span className="ml-2 text-lg text-gray-500">/ {totalMembers}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {activeMembers === totalMembers ? 'All present' : `${totalMembers - activeMembers} inactive`}
                  </div>
                </div>
              </div>

              {/* Status Card */}
              <div className="bg-gray-50 rounded-lg p-6 border border-gray-100">
                <div className="text-center">
                  <div className="text-gray-600 text-sm font-medium mb-3">Status</div>
                  <div className="flex items-center justify-center">
                    <span className={`text-2xl font-bold ${getStatusColor(status)}`}>
                      {status}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {status === 'GOOD' ? 'System operational' : 'Check alerts'}
                  </div>
                </div>
              </div>

              {/* Score Card */}
              <div className="bg-gray-50 rounded-lg p-6 border border-gray-100">
                <div className="text-center">
                  <div className="text-gray-600 text-sm font-medium mb-3">Score</div>
                  <div className="flex items-baseline justify-center">
                    <span className="text-5xl font-bold text-gray-900">{score}</span>
                    {scoreChange !== 0 && (
                      <span className={`ml-2 text-lg ${scoreChange > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {scoreChange > 0 ? '+' : ''}{scoreChange}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {score >= 80 ? 'Excellent' : score >= 60 ? 'Good' : 'Needs attention'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Member Details Panel */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-8">Member Details</h2>

          <div className="overflow-x-auto">
            {selectedHousehold && selectedHousehold.residents.length > 0 ? (
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Member</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Status</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Last Activity</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Health Score</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Location</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {selectedHousehold.residents.map((resident, index) => {
                    const initials = resident.name.split(' ').map(n => n[0]).join('');
                    const colors = ['blue', 'purple', 'green'];
                    const color = colors[index % colors.length];

                    return (
                      <tr key={resident.id} className="hover:bg-gray-50">
                        <td className="px-4 py-5">
                          <div className="flex items-center">
                            <div className={`h-10 w-10 bg-${color}-100 rounded-full flex items-center justify-center`}>
                              <span className={`text-${color}-700 font-semibold`}>{initials}</span>
                            </div>
                            <div className="ml-3">
                              <p className="text-sm font-medium text-gray-900">{resident.name}</p>
                              <p className="text-xs text-gray-500">Age: {resident.age}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-5 text-center">
                          <span className="inline-flex px-2.5 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-800">
                            Active
                          </span>
                        </td>
                        <td className="px-4 py-5 text-center text-sm text-gray-600">
                          {index === 0 ? '2 mins ago' : index === 1 ? '15 mins ago' : '1 hour ago'}
                        </td>
                        <td className="px-4 py-5 text-center">
                          <p className="text-sm font-medium text-gray-900">{88 - index * 3}/100</p>
                          <p className="text-xs text-gray-500">Good</p>
                        </td>
                        <td className="px-4 py-5 text-center text-sm text-gray-600">
                          {index === 0 ? 'Living Room' : index === 1 ? 'Kitchen' : 'Bedroom'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-8 text-gray-500">
                {selectedHouseholdId ? 'No residents found' : 'Select a household to view members'}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;