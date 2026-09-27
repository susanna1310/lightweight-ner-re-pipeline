/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.html', './src/**/*.js', './src/**/*.jsx'],
  theme: {
    extend: {},
  },
  plugins: [
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        tum: {
          "primary": "#0065BD",
          "primary-content": "#ffffff",
          "secondary": "#005293",
          "secondary-content": "#ffffff",
          "accent": "#98C6EA",
          "accent-content": "#003359",
          "neutral": "#232323",
          "neutral-content": "#ffffff",
          "base-100": "#ffffff",
          "base-200": "#f2f6fa",
          "base-300": "#dbe4ee",
          "base-content": "#1f2937",
          "info": "#3ABFF8",
          "success": "#36D399",
          "warning": "#FBBD23",
          "error": "#F87272",
        },
      },
    ],
  },
}
