/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/renderer/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'electron-bg': '#1e1e1e',
        'electron-surface': '#252525',
        'electron-border': '#3c3c3c',
        'electron-text': '#cccccc',
        'electron-accent': '#0078d4',
        'agent-analysis': '#3b82f6',
        'agent-gemini': '#34d399',
        'agent-imagemagick': '#f59e0b',
        'agent-background': '#8b5cf6',
        'agent-qc': '#ef4444',
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-gentle': 'bounce 1s infinite',
      }
    },
  },
  plugins: [],
}