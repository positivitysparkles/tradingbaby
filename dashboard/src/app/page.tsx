'use client'

import { useEffect, useState, useCallback } from 'react'
import { createClient } from '@supabase/supabase-js'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { format, parseISO, subDays } from 'date-fns'
import { GOALS, AFFIRMATIONS } from '../goals'

// Fallback placeholders keep the production build from throwing during prerender
// when env vars aren't present. On Vercel the real NEXT_PUBLIC_* values are used.
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL  || 'https://placeholder.supabase.co',
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-anon-key',
)

type Trade = {
  id: string
  date: string
  time_et: string
  ticker: string
  status: string
  entry_price: number
  exit_price: number | null
  qty: number
  realized_pnl: number | null
  stop_price: number
  t1_price: number
  t2_price: number
  t3_price: number
  setup_score: number
  setup_max: number
  deep_curl: boolean
  k_value: number
  d_value: number
  vol_ratio: number
  macd_hist: number
  macd_line: number
  exit_reason: string | null
  blockers: string | null
  notes: string | null
  grade: string | null
  catalyst: string | null
  session: string | null
}

// Closed trades before the bot stops "learning" and starts "tightening"
// (mirrors LEARN_THRESHOLD in bot/edge config).
const LEARN_THRESHOLD = 30
const GRADES = ['A+', 'A', 'B', 'C'] as const
const SESSIONS = ['premarket', 'open', 'midday', 'power hour', 'after-hours'] as const

// ── Midnight Rosé palette ─────────────────────────────────────────────────────
const C = {
  bg:       '#0b0910',
  surface:  '#15111f',
  surface2: '#1c1729',
  ink:      '#f3eef7',
  inkSoft:  '#9c90ad',
  pink:     '#ff5fa2',
  pinkSoft: '#ffa6cd',
  pinkDim:  '#b8407a',
  gold:     '#e7c79c',
  line:     'rgba(255,95,162,0.16)',
  win:      '#57e0a0',
  loss:     '#ff6b81',
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function sessionOf(timeEt: string): string {
  // timeEt like "07:42" or "07:42 ET"
  const m = /(\d{1,2}):(\d{2})/.exec(timeEt || '')
  if (!m) return 'unknown'
  const h = parseInt(m[1], 10) + parseInt(m[2], 10) / 60
  if (h < 9.5)  return 'premarket'
  if (h < 10.5) return 'open'
  if (h < 15)   return 'midday'
  if (h < 16)   return 'power hour'
  return 'after-hours'
}

function pnlStyle(v: number | null) {
  if (v === null) return { color: C.inkSoft }
  return { color: v >= 0 ? C.win : C.loss }
}

function topKey(counts: Record<string, number>): [string, number] | null {
  const e = Object.entries(counts).sort(([, a], [, b]) => b - a)
  return e.length ? e[0] : null
}

// ── Atoms ─────────────────────────────────────────────────────────────────────
function GradeBadge({ grade }: { grade: string | null }) {
  if (!grade) return <span style={{ color: C.inkSoft }} className="mono text-xs">—</span>
  const color = grade.startsWith('A') ? C.pink : grade === 'B' ? C.gold : C.inkSoft
  const glow  = grade === 'A+' ? { textShadow: '0 0 12px rgba(255,95,162,0.7)' } : {}
  return <span style={{ color, ...glow }} className="font-bold mono text-xs tracking-wide">{grade}</span>
}

function ScoreDots({ score, max }: { score: number; max: number }) {
  return (
    <span className="flex gap-1 items-center">
      {Array.from({ length: max }).map((_, i) => (
        <span key={i} style={{ background: i < score ? C.pink : 'rgba(255,95,162,0.18)' }}
          className="w-1.5 h-1.5 rounded-full inline-block" />
      ))}
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; text: string }> = {
    open:    { bg: 'rgba(255,95,162,0.14)', text: C.pink },
    closed:  { bg: 'rgba(156,144,173,0.14)', text: C.inkSoft },
    stopped: { bg: 'rgba(255,107,129,0.14)', text: C.loss },
  }
  const s = map[status] ?? map.closed
  return (
    <span style={{ background: s.bg, color: s.text }}
      className="text-[10px] px-2 py-0.5 rounded-md font-medium tracking-wider uppercase mono">
      {status}
    </span>
  )
}

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.line}`, boxShadow: '0 0 0 1px rgba(255,95,162,0.06), 0 18px 50px rgba(0,0,0,0.5)' }}
      className={`rounded-2xl ${className}`}>
      {children}
    </div>
  )
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ color: C.pink }} className="text-[10px] tracking-[0.28em] uppercase font-semibold mono mb-3">
      {children}
    </p>
  )
}

function Kpi({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
  return (
    <Card className="p-5 flex flex-col gap-1">
      <p style={{ color: C.inkSoft }} className="text-[10px] tracking-[0.2em] uppercase mono">{label}</p>
      <p style={{ color }} className="font-display text-3xl font-bold leading-none mt-1 mono">{value}</p>
      <p style={{ color: C.inkSoft }} className="text-xs mt-1">{sub}</p>
    </Card>
  )
}

function Divider() {
  return (
    <div className="flex items-center gap-3 my-7">
      <div style={{ background: `linear-gradient(to right, transparent, ${C.line})` }} className="flex-1 h-px" />
      <span style={{ color: C.pink }} className="text-xs tracking-[0.3em]">✦</span>
      <div style={{ background: `linear-gradient(to left, transparent, ${C.line})` }} className="flex-1 h-px" />
    </div>
  )
}

export default function Dashboard() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [range, setRange] = useState<7 | 30 | 90>(30)

  const load = useCallback(async () => {
    setLoading(true)
    const since = subDays(new Date(), range).toISOString().slice(0, 10)
    const { data, error } = await supabase
      .from('w118_trades')
      .select('*')
      .gte('date', since)
      .order('date', { ascending: false })
      .order('time_et', { ascending: false })
    if (!error) setTrades(data as Trade[])
    setLoading(false)
  }, [range])

  useEffect(() => { load() }, [load])

  // ── Stats ──────────────────────────────────────────────────────────────────
  const closed  = trades.filter(t => t.status !== 'open' && t.realized_pnl !== null)
  const open    = trades.filter(t => t.status === 'open')
  const netPnl  = closed.reduce((s, t) => s + (t.realized_pnl ?? 0), 0)
  const winners = closed.filter(t => (t.realized_pnl ?? 0) > 0)
  const losers  = closed.filter(t => (t.realized_pnl ?? 0) < 0)
  const winRate = closed.length ? Math.round((winners.length / closed.length) * 100) : 0
  const avgWin  = winners.length ? winners.reduce((s, t) => s + (t.realized_pnl ?? 0), 0) / winners.length : 0
  const avgLoss = losers.length ? losers.reduce((s, t) => s + (t.realized_pnl ?? 0), 0) / losers.length : 0
  const goalFuel = Math.max(0, netPnl)

  // Cumulative P&L chart
  const byDate: Record<string, number> = {}
  ;[...closed].reverse().forEach(t => { byDate[t.date] = (byDate[t.date] ?? 0) + (t.realized_pnl ?? 0) })
  let running = 0
  const chartData = Object.entries(byDate).map(([d, v]) => {
    running += v
    return { date: format(parseISO(d), 'MMM d'), pnl: parseFloat(running.toFixed(2)) }
  })

  // Daily affirmation
  const affirmation = AFFIRMATIONS[Math.floor(Date.now() / 86400000) % AFFIRMATIONS.length]

  // ── Loss Autopsy ───────────────────────────────────────────────────────────
  const lossReasons: Record<string, number> = {}
  const lossSessions: Record<string, number> = {}
  losers.forEach(t => {
    const r = t.exit_reason ?? 'unknown'
    lossReasons[r] = (lossReasons[r] ?? 0) + 1
    const s = sessionOf(t.time_et)
    lossSessions[s] = (lossSessions[s] ?? 0) + 1
  })
  const topLossReason  = topKey(lossReasons)
  const topLossSession = topKey(lossSessions)
  const avgLoserScore  = losers.length ? losers.reduce((s, t) => s + (t.setup_score ?? 0), 0) / losers.length : 0
  const avgWinnerScore = winners.length ? winners.reduce((s, t) => s + (t.setup_score ?? 0), 0) / winners.length : 0

  // Informational corrective insight (never auto-applied — for the human only)
  let corrective = 'Not enough losing trades yet to find a pattern. Keep the sample growing.'
  if (losers.length >= 3) {
    const bits: string[] = []
    if (topLossReason)  bits.push(`most losses exit via “${topLossReason[0]}” (${topLossReason[1]}×)`)
    if (topLossSession) bits.push(`cluster in the ${topLossSession[0]} session`)
    if (avgLoserScore + 0.4 < avgWinnerScore)
      bits.push(`losers average a weaker setup (${avgLoserScore.toFixed(1)} vs ${avgWinnerScore.toFixed(1)} dots)`)
    corrective = bits.length
      ? `Pattern: ${bits.join('; ')}. Tighten entries there.`
      : 'Losses look evenly spread — no single leak to plug yet.'
  }

  // ── Setup quality / deep curl / exit reasons ─────────────────────────────────
  const dc      = closed.filter(t => t.deep_curl)
  const dcWins  = dc.filter(t => (t.realized_pnl ?? 0) > 0).length
  const dcRate  = dc.length ? Math.round((dcWins / dc.length) * 100) : null
  const std     = closed.filter(t => !t.deep_curl)
  const stdWins = std.filter(t => (t.realized_pnl ?? 0) > 0).length
  const stdRate = std.length ? Math.round((stdWins / std.length) * 100) : null

  const exitReasons: Record<string, number> = {}
  closed.forEach(t => { const k = t.exit_reason ?? 'unknown'; exitReasons[k] = (exitReasons[k] ?? 0) + 1 })

  // ── Edge Report (learn → tighten) ────────────────────────────────────────────
  const phase = closed.length < LEARN_THRESHOLD ? 'Learning' : 'Tightening'
  const learnPct = Math.min(100, Math.round((closed.length / LEARN_THRESHOLD) * 100))
  const gradeStats = GRADES.map(g => {
    const ts = closed.filter(t => t.grade === g)
    const w  = ts.filter(t => (t.realized_pnl ?? 0) > 0).length
    const pnl = ts.reduce((s, t) => s + (t.realized_pnl ?? 0), 0)
    return { g, count: ts.length, win: ts.length ? Math.round((w / ts.length) * 100) : null, pnl }
  }).filter(s => s.count > 0)
  const sessionStats = SESSIONS.map(s => {
    const ts = closed.filter(t => (t.session ?? sessionOf(t.time_et)) === s)
    const w  = ts.filter(t => (t.realized_pnl ?? 0) > 0).length
    return { s, count: ts.length, win: ts.length ? Math.round((w / ts.length) * 100) : null }
  }).filter(x => x.count > 0)
  const bestGrade = gradeStats.filter(s => s.count >= 2).sort((a, b) => (b.win ?? 0) - (a.win ?? 0))[0]

  return (
    <div className="min-h-screen px-4 py-10 md:px-10 max-w-6xl mx-auto" style={{ color: C.ink }}>

      {/* ── Header ── */}
      <header>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <p style={{ color: C.pink }} className="text-[10px] tracking-[0.32em] uppercase font-semibold mono mb-2">
              Curl if Flow · Strategic Alpha
            </p>
            <h1 className="font-display text-5xl md:text-6xl font-bold leading-none tracking-tight" style={{ color: C.ink }}>
              <span style={{ color: C.pink }} className="glow-pink">Olya&rsquo;s</span> Dashboard
            </h1>
            <div className="mt-3 inline-flex items-center gap-2">
              <span
                style={{
                  background: phase === 'Tightening' ? 'rgba(87,224,160,0.12)' : 'rgba(255,95,162,0.12)',
                  color:      phase === 'Tightening' ? C.win : C.pink,
                  border:     `1px solid ${phase === 'Tightening' ? 'rgba(87,224,160,0.3)' : C.line}`,
                }}
                className="text-[10px] px-2.5 py-1 rounded-full mono tracking-wider uppercase font-semibold"
              >
                {phase === 'Tightening' ? '◆ Tightening' : `◇ Learning ${closed.length}/${LEARN_THRESHOLD}`}
              </span>
              <span style={{ color: C.inkSoft }} className="text-[10px] mono">
                self-improving
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 mt-1">
            {([7, 30, 90] as const).map(r => (
              <button key={r} onClick={() => setRange(r)}
                style={{
                  background: range === r ? C.pink : 'transparent',
                  color:      range === r ? C.bg : C.inkSoft,
                  border:     `1px solid ${range === r ? C.pink : C.line}`,
                }}
                className="px-3 py-1 rounded-lg text-xs mono transition-all duration-200">
                {r}d
              </button>
            ))}
            <button onClick={load} style={{ color: C.inkSoft, border: `1px solid ${C.line}` }}
              className="px-3 py-1 rounded-lg text-xs mono hover:opacity-80 transition-opacity">↻</button>
          </div>
        </div>

        {/* Mantra */}
        <div style={{ background: C.surface, border: `1px solid ${C.line}` }}
          className="mt-5 rounded-2xl px-5 py-4 flex items-center justify-between flex-wrap gap-2">
          <p className="font-display text-lg md:text-xl font-medium" style={{ color: C.ink }}>“{affirmation}”</p>
          <p style={{ color: C.gold }} className="text-[10px] tracking-[0.3em] uppercase font-semibold mono">Discipline = Freedom</p>
        </div>
      </header>

      <Divider />

      {/* ── KPIs ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Kpi label="Net P&L" value={`${netPnl >= 0 ? '+' : ''}$${netPnl.toFixed(2)}`}
          color={netPnl >= 0 ? C.win : C.loss} sub={`${closed.length} closed`} />
        <Kpi label="Win Rate" value={`${winRate}%`}
          color={winRate >= 70 ? C.win : winRate >= 50 ? C.pink : C.loss} sub={`${winners.length}W / ${losers.length}L`} />
        <Kpi label="Avg Win" value={`+$${avgWin.toFixed(2)}`} color={C.win} sub={`Avg Loss $${avgLoss.toFixed(2)}`} />
        <Kpi label="Live" value={`${open.length}`} color={C.pink}
          sub={open.length ? open.map(t => t.ticker).join(', ') : 'flat'} />
      </div>

      {/* ── Goals ── */}
      <Card className="p-5 mb-8">
        <div className="flex items-center justify-between mb-4">
          <Label>Building Toward</Label>
          <p style={{ color: C.inkSoft }} className="text-xs mono">
            Fuel <span style={{ color: C.win }} className="font-semibold">${goalFuel.toFixed(2)}</span>
          </p>
        </div>
        <div className="space-y-5">
          {GOALS.map(g => {
            const pct = Math.min(100, (goalFuel / g.target) * 100)
            const reached = goalFuel >= g.target
            return (
              <div key={g.label}>
                <div className="flex items-baseline justify-between mb-1.5">
                  <p className="text-sm font-medium" style={{ color: C.ink }}>
                    <span className="mr-1.5">{g.emoji}</span>{g.label}
                    {reached && <span style={{ color: C.win }} className="ml-2 text-xs mono">✓ reached</span>}
                  </p>
                  <p className="text-xs mono" style={{ color: C.inkSoft }}>
                    ${goalFuel.toFixed(0)} <span className="opacity-50">/ ${g.target.toLocaleString()}</span>
                  </p>
                </div>
                <div style={{ background: C.surface2 }} className="h-2.5 rounded-full overflow-hidden">
                  <div style={{
                    width: `${pct}%`,
                    background: reached
                      ? `linear-gradient(90deg, ${C.win}, #8af0c0)`
                      : `linear-gradient(90deg, ${C.pinkDim}, ${C.pink}, ${C.pinkSoft})`,
                    boxShadow: reached ? 'none' : '0 0 14px rgba(255,95,162,0.5)',
                  }} className="h-full rounded-full transition-all duration-700" />
                </div>
                <div className="flex items-center justify-between mt-1.5">
                  <p className="text-xs" style={{ color: C.inkSoft }}>{g.note}</p>
                  <p className="text-[11px] font-semibold mono" style={{ color: C.pink }}>{pct.toFixed(0)}%</p>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* ── P&L chart ── */}
      {chartData.length > 1 && (
        <Card className="p-5 mb-8">
          <Label>Cumulative P&L · {range}d</Label>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="pinkGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.pink} stopOpacity={0.35} />
                  <stop offset="95%" stopColor={C.pink} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,95,162,0.1)" />
              <XAxis dataKey="date" tick={{ fill: C.inkSoft, fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: C.inkSoft, fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} />
              <Tooltip contentStyle={{ background: C.surface2, border: `1px solid ${C.line}`, borderRadius: 12, fontFamily: 'JetBrains Mono', fontSize: 12, color: C.ink }}
                labelStyle={{ color: C.inkSoft }} formatter={(v: number) => [`$${v.toFixed(2)}`, 'P&L']} />
              <Area type="monotone" dataKey="pnl" stroke={C.pink} strokeWidth={2} fill="url(#pinkGrad)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* ── Loss Autopsy & Corrective Actions ── */}
      <Card className="p-5 mb-8">
        <div className="flex items-center justify-between mb-4">
          <Label>Loss Autopsy &amp; Corrective Actions</Label>
          <span style={{ color: C.loss }} className="text-xs mono">{losers.length} loss{losers.length === 1 ? '' : 'es'}</span>
        </div>

        {/* Corrective insight banner */}
        <div style={{ background: C.surface2, border: `1px solid ${C.line}` }} className="rounded-xl px-4 py-3 mb-4">
          <p className="text-[10px] tracking-[0.2em] uppercase mono mb-1" style={{ color: C.gold }}>What to fix</p>
          <p className="text-sm" style={{ color: C.ink }}>{corrective}</p>
        </div>

        {/* Per-loss table */}
        {losers.length > 0 ? (
          <div className="space-y-2">
            {losers.slice(0, 8).map(t => (
              <div key={t.id} className="flex items-start justify-between gap-3 py-2"
                style={{ borderBottom: `1px solid rgba(255,95,162,0.08)` }}>
                <div className="min-w-0">
                  <p className="text-sm font-semibold" style={{ color: C.ink }}>
                    {t.ticker}
                    <span className="ml-2 text-[11px] mono" style={{ color: C.inkSoft }}>
                      {format(parseISO(t.date), 'MMM d')} · {sessionOf(t.time_et)}
                    </span>
                  </p>
                  <p className="text-xs mt-0.5 truncate" style={{ color: C.inkSoft }}>
                    {t.notes ?? t.exit_reason ?? 'no note logged'}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-semibold mono" style={{ color: C.loss }}>
                    ${(t.realized_pnl ?? 0).toFixed(2)}
                  </p>
                  <div className="mt-1 flex justify-end"><ScoreDots score={t.setup_score ?? 0} max={t.setup_max ?? 5} /></div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm" style={{ color: C.inkSoft }}>No losing trades in this window. Clean book. 🤍</p>
        )}
      </Card>

      {/* ── Edge Report — what's working ── */}
      <Card className="p-5 mb-8">
        <div className="flex items-center justify-between mb-4">
          <Label>Edge Report — What&rsquo;s Working</Label>
          <span style={{ color: phase === 'Tightening' ? C.win : C.pink }} className="text-xs mono">
            {phase === 'Tightening' ? 'tightening live' : `learning ${closed.length}/${LEARN_THRESHOLD}`}
          </span>
        </div>

        {/* Learn → tighten progress */}
        <div className="mb-5">
          <div className="flex justify-between text-[11px] mono mb-1.5" style={{ color: C.inkSoft }}>
            <span>Data gathered toward auto-tighten</span>
            <span>{learnPct}%</span>
          </div>
          <div style={{ background: C.surface2 }} className="h-2 rounded-full overflow-hidden">
            <div style={{
              width: `${learnPct}%`,
              background: phase === 'Tightening'
                ? `linear-gradient(90deg, ${C.win}, #8af0c0)`
                : `linear-gradient(90deg, ${C.pinkDim}, ${C.pink}, ${C.pinkSoft})`,
            }} className="h-full rounded-full transition-all duration-700" />
          </div>
          <p className="text-xs mt-2" style={{ color: C.inkSoft }}>
            {phase === 'Tightening'
              ? 'The bot now auto-buys only grades proven to win; weaker setups drop to manual alerts.'
              : `Still taking every valid signal to learn. At ${LEARN_THRESHOLD} closed trades it auto-restricts to what wins.`}
            {bestGrade && ` Best grade so far: ${bestGrade.g} (${bestGrade.win}% over ${bestGrade.count}).`}
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 text-sm">
          {/* By grade */}
          <div>
            <p style={{ color: C.ink }} className="text-xs font-semibold tracking-wide uppercase mb-3 mono">Win Rate by Grade</p>
            {gradeStats.length ? gradeStats.map(s => (
              <div key={s.g} className="flex items-center gap-3 mb-2">
                <span className="w-7"><GradeBadge grade={s.g} /></span>
                <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: C.surface2 }}>
                  <div style={{ width: `${s.win ?? 0}%`, background: (s.win ?? 0) >= 50 ? C.win : C.pink }} className="h-full rounded-full" />
                </div>
                <span className="text-xs mono shrink-0" style={{ color: C.inkSoft }}>{s.win}% · {s.count}</span>
                <span className="text-xs mono shrink-0 w-16 text-right" style={{ color: s.pnl >= 0 ? C.win : C.loss }}>
                  {s.pnl >= 0 ? '+' : ''}${s.pnl.toFixed(0)}
                </span>
              </div>
            )) : <span style={{ color: C.inkSoft }} className="text-xs">No graded closed trades yet.</span>}
          </div>

          {/* By session */}
          <div>
            <p style={{ color: C.ink }} className="text-xs font-semibold tracking-wide uppercase mb-3 mono">Win Rate by Session</p>
            {sessionStats.length ? sessionStats.map(s => (
              <div key={s.s} className="flex items-center gap-3 mb-2">
                <span className="text-xs w-24 shrink-0" style={{ color: C.ink }}>{s.s}</span>
                <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: C.surface2 }}>
                  <div style={{ width: `${s.win ?? 0}%`, background: (s.win ?? 0) >= 50 ? C.win : C.pink }} className="h-full rounded-full" />
                </div>
                <span className="text-xs mono shrink-0" style={{ color: C.inkSoft }}>{s.win}% · {s.count}</span>
              </div>
            )) : <span style={{ color: C.inkSoft }} className="text-xs">No closed trades yet.</span>}
          </div>
        </div>
      </Card>

      {/* ── Trade log ── */}
      <Card className="overflow-hidden mb-8">
        <div style={{ borderBottom: `1px solid ${C.line}` }} className="px-5 py-3 flex items-center justify-between">
          <Label>Trade Log</Label>
          {loading && <span style={{ color: C.pink }} className="text-xs mono animate-pulse">loading…</span>}
        </div>

        {/* Desktop */}
        <div className="overflow-x-auto hidden md:block">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: `1px solid ${C.line}` }}>
                {['Date', 'Ticker', 'Grade', 'Status', 'Entry', 'Exit', 'P&L', 'Setup', 'K/D', 'Vol', 'Note'].map(h => (
                  <th key={h} style={{ color: C.inkSoft }} className="px-4 py-2 text-left text-[10px] tracking-[0.15em] uppercase mono">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {trades.map((t, i) => (
                <tr key={t.id} style={{ borderBottom: i < trades.length - 1 ? `1px solid rgba(255,95,162,0.07)` : undefined }}
                  className="transition-colors hover:bg-[rgba(255,95,162,0.05)]">
                  <td className="px-4 py-3 whitespace-nowrap mono text-xs" style={{ color: C.inkSoft }}>
                    {format(parseISO(t.date), 'MMM d')}<span className="ml-1.5 opacity-60">{t.time_et}</span>
                  </td>
                  <td className="px-4 py-3 font-semibold" style={{ color: C.ink }}>
                    {t.ticker}{t.deep_curl && <span style={{ color: C.pink }} className="ml-1 text-xs">⭐</span>}
                  </td>
                  <td className="px-4 py-3"><GradeBadge grade={t.grade} /></td>
                  <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                  <td className="px-4 py-3 mono" style={{ color: C.ink }}>${t.entry_price?.toFixed(3)}</td>
                  <td className="px-4 py-3 mono" style={{ color: C.inkSoft }}>{t.exit_price ? `$${t.exit_price.toFixed(3)}` : '—'}</td>
                  <td className="px-4 py-3 font-semibold mono" style={pnlStyle(t.realized_pnl)}>
                    {t.realized_pnl !== null ? `${t.realized_pnl >= 0 ? '+' : ''}$${t.realized_pnl.toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-3"><ScoreDots score={t.setup_score ?? 0} max={t.setup_max ?? 5} /></td>
                  <td className="px-4 py-3 mono text-xs" style={{ color: C.inkSoft }}>{t.k_value?.toFixed(0)}/{t.d_value?.toFixed(0)}</td>
                  <td className="px-4 py-3 mono text-xs" style={{ color: C.inkSoft }}>{t.vol_ratio?.toFixed(1)}×</td>
                  <td className="px-4 py-3 text-xs max-w-[180px] truncate" style={{ color: C.inkSoft }}>{t.notes ?? t.exit_reason ?? t.blockers ?? '—'}</td>
                </tr>
              ))}
              {!loading && trades.length === 0 && (
                <tr><td colSpan={11} className="px-4 py-12 text-center font-display text-lg" style={{ color: C.inkSoft }}>
                  No trades in the last {range} days. The patient win.
                </td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile */}
        <div className="md:hidden">
          {trades.map((t, i) => (
            <div key={t.id} className="p-4" style={{ borderTop: i > 0 ? `1px solid rgba(255,95,162,0.1)` : undefined }}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold" style={{ color: C.ink }}>{t.ticker}</span>
                  {t.deep_curl && <span style={{ color: C.pink }}>⭐</span>}
                  <GradeBadge grade={t.grade} />
                  <StatusBadge status={t.status} />
                </div>
                <span className="font-semibold mono" style={pnlStyle(t.realized_pnl)}>
                  {t.realized_pnl !== null ? `${t.realized_pnl >= 0 ? '+' : ''}$${t.realized_pnl.toFixed(2)}` : 'open'}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs mono" style={{ color: C.inkSoft }}>
                <span>{format(parseISO(t.date), 'MMM d')} {t.time_et}</span>
                <span>${t.entry_price?.toFixed(3)}{t.exit_price ? `→$${t.exit_price.toFixed(3)}` : ''}</span>
                <span>{t.vol_ratio?.toFixed(1)}×</span>
              </div>
              {(t.notes ?? t.exit_reason) && <p className="text-xs mt-2" style={{ color: C.inkSoft }}>{t.notes ?? t.exit_reason}</p>}
            </div>
          ))}
        </div>
      </Card>

      {/* ── Self-Audit ── */}
      <Card className="p-5">
        <Label>Strategic Self-Audit</Label>
        <div className="grid md:grid-cols-3 gap-6 text-sm">
          <div>
            <p style={{ color: C.ink }} className="text-xs font-semibold tracking-wide uppercase mb-3 mono">Setup Quality</p>
            {[5, 4, 3, 2].map(score => {
              const count = trades.filter(t => t.setup_score === score).length
              const won = trades.filter(t => t.setup_score === score && (t.realized_pnl ?? 0) > 0).length
              const rate = count > 0 ? Math.round((won / count) * 100) : null
              return (
                <div key={score} className="flex items-center gap-3 mb-2">
                  <ScoreDots score={score} max={5} />
                  <span style={{ color: C.inkSoft }} className="text-xs mono">{count} trades</span>
                  {rate !== null && <span style={{ color: rate >= 70 ? C.win : C.pink }} className="text-xs ml-auto font-semibold mono">{rate}%</span>}
                </div>
              )
            })}
          </div>
          <div>
            <p style={{ color: C.ink }} className="text-xs font-semibold tracking-wide uppercase mb-3 mono">Deep Curl ⭐</p>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span style={{ color: C.ink }}>Deep curl</span>
                <span className="mono font-semibold" style={{ color: dcRate !== null && (stdRate === null || dcRate > stdRate) ? C.win : C.inkSoft }}>
                  {dcRate !== null ? `${dcRate}%` : '—'} ({dc.length})
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span style={{ color: C.inkSoft }}>Standard</span>
                <span className="mono" style={{ color: C.inkSoft }}>{stdRate !== null ? `${stdRate}%` : '—'} ({std.length})</span>
              </div>
              <p style={{ color: C.inkSoft }} className="text-xs mt-3 leading-relaxed">
                {dc.length < 5 ? 'Need more data to draw conclusions.'
                  : dcRate !== null && stdRate !== null && dcRate > stdRate ? '⭐ Deep curls outperforming. Prioritize them.'
                  : 'Deep curls not showing edge yet.'}
              </p>
            </div>
          </div>
          <div>
            <p style={{ color: C.ink }} className="text-xs font-semibold tracking-wide uppercase mb-3 mono">Exit Reasons</p>
            <div className="space-y-2">
              {Object.entries(exitReasons).sort(([, a], [, b]) => b - a).slice(0, 6).map(([r, n]) => (
                <div key={r} className="flex justify-between text-xs">
                  <span style={{ color: C.inkSoft }} className="truncate max-w-[160px]">{r}</span>
                  <span style={{ color: C.pink }} className="ml-2 shrink-0 font-semibold mono">{n}×</span>
                </div>
              ))}
              {Object.keys(exitReasons).length === 0 && <span style={{ color: C.inkSoft }} className="text-xs">No closed trades yet.</span>}
            </div>
          </div>
        </div>
      </Card>

      <Divider />
      <p style={{ color: C.inkSoft }} className="text-center text-[10px] tracking-[0.3em] uppercase mono">
        Romanticize your discipline · Private · {new Date().getFullYear()}
      </p>
    </div>
  )
}
