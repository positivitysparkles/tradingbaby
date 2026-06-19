import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: "Olya's Dashboard",
  description: 'Private trading P&L · Curl if Flow',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
