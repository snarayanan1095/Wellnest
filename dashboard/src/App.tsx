import { useState, useEffect } from 'react';
import {
  fetchHouseholds,
  fetchHousehold,
  fetchWeeklyTrends,
  calculateScoreChange,
  type HouseholdListItem,
  type Household
} from './services/api';
import { websocketService } from './services/websocket';

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

  // State for live locations (one per resident)
  const [liveLocations, setLiveLocations] = useState<Record<string, string>>({});

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
      // Set up auto-refresh every 10 minutes
      const interval = setInterval(() => {
        loadHouseholdData(selectedHouseholdId);
      }, 600000); // 10 minutes = 600000 milliseconds

      return () => clearInterval(interval);
    }
  }, [selectedHouseholdId]);

  // Connect to WebSocket when household changes
  useEffect(() => {
    if (selectedHouseholdId) {
      // Clear previous locations when switching households
      setLiveLocations({});

      // Connect to WebSocket for this household
      websocketService.connect(selectedHouseholdId);

      // Subscribe to events
      const unsubscribe = websocketService.onEvent((event: any) => {
        // Handle initial state message
        if (event.type === 'initial_state' && event.residents) {
          setLiveLocations(event.residents);
        }
        // Handle regular location updates
        else if (event.resident && event.location) {
          const residentName = String(event.resident);
          setLiveLocations(prev => ({
            ...prev,
            [residentName]: event.location
          }));
        }
      });

      // Cleanup on unmount or household change
      return () => {
        unsubscribe();
        websocketService.disconnect();
      };
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

  const formatLocation = (location: string): string => {
    // Format location string (capitalize, replace underscores with spaces)
    if (!location || location === 'Unknown') return location;
    return location
      .replace(/_/g, ' ')
      .replace(/\b\w/g, char => char.toUpperCase());
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

        {/* Live Activity Feed and Alert Center */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Live Activity Feed Panel */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Live Activity Feed</h2>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Live
              </span>
            </div>

            <div className="space-y-4">
            {selectedHousehold && selectedHousehold.residents.length > 0 ? (
              <>
                {/* Show current locations for each resident */}
                {selectedHousehold.residents.map((resident) => {
                  const residentKey = resident.name.toLowerCase().replace(' ', '');
                  const currentLocation = liveLocations[residentKey] || liveLocations[resident.name.toLowerCase()] || 'Unknown';

                  return (
                    <div key={resident.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                          <span className="text-blue-700 font-semibold">
                            {resident.name.split(' ').map(n => n[0]).join('')}
                          </span>
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-gray-900">
                            {resident.name} is in {formatLocation(currentLocation)}
                          </p>
                          <p className="text-xs text-gray-500">
                            {currentLocation !== 'Unknown' ? 'Live' : 'Waiting for data...'}
                          </p>
                        </div>
                      </div>
                      {currentLocation !== 'Unknown' && (
                        <div className="flex items-center">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                          <span className="text-xs text-green-600">Active</span>
                        </div>
                      )}
                    </div>
                  );
                })}

                {/* Connection status */}
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">
                      WebSocket: {websocketService.isConnected() ?
                        <span className="text-green-600">Connected</span> :
                        <span className="text-red-600">Disconnected</span>
                      }
                    </span>
                    <span className="text-gray-500">
                      Household: {selectedHouseholdId}
                    </span>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                {selectedHouseholdId ? 'No residents found' : 'Select a household to view live feed'}
              </div>
            )}
            </div>
          </div>

          {/* Alert Center Panel */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Alert Center</h2>
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                3 Active
              </span>
            </div>

            <div className="space-y-3">
              {/* Mock alerts for now - will be replaced with real data */}
              {/* Critical Alert */}
              <div className="border-l-4 border-red-500 bg-red-50 p-4 rounded-r-lg">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-medium text-red-800">
                      Prolonged Inactivity Detected
                    </p>
                    <p className="mt-1 text-xs text-red-700">
                      No motion detected in Bedroom 1 for 4 hours
                    </p>
                    <p className="mt-2 text-xs text-red-600">
                      2 minutes ago • Grandma
                    </p>
                  </div>
                </div>
              </div>

              {/* Warning Alert */}
              <div className="border-l-4 border-yellow-500 bg-yellow-50 p-4 rounded-r-lg">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-medium text-yellow-800">
                      Unusual Pattern Detected
                    </p>
                    <p className="mt-1 text-xs text-yellow-700">
                      Multiple bathroom visits in short period
                    </p>
                    <p className="mt-2 text-xs text-yellow-600">
                      15 minutes ago • Grandpa
                    </p>
                  </div>
                </div>
              </div>

              {/* Info Alert */}
              <div className="border-l-4 border-blue-500 bg-blue-50 p-4 rounded-r-lg">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-medium text-blue-800">
                      Late Wake Up
                    </p>
                    <p className="mt-1 text-xs text-blue-700">
                      First activity detected at 10:30 AM
                    </p>
                    <p className="mt-2 text-xs text-blue-600">
                      1 hour ago • Grandmom
                    </p>
                  </div>
                </div>
              </div>

              {/* No alerts state (hidden when there are alerts) */}
              {false && (
                <div className="text-center py-8 text-gray-500">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="mt-2 text-sm">No active alerts</p>
                  <p className="text-xs text-gray-400 mt-1">All systems normal</p>
                </div>
              )}
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

export default App;