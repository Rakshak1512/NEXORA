/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cicada: {
          dark: '#070C14',
          card: '#0D1524',
          border: '#1A2740',
          hover: '#131F36',
          cyan: '#00E5FF',
          teal: '#00BFA5',
          navy: '#0A192F',
          amber: '#FFB300',
          rose: '#FF3366',
          emerald: '#00E676',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      }
    },
  },
  plugins: [],
}

