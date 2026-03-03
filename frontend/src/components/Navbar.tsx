// src/components/Navbar.tsx
//
// Persistent top navigation bar.
// Shows the application name and a link back to the dashboard.

import { Link } from 'react-router-dom'

/**
 * Application header / navigation bar.
 *
 * Rendered by App.tsx above <Routes> so it persists across all pages.
 * Uses React Router's <Link> instead of <a> to avoid a full page reload
 * when navigating between the dashboard and lot detail views.
 */
export default function Navbar() {
  return (
    <nav className="bg-brand-800 text-white shadow-md">
      <div className="max-w-screen-xl mx-auto px-4 py-3 flex items-center gap-6">
        {/* Logo / brand name — clicking returns to dashboard */}
        <Link to="/" className="text-xl font-bold tracking-tight hover:text-blue-200 transition-colors">
          ⚙ Steelworks Ops Analytics
        </Link>

        {/* Navigation links */}
        <div className="flex items-center gap-4 text-sm font-medium">
          <Link
            to="/"
            className="hover:text-blue-200 transition-colors"
          >
            Dashboard
          </Link>
        </div>

        {/* Spacer pushes version badge to the right */}
        <div className="ml-auto text-xs text-blue-300">v0.1.0</div>
      </div>
    </nav>
  )
}
