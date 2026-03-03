// frontend/tailwind.config.js
//
// Tailwind CSS configuration.
// `content` tells Tailwind which files to scan for class names.
// Any class used in .tsx or .html files will be included in the CSS bundle;
// unused classes are purged in production, keeping the CSS file tiny.

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Custom colors matching a steel/industrial aesthetic
      colors: {
        brand: {
          50:  '#eff6ff',
          100: '#dbeafe',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',   // Primary — steel blue header
          900: '#1e3a8a',
        },
      },
    },
  },
  plugins: [],
}
