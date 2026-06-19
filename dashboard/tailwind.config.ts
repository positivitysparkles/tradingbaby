import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        gold:    { DEFAULT: '#c9a96e', dim: '#8b6e3c', muted: 'rgba(201,169,110,0.14)' },
        rose:    { DEFAULT: '#c4789b', dim: '#8b4e6e' },
        cream:   '#f0ebe0',
        taupe:   '#7a6a5a',
        bg:      '#080807',
        surface: '#100f0e',
        card:    '#141210',
        win:     '#6aad8a',
        loss:    '#c06060',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        sans:    ['Inter', 'system-ui', 'sans-serif'],
      },
      borderColor: {
        gold: 'rgba(201,169,110,0.14)',
      },
    },
  },
  plugins: [],
}
export default config
