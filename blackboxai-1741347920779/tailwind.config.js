/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.{html,htm}",
    "./static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        // Primary color (amber replacing coral)
        'primary': '#F59E0B', // amber-500
        'primary-light': '#FCD34D', // amber-300
        'primary-dark': '#D97706', // amber-600
        
        // Action colors
        'danger': '#DC2626', // red-600
        'success': '#059669', // green-600
        
        // Legacy color name support (mapped to new values)
        'bs-coral': '#F59E0B', // amber-500
        'bs-yellow': '#FCD34D', // amber-300
        'bs-darkyellow': '#D97706', // amber-600
        'bs-red': '#DC2626', // red-600
        'bs-green': '#059669', // green-600
      },
      fontFamily: {
        'primary': ['"Analogist"', 'sans-serif'],
        'secondary': ['"Oswald-Medium"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}