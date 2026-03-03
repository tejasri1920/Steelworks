// src/App.tsx
//
// Root component that defines the application's route structure.
//
// Routes:
//   /                → DashboardPage (main lot summary + filters)
//   /lots/:lot_code  → LotDetailPage (deep-dive into one lot's records)
//
// React Router's <Routes> / <Route> render the matched page component inside
// the Navbar, keeping the header visible at all times.

import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import DashboardPage from './pages/DashboardPage'
import LotDetailPage from './pages/LotDetailPage'

/**
 * Root application component.
 *
 * Renders a persistent Navbar at the top, then switches page content
 * based on the current URL path using React Router.
 */
export default function App() {
  return (
    // min-h-screen ensures the page fills the viewport even when content is short
    <div className="min-h-screen bg-slate-50">
      {/* Persistent navigation bar */}
      <Navbar />

      {/* Page content — changes with the URL */}
      <main className="max-w-screen-xl mx-auto px-4 py-6">
        <Routes>
          {/* Default route: the main Operations Dashboard */}
          <Route path="/" element={<DashboardPage />} />

          {/* Lot detail: :lot_code is a URL parameter, e.g., /lots/LOT-20260112-001 */}
          <Route path="/lots/:lot_code" element={<LotDetailPage />} />

          {/* Catch-all: redirect unknown paths back to the dashboard */}
          <Route path="*" element={<DashboardPage />} />
        </Routes>
      </main>
    </div>
  )
}
