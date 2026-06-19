import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        bg:      '#0b0910',
        bg2:     '#120e1a',
        surface: '#15111f',
        surface2:'#1c1729',
        ink:     '#f3eef7',
        inkSoft: '#9c90ad',
        pink:    { DEFAULT: '#ff5fa2', soft: '#ffa6cd', dim: '#b8407a' },
        gold:    '#e7c79c',
        line:    'rgba(255,95,162,0.16)',
        win:     '#57e0a0',
        loss:    '#ff6b81',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(255,95,162,0.10), 0 18px 50px rgba(0,0,0,0.5)',
      },
    },
  },
  plugins: [],
}
export default config
