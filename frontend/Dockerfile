# frontend/Dockerfile
#
# Multi-stage build for the React frontend.
#
# Stage 1 (builder): installs dependencies and builds the static assets.
# Stage 2 (runtime): serves the built assets with Nginx (a lightweight,
#   production-grade web server).  The Nginx config also proxies API requests
#   to the backend container so the browser only needs one origin.

# ── Stage 1: Node builder ────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package manifests first — Docker caches this layer so `npm install`
# only re-runs when package.json or package-lock.json changes.
COPY package.json package-lock.json* ./

RUN npm install

# Copy all source files and build the production bundle.
# VITE_API_BASE_URL is injected at build time via --build-arg so the frontend
# knows the backend URL without needing runtime JavaScript.
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build    # Outputs to /app/dist

# ── Stage 2: Nginx static server ──────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Copy the built React app into Nginx's web root
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom Nginx config: enables React Router (HTML5 history API) by
# redirecting all 404s back to index.html, and proxies /api/* to the backend.
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
