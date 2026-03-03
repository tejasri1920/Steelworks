// src/main.tsx
//
// Application bootstrap — creates the React root and wraps the app with
// providers needed globally:
//   - QueryClientProvider: makes React Query's cache available to all components
//   - BrowserRouter: enables client-side routing with React Router

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

/**
 * Global React Query client.
 *
 * React Query manages server-state (API responses): caching, refetching,
 * loading/error states.  This replaces manual useEffect + useState patterns.
 *
 * Configuration:
 *   staleTime: 60_000 ms — data is considered "fresh" for 60 seconds.
 *     Within this window, navigating back to a page shows cached data
 *     instantly without re-fetching.  This helps with AC9 (consistent
 *     results): the analyst sees the same data in the same meeting.
 *   retry: 1 — retry once on failure before showing an error.
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,    // 60 seconds — avoid redundant refetches in meetings
      retry: 1,
    },
  },
})

// `document.getElementById('root')!` — the `!` tells TypeScript the element
// definitely exists (it's in index.html); without `!`, TypeScript would
// complain that it could be null.
ReactDOM.createRoot(document.getElementById('root')!).render(
  // StrictMode renders components twice in development to help detect side effects.
  // Has no effect in production builds.
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
