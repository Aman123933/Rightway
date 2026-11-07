/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Noto Sans Devanagari', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#f0f5fa',
          100: '#e1ecf5',
          200: '#c3d9eb',
          600: '#1e5a8a',
          700: '#16456b',
          800: '#113350',
          900: '#0c2438',
        },
      },
    },
  },
  plugins: [],
}
