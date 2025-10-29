import { useState, useEffect } from 'react';
import { HouseholdCard } from './HouseholdCard';
import { LiveFeed } from './LiveFeed';
import { AlertCenter } from './AlertCenter';
import { RoutineTimeline } from './RoutineTimeline';
import { WeeklyTrends } from './WeeklyTrends';
import { DayDetailView } from './DayDetailView';
import { SemanticSearch } from './SemanticSearch';
import { useWebSocket } from '@/hooks/useWebSocket';
import { apiService } from '@/services/api';
import type { Household, Alert, LiveFeedItem, RoutineTimeline as RoutineTimelineType, WeeklyTrend, DayDetail } from '@/types';
import { Loader2 } from 'lucide-react';

export function Dashboard() {
  const [selectedHouseholdId, setSelectedHouseholdId] = useState<string | null>(null);
  const [households, setHouseholds] = useState<Household[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [liveFeed, setLiveFeed] = useState<LiveFeedItem[]>([]);
  const [routineTimeline, setRoutineTimeline] = useState<RoutineTimelineType | null>(null);
  const [weeklyTrends, setWeeklyTrends] = useState<WeeklyTrend[]>([]);
  const [selectedDayDetail, setSelectedDayDetail] = useState<DayDetail | null>(null);
  const [currentLocation, setCurrentLocation] = useState<string>('');
  const [loading, setLoading] = useState(true);

  // WebSocket connection for real-time updates
  const { messages, isConnected } = useWebSocket(selectedHouseholdId);

  // Load initial data
  useEffect(() => {
    loadHouseholds();
  }, []);

  // Load household-specific data when household is selected
  useEffect(() => {
    if (selectedHouseholdId) {
      loadHouseholdData(selectedHouseholdId);
    }
  }, [selectedHouseholdId]);

  // Handle WebSocket messages
  useEffect(() => {
    messages.forEach((message) => {
      if (message.type === 'event') {
        // Add new event to live feed
        const newFeedItem: LiveFeedItem = {
          id: message.data.id,
          type: message.data.sensor_type || 'activity',
          location: message.data.location,
          timestamp: new Date(message.data.timestamp),
          description: `${message.data.sensor_type} detected`,
        };
        setLiveFeed((prev) => [newFeedItem, ...prev].slice(0, 50));

        // Update current location
        if (message.data.location) {
          setCurrentLocation(message.data.location);
        }
      } else if (message.type === 'alert') {
        // Add new alert
        setAlerts((prev) => [message.data, ...prev]);
      }
    });
  }, [messages]);

  const loadHouseholds = async () => {
    try {
      const data = await apiService.getHouseholds();
      setHouseholds(data);
      if (data.length > 0) {
        setSelectedHouseholdId(data[0].id);
      }
    } catch (error) {
      console.error('Error loading households:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadHouseholdData = async (householdId: string) => {
    try {
      // Load all data in parallel
      const [alertsData, eventsData, routineData, trendsData] = await Promise.all([
        apiService.getAlerts(householdId),
        apiService.getEvents(householdId, 50),
        apiService.getRoutine(householdId),
        apiService.getWeeklyTrends(householdId),
      ]);

      setAlerts(alertsData);

      // Convert events to live feed items
      const feedItems: LiveFeedItem[] = eventsData.map((event: any) => ({
        id: event.id,
        type: event.sensor_type || 'activity',
        location: event.location,
        timestamp: new Date(event.timestamp),
        description: `${event.sensor_type} detected`,
      }));
      setLiveFeed(feedItems);

      // Set current location from most recent event
      if (feedItems.length > 0) {
        setCurrentLocation(feedItems[0].location);
      }

      setRoutineTimeline(routineData);
      setWeeklyTrends(trendsData);
    } catch (error) {
      console.error('Error loading household data:', error);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await apiService.acknowledgeAlert(alertId);
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId
            ? { ...alert, acknowledged: true, acknowledgedAt: new Date() }
            : alert
        )
      );
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const handleDayClick = async (date: Date) => {
    if (!selectedHouseholdId) return;

    try {
      const dateStr = date.toISOString().split('T')[0];
      const dayDetail = await apiService.getDayDetail(selectedHouseholdId, dateStr);
      setSelectedDayDetail(dayDetail);
    } catch (error) {
      console.error('Error loading day detail:', error);
    }
  };

  const handleSearch = async (query: string) => {
    if (!selectedHouseholdId) return [];

    try {
      return await apiService.search(query, selectedHouseholdId);
    } catch (error) {
      console.error('Error searching:', error);
      return [];
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-12 h-12 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Wellnest Dashboard</h1>
              <p className="text-sm text-gray-500 mt-1">
                Monitor and track your loved ones' wellbeing
                {isConnected && (
                  <span className="ml-2 inline-flex items-center gap-1 text-green-600">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    Live
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Household Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {households.map((household) => (
            <HouseholdCard
              key={household.id}
              household={household}
              onClick={() => setSelectedHouseholdId(household.id)}
            />
          ))}
        </div>

        {selectedHouseholdId && (
          <>
            {/* Top Row: Live Feed & Alert Center */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <LiveFeed
                householdId={selectedHouseholdId}
                items={liveFeed}
                currentLocation={currentLocation}
              />
              <AlertCenter alerts={alerts} onAcknowledge={handleAcknowledgeAlert} />
            </div>

            {/* Middle Row: Routine Timeline & Weekly Trends */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {routineTimeline && <RoutineTimeline timeline={routineTimeline} />}
              {weeklyTrends.length > 0 && <WeeklyTrends trends={weeklyTrends} />}
            </div>

            {/* Bottom Row: Semantic Search */}
            <div className="mb-8">
              <SemanticSearch householdId={selectedHouseholdId} onSearch={handleSearch} />
            </div>
          </>
        )}
      </main>

      {/* Day Detail Modal */}
      {selectedDayDetail && (
        <DayDetailView
          dayDetail={selectedDayDetail}
          onClose={() => setSelectedDayDetail(null)}
        />
      )}
    </div>
  );
}
