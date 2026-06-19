import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        bg:      '#f4efe6',
        bgSoft:  '#ece5d8',
        surface: '#fffdf8',
        ink:     '#2b2620',
        inkSoft: '#6b6256',
        gold:    { DEFAULT: '#b08d4f', soft: '#c9a96e' },
        line:    'rgba(176,141,79,0.22)',
        win:     '#3f8f63',
        loss:    '#b4524a',
        rose:    '#b06087',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        sans:    ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(43,38,32,0.04), 0 8px 24px rgba(43,38,32,0.05)',
      },
    },
  },
  plugins: [],
}
export default config
