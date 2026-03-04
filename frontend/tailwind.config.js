/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          purple: '#8b5cf6',
          pink:   '#ec4899',
        },
      },
    },
  },
  plugins: [],
}
