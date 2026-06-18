import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        green:  { 400: '#4ade80', 500: '#22c55e', 900: '#14532d' },
        red:    { 400: '#f87171', 500: '#ef4444', 900: '#7f1d1d' },
        brand:  '#7c3aed',
      },
      fontFamily: { mono: ['JetBrains Mono', 'monospace'] },
    },
  },
  plugins: [],
}
export default config
