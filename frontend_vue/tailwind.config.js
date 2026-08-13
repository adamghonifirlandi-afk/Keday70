/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0B0E14',
        surface: '#151A22',
        surface2: '#212631',
        primary: '#4ECCA3',
        secondary: '#00B8D9',
        accent: '#7F77DD',
        warning: '#EF9F27',
        danger: '#E24B4A',
        success: '#97C459',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
