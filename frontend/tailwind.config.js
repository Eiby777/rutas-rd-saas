/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: '#004aad', // Azul corporativo (inspirado en bandera RD)
        secondary: '#d9534f',
        success: '#5cb85c',
      },
    },
  },
  plugins: [],
}
