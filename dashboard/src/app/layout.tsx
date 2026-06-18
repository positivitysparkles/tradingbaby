import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'W118 Trading Dashboard',
  description: 'Private P&L dashboard',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
