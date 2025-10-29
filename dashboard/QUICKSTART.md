# Wellnest Dashboard - Quick Start Guide

## Getting Started in 3 Steps

### 1. Install Dependencies
```bash
cd dashboard
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env
```

The default configuration connects to `http://localhost:8000` for the API.

### 3. Start Development Server
```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to view the dashboard.

## What You Get

### ✅ All Features Implemented

1. **Household Card** - Overview with status and daily score
2. **Live Feed** - Real-time activity stream with current location
3. **Alert Center** - Active & past alerts with one-click acknowledge
4. **Routine Timeline** - Today vs baseline with AI summary
5. **Weekly Trends** - 7-day visualization with patterns
6. **Day Detail View** - Deep dive into any day's activities
7. **Semantic Search** - Natural language query interface

### 🔄 Real-Time Updates

The dashboard automatically connects to the WebSocket endpoint at:
```
ws://localhost:8000/ws/alerts/{household_id}
```

### 🎨 Modern UI

- Responsive design (mobile, tablet, desktop)
- Tailwind CSS styling
- Lucide icons
- Recharts for data visualization
- Smooth animations and transitions

## Folder Structure

```
dashboard/
├── src/
│   ├── components/           # All dashboard components
│   ├── hooks/                # useWebSocket hook
│   ├── services/             # API service layer
│   ├── types/                # TypeScript definitions
│   └── utils/                # Helper functions
├── package.json              # Dependencies
├── vite.config.ts            # Vite configuration
├── tailwind.config.js        # Tailwind configuration
└── tsconfig.json             # TypeScript configuration
```

## Backend Integration

Make sure your FastAPI backend is running on port 8000 with these endpoints:

- `/api/households` - List households
- `/api/events` - Event stream
- `/api/alerts` - Alert management
- `/api/routines` - Routine data
- `/api/trends/weekly` - Weekly analytics
- `/api/details/day` - Day details
- `/api/search` - Semantic search
- `/ws/alerts/{id}` - WebSocket connection

## Development Commands

```bash
# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Customization

### Colors
Edit [tailwind.config.js](tailwind.config.js) to customize the color scheme.

### API URL
Edit `.env` to change the backend API URL:
```
VITE_API_URL=http://your-api-url:8000
```

### Components
All components are in [src/components/](src/components/) and can be customized independently.

## Next Steps

1. **Connect to Real Data**: Update API endpoints to match your backend
2. **Add Authentication**: Implement user login and auth tokens
3. **Customize Styling**: Adjust colors and layouts to match your brand
4. **Add More Features**: Extend components with additional functionality
5. **Deploy**: Build and deploy to your hosting platform

## Troubleshooting

**Port already in use?**
```bash
# Change the port in vite.config.ts or use:
npm run dev -- --port 3001
```

**API connection issues?**
- Ensure backend is running on port 8000
- Check CORS settings in FastAPI
- Verify API endpoint paths

**WebSocket not connecting?**
- Check WebSocket URL in useWebSocket hook
- Ensure backend WebSocket endpoint is active
- Check browser console for connection errors

## Support

For issues or questions:
- Check the main [README.md](README.md)
- Review component code in [src/components/](src/components/)
- Check backend API documentation

---

**Happy monitoring! 🏥💙**
