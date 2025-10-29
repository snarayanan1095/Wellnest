import { useState } from 'react'
import type { Household, Alert, LiveFeedItem } from './types'

function App() {
  const [households] = useState<Household[]>([
    {
      id: '1',
      name: 'Demo Household',
      residents: [{ id: '1', name: 'Demo User', age: 75 }],
      status: 'normal',
      todayScore: 85,
      lastUpdate: new Date(),
    }
  ])

  const [alerts] = useState<Alert[]>([])
  const [liveFeed] = useState<LiveFeedItem[]>([])

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
            <div
              key={household.id}
              className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{household.name}</h3>
                  <p className="text-sm text-gray-500">
                    {household.residents.length} resident(s)
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                  All Good
                </span>
              </div>

              <div className="border-t pt-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Today's Score</span>
                  <span className="text-2xl font-bold text-green-600">
                    {household.todayScore}
                  </span>
                </div>
                <div className="mt-2 bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-green-500 transition-all duration-500"
                    style={{ width: `${household.todayScore}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Status Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Live Feed */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Live Activity Feed</h2>
            {liveFeed.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <p>No recent activity</p>
                <p className="text-sm mt-2">Connect to API to see live events</p>
              </div>
            ) : (
              <div className="space-y-3">
                {liveFeed.map((item) => (
                  <div key={item.id} className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-gray-900">{item.description}</p>
                    <p className="text-xs text-gray-600 mt-1">{item.location}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Alert Center */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Alert Center</h2>
            {alerts.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <div className="text-5xl mb-2">✓</div>
                <p>No active alerts</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div key={alert.id} className="p-4 bg-red-50 rounded-lg border border-red-200">
                    <h4 className="font-semibold text-gray-900">{alert.title}</h4>
                    <p className="text-sm text-gray-700 mt-1">{alert.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-2">🎉 Dashboard is Running!</h3>
          <p className="text-sm text-blue-800">
            The dashboard is connected and ready. Full features will appear when connected to the Wellnest API.
          </p>
          <div className="mt-3 text-xs text-blue-700">
            <p><strong>API URL:</strong> http://localhost:8000</p>
            <p><strong>Status:</strong> Waiting for data...</p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
