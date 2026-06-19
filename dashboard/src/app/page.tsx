'use client'

import { useEffect, useState, useCallback } from 'react'
import { createClient } from '@supabase/supabase-js'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { format, parseISO, subDays } from 'date-fns'
import { GOALS, AFFIRMATIONS } from '../goals'

// Fallback placeholders keep the production build from throwing during
// prerender when env vars aren't present (e.g. CI). On Vercel the real
// NEXT_PUBLIC_* values are inlined at build and used in the browser.
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
}

// ── Light luxury palette ──────────────────────────────────────────────────────
const C = {
  bg:      '#f4efe6',
  surface: '#fffdf8',
  ink:     '#2b2620',
  inkSoft: '#6b6256',
  gold:    '#b08d4f',
  goldSoft:'#c9a96e',
  line:    'rgba(176,141,79,0.22)',
  win:     '#3f8f63',
  loss:    '#b4524a',
  rose:    '#b06087',
}

function pnlColor(v: number | null) {
  if (v === null) return { color: C.inkSoft }
  return { color: v >= 0 ? C.win : C.loss }
}

function ScoreDots({ score, max }: { score: number; max: number }) {
  return (
    <span className="flex gap-1 items-center">
      {Array.from({ length: max }).map((_, i) => (
        <span
          key={i}
          style={{ background: i < score ? C.gold : 'rgba(176,141,79,0.2)' }}
          className="w-1.5 h-1.5 rounded-full inline-block"
        />
      ))}
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; text: string }> = {
    open:    { bg: 'rgba(176,96,135,0.12)', text: C.rose },
    closed:  { bg: 'rgba(176,141,79,0.12)', text: C.gold },
    stopped: { bg: 'rgba(180,82,74,0.12)',  text: C.loss },
  }
  const s = map[status] ?? map.closed
  return (
    <span
      style={{ background: s.bg, color: s.text }}
      className="text-[10px] px-2 py-0.5 rounded-full font-medium tracking-wider uppercase"
    >
      {status}
    </span>
  )
}

function GoldDivider() {
  return (
    <div className="flex items-center gap-3 my-7">
      <div style={{ background: `linear-gradient(to right, transparent, ${C.line})` }} className="flex-1 h-px" />
      <span style={{ color: C.gold }} className="text-xs tracking-[0.3em]">✦</span>
      <div style={{ background: `linear-gradient(to left, transparent, ${C.line})` }} className="flex-1 h-px" />
    </div>
  )
}

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      style={{ background: C.surface, border: `1px solid ${C.line}`, boxShadow: '0 1px 2px rgba(43,38,32,0.04), 0 8px 24px rgba(43,38,32,0.05)' }}
      className={`rounded-2xl ${className}`}
    >
      {children}
    </div>
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ color: C.gold }} className="text-[10px] tracking-[0.25em] uppercase font-sans font-semibold mb-3">
      {children}
    </p>
  )
}

function KpiCard({ label, value, sub, color }: {
  label: string; value: string; sub: string; color: string
}) {
  return (
    <Card className="p-5 flex flex-col gap-1">
      <p style={{ color: C.inkSoft }} className="text-[10px] tracking-[0.2em] uppercase font-sans font-medium">
        {label}
      </p>
      <p style={{ color }} className="font-display text-3xl font-semibold leading-none mt-1">
        {value}
      </p>
      <p style={{ color: C.inkSoft }} className="text-xs font-sans mt-1">{sub}</p>
    </Card>
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

  // ── Derived stats ──────────────────────────────────────────────────────────
  const closed   = trades.filter(t => t.status !== 'open' && t.realized_pnl !== null)
  const open     = trades.filter(t => t.status === 'open')
  const netPnl   = closed.reduce((s, t) => s + (t.realized_pnl ?? 0), 0)
  const wins     = closed.filter(t => (t.realized_pnl ?? 0) > 0).length
  const losers   = closed.filter(t => (t.realized_pnl ?? 0) < 0)
  const winRate  = closed.length ? Math.round((wins / closed.length) * 100) : 0
  const avgWin   = wins
    ? closed.filter(t => (t.realized_pnl ?? 0) > 0).reduce((s, t) => s + (t.realized_pnl ?? 0), 0) / wins
    : 0
  const avgLoss  = losers.length
    ? losers.reduce((s, t) => s + (t.realized_pnl ?? 0), 0) / losers.length
    : 0

  // Total booked across ALL time-filtered closed trades = goal fuel (never below 0)
  const goalFuel = Math.max(0, netPnl)

  // Cumulative P&L by date for chart
  const byDate: Record<string, number> = {}
  ;[...closed].reverse().forEach(t => {
    byDate[t.date] = (byDate[t.date] ?? 0) + (t.realized_pnl ?? 0)
  })
  let running = 0
  const chartData = Object.entries(byDate).map(([d, v]) => {
    running += v
    return { date: format(parseISO(d), 'MMM d'), pnl: parseFloat(running.toFixed(2)) }
  })

  // Daily affirmation (rotates by day-of-year)
  const dayIdx = Math.floor(Date.now() / 86400000) % AFFIRMATIONS.length
  const affirmation = AFFIRMATIONS[dayIdx]

  // ── Audit helpers ──────────────────────────────────────────────────────────
  const deepCurlTrades = closed.filter(t => t.deep_curl)
  const dcWins  = deepCurlTrades.filter(t => (t.realized_pnl ?? 0) > 0).length
  const dcRate  = deepCurlTrades.length ? Math.round((dcWins / deepCurlTrades.length) * 100) : null
  const stdTrades = closed.filter(t => !t.deep_curl)
  const stdWins = stdTrades.filter(t => (t.realized_pnl ?? 0) > 0).length
  const stdRate = stdTrades.length ? Math.round((stdWins / stdTrades.length) * 100) : null

  const exitReasons: Record<string, number> = {}
  closed.forEach(t => {
    const k = t.exit_reason ?? 'unknown'
    exitReasons[k] = (exitReasons[k] ?? 0) + 1
  })

  return (
    <div className="min-h-screen px-4 py-10 md:px-10 max-w-6xl mx-auto" style={{ color: C.ink }}>

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <p style={{ color: C.gold, letterSpacing: '0.3em' }} className="text-[10px] uppercase font-sans font-semibold mb-2">
              W118 · Curl if Flow · Private
            </p>
            <h1 className="font-display text-5xl md:text-6xl font-semibold leading-none" style={{ color: C.ink }}>
              <span style={{ color: C.gold }} className="italic">Olya&rsquo;s</span> Dashboard
            </h1>
          </div>

          <div className="flex items-center gap-2 mt-1">
            {([7, 30, 90] as const).map(r => (
              <button
                key={r}
                onClick={() => setRange(r)}
                style={{
                  background: range === r ? C.gold : C.surface,
                  color:      range === r ? C.surface : C.inkSoft,
                  border:     `1px solid ${range === r ? C.gold : C.line}`,
                }}
                className="px-3 py-1 rounded-full text-xs font-sans transition-all duration-200"
              >
                {r}d
              </button>
            ))}
            <button
              onClick={load}
              style={{ color: C.inkSoft, background: C.surface, border: `1px solid ${C.line}` }}
              className="px-3 py-1 rounded-full text-xs font-sans hover:opacity-80 transition-opacity"
            >
              ↻
            </button>
          </div>
        </div>

        {/* Mantra banner */}
        <div
          style={{ background: C.surface, border: `1px solid ${C.line}` }}
          className="mt-5 rounded-2xl px-5 py-4 flex items-center justify-between flex-wrap gap-2"
        >
          <p className="font-display italic text-lg md:text-xl" style={{ color: C.ink }}>
            “{affirmation}”
          </p>
          <p style={{ color: C.gold }} className="text-[10px] tracking-[0.3em] uppercase font-sans font-semibold">
            Discipline = Freedom
          </p>
        </div>
      </header>

      <GoldDivider />

      {/* ── KPI cards ──────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard
          label="Net P&L"
          value={`${netPnl >= 0 ? '+' : ''}$${netPnl.toFixed(2)}`}
          color={netPnl >= 0 ? C.win : C.loss}
          sub={`${closed.length} closed trades`}
        />
        <KpiCard
          label="Win Rate"
          value={`${winRate}%`}
          color={winRate >= 70 ? C.win : winRate >= 50 ? C.gold : C.loss}
          sub={`${wins}W / ${losers.length}L`}
        />
        <KpiCard
          label="Avg Win"
          value={`+$${avgWin.toFixed(2)}`}
          color={C.win}
          sub={`Avg Loss: $${avgLoss.toFixed(2)}`}
        />
        <KpiCard
          label="Live Positions"
          value={`${open.length}`}
          color={C.rose}
          sub={open.length > 0 ? open.map(t => t.ticker).join(', ') : 'No open trades'}
        />
      </div>

      {/* ── Goal progress ──────────────────────────────────────────────────── */}
      <Card className="p-5 mb-8">
        <div className="flex items-center justify-between mb-4">
          <SectionLabel>Building Toward</SectionLabel>
          <p style={{ color: C.inkSoft }} className="text-xs font-sans">
            Fuel: <span style={{ color: C.win }} className="font-semibold">${goalFuel.toFixed(2)}</span>
          </p>
        </div>
        <div className="space-y-5">
          {GOALS.map(g => {
            const pct = Math.min(100, (goalFuel / g.target) * 100)
            const reached = goalFuel >= g.target
            return (
              <div key={g.label}>
                <div className="flex items-baseline justify-between mb-1.5">
                  <p className="font-sans text-sm font-medium" style={{ color: C.ink }}>
                    <span className="mr-1.5">{g.emoji}</span>{g.label}
                    {reached && <span style={{ color: C.win }} className="ml-2 text-xs">✓ reached</span>}
                  </p>
                  <p className="font-sans text-xs" style={{ color: C.inkSoft }}>
                    ${goalFuel.toFixed(0)} <span className="opacity-50">/ ${g.target.toLocaleString()}</span>
                  </p>
                </div>
                <div style={{ background: C.bg }} className="h-2.5 rounded-full overflow-hidden">
                  <div
                    style={{
                      width: `${pct}%`,
                      background: reached
                        ? `linear-gradient(90deg, ${C.win}, #5fae84)`
                        : `linear-gradient(90deg, ${C.gold}, ${C.goldSoft})`,
                    }}
                    className="h-full rounded-full transition-all duration-700"
                  />
                </div>
                <div className="flex items-center justify-between mt-1.5">
                  <p className="font-display italic text-xs" style={{ color: C.inkSoft }}>{g.note}</p>
                  <p className="font-sans text-[11px] font-semibold" style={{ color: C.gold }}>{pct.toFixed(0)}%</p>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* ── Cumulative P&L chart ───────────────────────────────────────────── */}
      {chartData.length > 1 && (
        <Card className="p-5 mb-8">
          <SectionLabel>Cumulative P&L · {range}d</SectionLabel>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="goldGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={C.gold} stopOpacity={0.28} />
                  <stop offset="95%" stopColor={C.gold} stopOpacity={0}    />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(176,141,79,0.14)" />
              <XAxis dataKey="date" tick={{ fill: C.inkSoft, fontSize: 10, fontFamily: 'Inter' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: C.inkSoft, fontSize: 10, fontFamily: 'Inter' }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} />
              <Tooltip
                contentStyle={{ background: C.surface, border: `1px solid ${C.line}`, borderRadius: 12, fontFamily: 'Inter', fontSize: 12, color: C.ink }}
                labelStyle={{ color: C.inkSoft }}
                formatter={(v: number) => [`$${v.toFixed(2)}`, 'P&L']}
              />
              <Area type="monotone" dataKey="pnl" stroke={C.gold} strokeWidth={2} fill="url(#goldGrad)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* ── Trade log ──────────────────────────────────────────────────────── */}
      <Card className="overflow-hidden mb-8">
        <div style={{ borderBottom: `1px solid ${C.line}` }} className="px-5 py-3 flex items-center justify-between">
          <SectionLabel>Trade Log</SectionLabel>
          {loading && <span style={{ color: C.gold }} className="text-xs font-sans animate-pulse">loading…</span>}
        </div>

        {/* Desktop */}
        <div className="overflow-x-auto hidden md:block">
          <table className="w-full text-sm font-sans">
            <thead>
              <tr style={{ borderBottom: `1px solid ${C.line}` }}>
                {['Date', 'Ticker', 'Status', 'Entry', 'Exit', 'P&L', 'Setup', 'K / D', 'Vol', 'Exit reason'].map(h => (
                  <th key={h} style={{ color: C.inkSoft }} className="px-4 py-2 text-left text-[10px] tracking-[0.15em] uppercase font-semibold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {trades.map((t, i) => (
                <tr key={t.id} style={{ borderBottom: i < trades.length - 1 ? `1px solid rgba(176,141,79,0.1)` : undefined }} className="transition-colors hover:bg-[rgba(176,141,79,0.05)]">
                  <td className="px-4 py-3 whitespace-nowrap" style={{ color: C.inkSoft }}>
                    {format(parseISO(t.date), 'MMM d')}
                    <span className="text-[10px] ml-1.5 opacity-60">{t.time_et}</span>
                  </td>
                  <td className="px-4 py-3 font-semibold" style={{ color: C.ink }}>
                    {t.ticker}
                    {t.deep_curl && <span style={{ color: C.gold }} className="ml-1 text-xs">⭐</span>}
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                  <td className="px-4 py-3" style={{ color: C.ink }}>${t.entry_price?.toFixed(3)}</td>
                  <td className="px-4 py-3" style={{ color: C.inkSoft }}>{t.exit_price ? `$${t.exit_price.toFixed(3)}` : '—'}</td>
                  <td className="px-4 py-3 font-semibold" style={pnlColor(t.realized_pnl)}>
                    {t.realized_pnl !== null ? `${t.realized_pnl >= 0 ? '+' : ''}$${t.realized_pnl.toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-3"><ScoreDots score={t.setup_score ?? 0} max={t.setup_max ?? 5} /></td>
                  <td className="px-4 py-3 text-xs" style={{ color: C.inkSoft }}>{t.k_value?.toFixed(0)} / {t.d_value?.toFixed(0)}</td>
                  <td className="px-4 py-3 text-xs" style={{ color: C.inkSoft }}>{t.vol_ratio?.toFixed(1)}×</td>
                  <td className="px-4 py-3 text-xs max-w-[180px] truncate" style={{ color: C.inkSoft }}>{t.exit_reason ?? t.blockers ?? '—'}</td>
                </tr>
              ))}
              {!loading && trades.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center font-display italic text-lg" style={{ color: C.inkSoft }}>
                    No trades in the last {range} days. The patient win.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile cards */}
        <div className="md:hidden" style={{ borderColor: 'rgba(176,141,79,0.12)' }}>
          {trades.map((t, i) => (
            <div key={t.id} className="p-4" style={{ borderTop: i > 0 ? `1px solid rgba(176,141,79,0.12)` : undefined }}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold" style={{ color: C.ink }}>{t.ticker}</span>
                  {t.deep_curl && <span style={{ color: C.gold }}>⭐</span>}
                  <StatusBadge status={t.status} />
                </div>
                <span className="font-semibold" style={pnlColor(t.realized_pnl)}>
                  {t.realized_pnl !== null ? `${t.realized_pnl >= 0 ? '+' : ''}$${t.realized_pnl.toFixed(2)}` : 'open'}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs" style={{ color: C.inkSoft }}>
                <span>{format(parseISO(t.date), 'MMM d')} {t.time_et}</span>
                <span>in ${t.entry_price?.toFixed(3)}{t.exit_price ? ` → $${t.exit_price.toFixed(3)}` : ''}</span>
                <span>{t.vol_ratio?.toFixed(1)}× vol</span>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <ScoreDots score={t.setup_score ?? 0} max={t.setup_max ?? 5} />
                {t.exit_reason && <span className="text-xs truncate" style={{ color: C.inkSoft }}>{t.exit_reason}</span>}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* ── Self-Audit ─────────────────────────────────────────────────────── */}
      <Card className="p-5">
        <SectionLabel>Daily Strategic Self-Audit</SectionLabel>
        <div className="grid md:grid-cols-3 gap-6 text-sm font-sans">

          {/* Setup quality */}
          <div>
            <p style={{ color: C.ink }} className="text-xs font-semibold tracking-wide uppercase mb-3">Setup Quality</p>
            {[5, 4, 3, 2].map(score => {
              const count = trades.filter(t => t.setup_score === score).length
              const won   = trades.filter(t => t.setup_score === score && (t.realized_pnl ?? 0) > 0).length
              const rate  = count > 0 ? Math.round((won / count) * 100) : null
              return (
                <div key={score} className="flex items-center gap-3 mb-2">
                  <ScoreDots score={score} max={5} />
                  <span style={{ color: C.inkSoft }} className="text-xs">{count} trades</span>
                  {rate !== null && (
                    <span style={{ color: rate >= 70 ? C.win : C.gold }} className="text-xs ml-auto font-semibold">{rate}% win</span>
                  )}
                </div>
              )
            })}
          </div>

          {/* Deep curl */}
          <div>
            <p style={{ color: C.ink }} className="text-xs font-semibold tracking-wide uppercase mb-3">Deep Curl ⭐</p>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span style={{ color: C.ink }}>Deep curl entries</span>
                <span style={{ color: dcRate !== null && (stdRate === null || dcRate > stdRate) ? C.win : C.inkSoft }} className="font-semibold">
                  {dcRate !== null ? `${dcRate}%` : '—'} ({deepCurlTrades.length})
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span style={{ color: C.inkSoft }}>Standard entries</span>
                <span style={{ color: C.inkSoft }}>{stdRate !== null ? `${stdRate}%` : '—'} ({stdTrades.length})</span>
              </div>
              <p style={{ color: C.inkSoft }} className="text-xs mt-3 leading-relaxed">
                {deepCurlTrades.length < 5
                  ? 'Need more data to draw conclusions.'
                  : dcRate !== null && stdRate !== null && dcRate > stdRate
                    ? '⭐ Deep curls are outperforming. Prioritize them.'
                    : 'Deep curls not showing edge yet — keep collecting data.'}
              </p>
            </div>
          </div>

          {/* Exit reasons */}
          <div>
            <p style={{ color: C.ink }} className="text-xs font-semibold tracking-wide uppercase mb-3">Exit Reasons</p>
            <div className="space-y-2">
              {Object.entries(exitReasons).sort(([, a], [, b]) => b - a).slice(0, 6).map(([r, n]) => (
                <div key={r} className="flex justify-between text-xs">
                  <span style={{ color: C.inkSoft }} className="truncate max-w-[160px]">{r}</span>
                  <span style={{ color: C.gold }} className="ml-2 shrink-0 font-semibold">{n}×</span>
                </div>
              ))}
              {Object.keys(exitReasons).length === 0 && (
                <span style={{ color: C.inkSoft }} className="text-xs italic">No closed trades yet.</span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <GoldDivider />
      <p style={{ color: C.inkSoft }} className="text-center text-[10px] tracking-[0.3em] uppercase font-sans">
        Romanticize your discipline &nbsp;·&nbsp; Private &nbsp;·&nbsp; {new Date().getFullYear()}
      </p>

    </div>
  )
}
