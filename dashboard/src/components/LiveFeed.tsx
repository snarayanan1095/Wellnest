import { useEffect, useState } from 'react';
import { Activity, DoorOpen, MapPin, AlertCircle, Clock } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { LiveFeedItem } from '@/types';
import { format } from 'date-fns';

interface LiveFeedProps {
  householdId: string;
  items: LiveFeedItem[];
  currentLocation?: string;
}

export function LiveFeed({ householdId, items, currentLocation }: LiveFeedProps) {
  const [feedItems, setFeedItems] = useState<LiveFeedItem[]>(items);

  useEffect(() => {
    setFeedItems(items);
  }, [items]);

  const getIcon = (type: LiveFeedItem['type']) => {
    switch (type) {
      case 'motion':
        return <Activity className="w-4 h-4" />;
      case 'door':
        return <DoorOpen className="w-4 h-4" />;
      case 'activity':
        return <Clock className="w-4 h-4" />;
      case 'alert':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const getItemColor = (type: LiveFeedItem['type']) => {
    switch (type) {
      case 'motion':
        return 'bg-blue-50 text-blue-600';
      case 'door':
        return 'bg-purple-50 text-purple-600';
      case 'activity':
        return 'bg-green-50 text-green-600';
      case 'alert':
        return 'bg-red-50 text-red-600';
      default:
        return 'bg-gray-50 text-gray-600';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header with Current Location Badge */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Live Activity Feed</h2>
        {currentLocation && (
          <div className="flex items-center gap-2 bg-primary-500 text-white px-4 py-2 rounded-full shadow-lg animate-pulse">
            <MapPin className="w-5 h-5" />
            <span className="font-semibold">{currentLocation}</span>
          </div>
        )}
      </div>

      {/* Feed Stream */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {feedItems.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No recent activity</p>
          </div>
        ) : (
          feedItems.map((item) => (
            <div
              key={item.id}
              className={cn(
                'flex items-start gap-3 p-3 rounded-lg transition-all hover:shadow-md',
                getItemColor(item.type)
              )}
            >
              <div className="flex-shrink-0 mt-1">
                {getIcon(item.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {item.description}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      <MapPin className="w-3 h-3 inline mr-1" />
                      {item.location}
                    </p>
                  </div>
                  <span className="text-xs text-gray-500 whitespace-nowrap">
                    {format(new Date(item.timestamp), 'HH:mm:ss')}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Activity indicator */}
      <div className="mt-4 pt-4 border-t flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span>Live updates active</span>
        </div>
        <span>{feedItems.length} events today</span>
      </div>
    </div>
  );
}
