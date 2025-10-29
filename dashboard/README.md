# Wellnest Dashboard

A modern React-based dashboard for monitoring and tracking elderly care through the Wellnest system.

## Features

### 1. Household Card
- High-level status overview (normal, caution, alert)
- Today's wellbeing score with visual indicators
- Resident information display
- Real-time status updates

### 2. Live Feed
- Real-time activity stream
- Current location badge with live updates
- Event categorization (motion, door, activity, alerts)
- Scrollable feed with latest 50 events

### 3. Alert Center
- Active and past alerts with badges
- One-click acknowledgment
- Severity-based color coding (critical, high, medium, low)
- Alert type categorization (anomaly, health, safety, routine)

### 4. Routine Timeline
- Daily routine vs baseline comparison
- AI-powered LLM summary of the day
- Activity status tracking (on-time, early, late, missed)
- Deviation metrics and visual indicators

### 5. Weekly Trends
- 7-day score visualization with charts
- Color-coded status indicators
- Pattern analysis and insights
- Anomaly count tracking

### 6. Drill Down Day View
- Detailed day analysis with tabs
- Routine breakdown
- Anomaly list with details
- Similar day patterns with similarity scores

### 7. Semantic Search Bar (Optional)
- Natural language query support
- AI-powered semantic understanding
- Relevance scoring
- Multi-type search results (events, routines, anomalies)

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **Lucide React** - Icon library
- **date-fns** - Date formatting

## Setup

### Prerequisites

- Node.js 18+ and npm
- Wellnest backend API running on port 8000

### Installation

1. Install dependencies:
```bash
cd dashboard
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Start the development server:
```bash
npm run dev
```

The dashboard will be available at [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
npm run build
npm run preview
```

## Project Structure

```
dashboard/
├── src/
│   ├── components/        # React components
│   │   ├── Dashboard.tsx           # Main dashboard
│   │   ├── HouseholdCard.tsx       # Household overview
│   │   ├── LiveFeed.tsx            # Real-time activity feed
│   │   ├── AlertCenter.tsx         # Alert management
│   │   ├── RoutineTimeline.tsx     # Daily routine view
│   │   ├── WeeklyTrends.tsx        # Weekly analytics
│   │   ├── DayDetailView.tsx       # Detailed day view
│   │   └── SemanticSearch.tsx      # Search interface
│   ├── hooks/             # Custom React hooks
│   │   └── useWebSocket.ts         # WebSocket connection
│   ├── services/          # API services
│   │   └── api.ts                  # API client
│   ├── types/             # TypeScript types
│   │   └── index.ts                # Type definitions
│   ├── utils/             # Utility functions
│   │   └── cn.ts                   # Class name utility
│   ├── App.tsx            # Root component
│   ├── main.tsx           # Entry point
│   └── index.css          # Global styles
├── public/                # Static assets
├── index.html             # HTML entry point
├── package.json           # Dependencies
├── tsconfig.json          # TypeScript config
├── vite.config.ts         # Vite config
├── tailwind.config.js     # Tailwind config
└── README.md
```

## API Integration

The dashboard connects to the Wellnest FastAPI backend and expects the following endpoints:

- `GET /api/households` - List all households
- `GET /api/households/{id}` - Get household details
- `GET /api/events` - Get recent events
- `GET /api/alerts` - Get alerts
- `POST /api/alerts/{id}/acknowledge` - Acknowledge alert
- `GET /api/routines` - Get routine data
- `GET /api/trends/weekly` - Get weekly trends
- `GET /api/details/day` - Get day details
- `GET /api/search` - Semantic search
- `WS /ws/alerts/{household_id}` - WebSocket for real-time updates

## Features in Detail

### Real-time Updates
The dashboard uses WebSocket connections to receive real-time updates for:
- New events and activities
- Alert notifications
- Status changes
- Location updates

### Responsive Design
- Mobile-first approach
- Responsive grid layouts
- Touch-friendly interactions
- Adaptive component sizing

### Accessibility
- Semantic HTML
- ARIA labels
- Keyboard navigation
- High contrast colors

## Development

### Running Tests
```bash
npm run test
```

### Linting
```bash
npm run lint
```

### Type Checking
```bash
npm run type-check
```

## Contributing

1. Follow the existing code style
2. Add TypeScript types for all new code
3. Test on multiple screen sizes
4. Ensure accessibility standards

## License

MIT
