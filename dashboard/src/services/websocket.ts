/**
 * WebSocket service for real-time event streaming
 */

export interface LocationEvent {
  household_id: string;
  sensor_id: string;
  sensor_type: string;
  location: string;
  resident?: string;
  value: string;
  timestamp: string;
}

type EventCallback = (event: LocationEvent) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private householdId: string | null = null;
  private eventCallbacks: Set<EventCallback> = new Set();
  private reconnectTimeout: number | null = null;
  private isConnecting = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000; // 3 seconds

  /**
   * Connect to WebSocket for specific household
   */
  connect(householdId: string) {
    // If already connected to same household, do nothing
    if (this.ws && this.householdId === householdId &&
        this.ws.readyState === WebSocket.OPEN) {
      console.log(`Already connected to household ${householdId}`);
      return;
    }

    // If connected to different household, disconnect first
    if (this.ws && this.householdId !== householdId) {
      this.disconnect();
    }

    if (this.isConnecting) {
      console.log('Connection already in progress...');
      return;
    }

    this.householdId = householdId;
    this.isConnecting = true;
    this.reconnectAttempts = 0;

    // Determine WebSocket URL based on environment
    let wsUrl: string;
    if (window.location.port === '3000') {
      // Production/Docker - use relative URL through nginx
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${protocol}//${window.location.host}/api/ws/events/${householdId}`;
    } else {
      // Development - connect directly to backend
      wsUrl = `ws://localhost:8000/api/ws/events/${householdId}`;
    }
    console.log(`Connecting to WebSocket: ${wsUrl}`);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`✓ WebSocket connected for household ${householdId}`);
        this.isConnecting = false;
        this.reconnectAttempts = 0;

        // Send heartbeat every 30 seconds to keep connection alive
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Notify all registered callbacks
          this.eventCallbacks.forEach(callback => {
            try {
              callback(data);
            } catch (err) {
              console.error('Error in event callback:', err);
            }
          });
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
      };

      this.ws.onclose = (event) => {
        console.log(`WebSocket closed for household ${householdId}`, event.code, event.reason);
        this.isConnecting = false;
        this.stopHeartbeat();

        // Auto-reconnect if not manually disconnected
        if (this.householdId === householdId && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

          this.reconnectTimeout = window.setTimeout(() => {
            if (this.householdId === householdId) {
              this.connect(householdId);
            }
          }, this.reconnectDelay);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.isConnecting = false;
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    this.householdId = null;
    this.stopHeartbeat();

    if (this.reconnectTimeout) {
      window.clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      // Close connection
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close();
      }
      this.ws = null;
    }

    console.log('WebSocket disconnected');
  }

  /**
   * Register callback for events
   */
  onEvent(callback: EventCallback) {
    this.eventCallbacks.add(callback);

    // Return unsubscribe function
    return () => {
      this.eventCallbacks.delete(callback);
    };
  }

  /**
   * Send heartbeat to keep connection alive
   */
  private heartbeatInterval: number | null = null;

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000); // Every 30 seconds
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      window.clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();