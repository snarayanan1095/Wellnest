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
import { AlertService, type Alert, type AlertCounts } from './services/alerts';
import RoutineTimeline from './components/RoutineTimeline';

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

  // State for live locations (one per resident) and their last active timestamps
  const [liveLocations, setLiveLocations] = useState<Record<string, string>>({});
  const [lastActiveTimestamps, setLastActiveTimestamps] = useState<Record<string, string>>({});

  // State for alerts
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertCounts, setAlertCounts] = useState<AlertCounts>({ high: 0, medium: 0, low: 0, total: 0 });

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
      // Clear previous locations and timestamps when switching households
      setLiveLocations({});
      setLastActiveTimestamps({});

      // Connect to WebSocket for this household
      websocketService.connect(selectedHouseholdId);

      // Subscribe to events
      const unsubscribe = websocketService.onEvent((event: any) => {
        // Handle initial state message
        if (event.type === 'initial_state' && event.residents) {
          setLiveLocations(event.residents);
          // Also set timestamps if provided
          if (event.timestamps) {
            setLastActiveTimestamps(event.timestamps);
          }
        }
        // Handle regular location updates
        else if (event.resident && event.location) {
          const residentName = String(event.resident);
          setLiveLocations(prev => ({
            ...prev,
            [residentName]: event.location
          }));
          // Update timestamp if provided
          if (event.last_active) {
            setLastActiveTimestamps(prev => ({
              ...prev,
              [residentName]: event.last_active
            }));
          }
        }
        // Handle real-time alerts
        else if (event.alert_id && event.severity) {
          console.log('📨 Received real-time alert:', event);

          // Add the new alert to the beginning of the list
          const newAlert: Alert = {
            alert_id: event.alert_id,
            household_id: event.household_id || selectedHouseholdId,
            type: event.type,
            severity: event.severity,
            title: event.title,
            message: event.message,
            timestamp: event.timestamp,
            acknowledged: false,
            created_at: event.timestamp
          };

          // Keep only the latest alert
          setAlerts([newAlert]); // Keep only the latest alert

          // Update alert counts
          setAlertCounts(prev => ({
            ...prev,
            [event.severity]: prev[event.severity as keyof AlertCounts] + 1,
            total: prev.total + 1
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

      // Fetch alerts for this household - only the latest one
      try {
        const [alertData, alertCountData] = await Promise.all([
          AlertService.getAlerts(householdId, { limit: 1, hours: 24, acknowledged: false }),
          AlertService.getAlertCounts(householdId, 24)
        ]);
        setAlerts(alertData.slice(0, 1)); // Keep only the latest alert
        setAlertCounts(alertCountData);
      } catch (err) {
        console.error('Failed to load alerts:', err);
        // Don't fail the whole load if alerts fail
      }

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

  const formatLastActive = (timestamp: string | undefined): { status: string; detail: string } => {
    if (!timestamp) return { status: 'Unknown', detail: 'No data' };

    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    // Format time as HH:MM AM/PM
    const timeStr = date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });

    if (diffMins < 1) {
      return { status: 'Active now', detail: 'Currently active' };
    }

    if (diffMins < 5) {
      return { status: 'Recently active', detail: `Last seen at ${timeStr}` };
    }

    if (diffMins < 60) {
      return {
        status: `${diffMins} min${diffMins !== 1 ? 's' : ''} ago`,
        detail: `Last seen at ${timeStr}`
      };
    }

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) {
      return {
        status: `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`,
        detail: `Last seen at ${timeStr}`
      };
    }

    const diffDays = Math.floor(diffHours / 24);
    const dateStr = date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });

    return {
      status: `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`,
      detail: `Last seen ${dateStr} at ${timeStr}`
    };
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
                            {currentLocation !== 'Unknown'
                              ? formatLastActive(lastActiveTimestamps[resident.name]).detail
                              : 'Waiting for data...'
                            }
                          </p>
                        </div>
                      </div>
                      {currentLocation !== 'Unknown' && (
                        <div className="flex items-center">
                          {formatLastActive(lastActiveTimestamps[resident.name]).status === 'Active now' ? (
                            <>
                              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                              <span className="text-xs text-green-600">Active</span>
                            </>
                          ) : formatLastActive(lastActiveTimestamps[resident.name]).status === 'Recently active' ? (
                            <>
                              <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>
                              <span className="text-xs text-yellow-600">
                                {formatLastActive(lastActiveTimestamps[resident.name]).status}
                              </span>
                            </>
                          ) : (
                            <>
                              <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                              <span className="text-xs text-gray-400">
                                {formatLastActive(lastActiveTimestamps[resident.name]).status}
                              </span>
                            </>
                          )}
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
              {alertCounts.total > 0 && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  {alertCounts.total} Active
                </span>
              )}
            </div>

            <div className="space-y-3">
              {/* Real alerts from backend - showing only latest */}
              {alerts.length > 0 ? (
                alerts.slice(0, 1).map((alert) => {
                  const colors = AlertService.getSeverityColor(alert.severity);
                  const timeAgo = AlertService.formatTimeAgo(alert.timestamp);

                  return (
                    <div key={alert.alert_id} className={`border-l-4 ${colors.border} ${colors.bg} p-4 rounded-r-lg`}>
                      <div className="flex items-start">
                        <div className="flex-shrink-0">
                          <svg className={`h-5 w-5 ${colors.icon}`} viewBox="0 0 20 20" fill="currentColor">
                            {alert.severity === 'high' ? (
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            ) : alert.severity === 'medium' ? (
                              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            ) : (
                              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                            )}
                          </svg>
                        </div>
                        <div className="ml-3 flex-1">
                          <p className={`text-sm font-medium ${colors.text}`}>
                            {alert.title}
                          </p>
                          <p className={`mt-1 text-xs ${colors.text} opacity-90`}>
                            {alert.message}
                          </p>
                          <p className={`mt-2 text-xs ${colors.text} opacity-75`}>
                            {timeAgo}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : selectedHouseholdId ? (
                <div className="text-center py-8 text-gray-500">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="mt-2 text-sm">No active alerts</p>
                  <p className="text-xs text-gray-400 mt-1">All systems normal</p>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  Select a household to view alerts
                </div>
              )}
            </div>

          </div>
        </div>
      </div>

      {/* Routine Timeline Panel - Below Live Feed and Alert Center */}
      <div className="mt-6">
        <RoutineTimeline householdId={selectedHouseholdId} />
      </div>
    </div>
  );
}

export default App;