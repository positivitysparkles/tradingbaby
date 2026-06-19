// ── Olya's Goals ──────────────────────────────────────────────────────────────
// Edit these freely. Each goal's progress bar fills from your cumulative net
// realized P&L (the money the bot actually books). Order = priority, top first.
//
// `target`  = dollars needed to call it "reached"
// `note`    = the dream in your words (shows under the bar)
// `emoji`   = vibe

export type Goal = {
  label:  string
  emoji:  string
  target: number
  note:   string
}

export const GOALS: Goal[] = [
  {
    label:  'Moving Out Fund',
    emoji:  '🔑',
    target: 5000,
    note:   'First + last + deposit. My own space, my own rules.',
  },
  {
    label:  'Ocean View Retreat',
    emoji:  '🌊',
    target: 25000,
    note:   'Epic views. Floor-to-ceiling windows. Salt air.',
  },
  {
    label:  'Dream Car Fund',
    emoji:  '🤍',
    target: 60000,
    note:   "I'm the owner of my dream car, and it feels amazing.",
  },
  {
    label:  'Total Freedom',
    emoji:  '🕊️',
    target: 100000,
    note:   'Financially free. Discipline = Freedom.',
  },
]

// ── Mindset journal — rotates daily ───────────────────────────────────────────
export const AFFIRMATIONS: string[] = [
  "She doesn't chase. She builds.",
  'Romanticize your discipline.',
  'Discipline = Freedom.',
  'I am financially free.',
  'I am the owner of my dream life, and it feels amazing.',
  'Trading isn’t about money. It’s about who I become.',
  'Patience is a position. I wait for my setup.',
  'Small, consistent, relentless. That’s how empires are built.',
]
