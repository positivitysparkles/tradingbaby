'use client'

import { useEffect, useState, useCallback } from 'react'
import { createClient } from '@supabase/supabase-js'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { format, parseISO, subDays } from 'date-fns'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
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

// ── Design tokens (inline so Tailwind JIT picks them up) ──────────────────────
const C = {
  gold:     '#c9a96e',
  goldDim:  '#8b6e3c',
  rose:     '#c4789b',
  cream:    '#f0ebe0',
  taupe:    '#7a6a5a',
  bg:       '#080807',
  card:     '#141210',
  border:   'rgba(201,169,110,0.14)',
  win:      '#6aad8a',
  loss:     '#c06060',
}

function pnlColor(v: number | null) {
  if (v === null) return 'text-[#7a6a5a]'
  return v >= 0 ? 'text-[#6aad8a]' : 'text-[#c06060]'
}

function ScoreDots({ score, max }: { score: number; max: number }) {
  return (
    <span className="flex gap-1 items-center">
      {Array.from({ length: max }).map((_, i) => (
        <span
          key={i}
          style={{ background: i < score ? C.gold : 'rgba(201,169,110,0.15)' }}
          className="w-1.5 h-1.5 rounded-full inline-block"
        />
      ))}
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; text: string; border: string }> = {
    open:    { bg: 'rgba(196,120,155,0.1)', text: C.rose,   border: 'rgba(196,120,155,0.25)' },
    closed:  { bg: 'rgba(201,169,110,0.08)', text: C.taupe, border: 'rgba(201,169,110,0.2)' },
    stopped: { bg: 'rgba(192,96,96,0.1)',   text: C.loss,   border: 'rgba(192,96,96,0.25)' },
  }
  const s = map[status] ?? map.closed
  return (
    <span
      style={{ background: s.bg, color: s.text, border: `1px solid ${s.border}` }}
      className="text-[10px] px-2 py-0.5 rounded-full font-medium tracking-wider uppercase"
    >
      {status}
    </span>
  )
}

function GoldDivider() {
  return (
    <div className="flex items-center gap-3 my-6">
      <div style={{ background: `linear-gradient(to right, transparent, ${C.goldDim})` }} className="flex-1 h-px" />
      <span style={{ color: C.gold }} className="text-xs tracking-[0.3em] uppercase">✦</span>
      <div style={{ background: `linear-gradient(to left, transparent, ${C.goldDim})` }} className="flex-1 h-px" />
    </div>
  )
}

function KpiCard({ label, value, sub, color }: {
  label: string; value: string; sub: string; color: string
}) {
  return (
    <div
      style={{ background: C.card, border: `1px solid ${C.border}` }}
      className="rounded-2xl p-5 flex flex-col gap-1"
    >
      <p style={{ color: C.taupe }} className="text-[10px] tracking-[0.25em] uppercase font-sans font-medium">
        {label}
      </p>
      <p style={{ color }} className="font-display text-3xl font-semibold leading-none mt-1">
        {value}
      </p>
      <p style={{ color: C.taupe }} className="text-xs font-sans mt-1">{sub}</p>
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

  // ── Audit helpers ──────────────────────────────────────────────────────────
  const deepCurlTrades = closed.filter(t => t.deep_curl)
  const dcWins   = deepCurlTrades.filter(t => (t.realized_pnl ?? 0) > 0).length
  const dcRate   = deepCurlTrades.length ? Math.round((dcWins / deepCurlTrades.length) * 100) : null
  const stdTrades = closed.filter(t => !t.deep_curl)
  const stdWins  = stdTrades.filter(t => (t.realized_pnl ?? 0) > 0).length
  const stdRate  = stdTrades.length ? Math.round((stdWins / stdTrades.length) * 100) : null

  const exitReasons: Record<string, number> = {}
  closed.forEach(t => {
    const k = t.exit_reason ?? 'unknown'
    exitReasons[k] = (exitReasons[k] ?? 0) + 1
  })

  return (
    <div
      style={{ background: C.bg }}
      className="min-h-screen text-[#f0ebe0] px-4 py-10 md:px-10 max-w-6xl mx-auto"
    >

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header className="mb-2">
        <div className="flex items-start justify-between">
          <div>
            <p style={{ color: C.gold, letterSpacing: '0.3em' }} className="text-[10px] uppercase font-sans mb-2">
              W118 · Curl if Flow · Private
            </p>
            <h1 className="font-display text-5xl md:text-6xl font-semibold leading-none" style={{ color: C.cream }}>
              <span style={{ color: C.gold }} className="italic">Olya&rsquo;s</span> Dashboard
            </h1>
          </div>

          {/* Range + refresh */}
          <div className="flex items-center gap-2 mt-2">
            {([7, 30, 90] as const).map(r => (
              <button
                key={r}
                onClick={() => setRange(r)}
                style={{
                  background: range === r ? C.gold : 'transparent',
                  color:      range === r ? C.bg   : C.taupe,
                  border:     `1px solid ${range === r ? C.gold : C.border}`,
                }}
                className="px-3 py-1 rounded-full text-xs font-sans transition-all duration-200 hover:border-gold"
              >
                {r}d
              </button>
            ))}
            <button
              onClick={load}
              style={{ color: C.taupe, border: `1px solid ${C.border}` }}
              className="px-3 py-1 rounded-full text-xs font-sans hover:opacity-80 transition-opacity"
            >
              ↻
            </button>
          </div>
        </div>

        {/* Quote */}
        <p
          style={{ color: C.taupe, borderLeft: `2px solid ${C.goldDim}` }}
          className="font-display italic text-base md:text-lg mt-4 pl-4"
        >
          She doesn&rsquo;t chase. She builds.
        </p>
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

      {/* ── Cumulative P&L chart ───────────────────────────────────────────── */}
      {chartData.length > 1 && (
        <div
          style={{ background: C.card, border: `1px solid ${C.border}` }}
          className="rounded-2xl p-5 mb-8"
        >
          <p style={{ color: C.taupe }} className="text-[10px] tracking-[0.25em] uppercase font-sans mb-4">
            Cumulative P&L · {range}d
          </p>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="goldGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={C.gold} stopOpacity={0.25} />
                  <stop offset="95%" stopColor={C.gold} stopOpacity={0}    />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(201,169,110,0.07)" />
              <XAxis
                dataKey="date"
                tick={{ fill: C.taupe, fontSize: 10, fontFamily: 'Inter' }}
                axisLine={false} tickLine={false}
              />
              <YAxis
                tick={{ fill: C.taupe, fontSize: 10, fontFamily: 'Inter' }}
                axisLine={false} tickLine={false}
                tickFormatter={v => `$${v}`}
              />
              <Tooltip
                contentStyle={{
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  borderRadius: 12,
                  fontFamily: 'Inter',
                  fontSize: 12,
                }}
                labelStyle={{ color: C.taupe }}
                formatter={(v: number) => [`$${v.toFixed(2)}`, 'P&L']}
              />
              <Area
                type="monotone"
                dataKey="pnl"
                stroke={C.gold}
                strokeWidth={1.5}
                fill="url(#goldGrad)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Trade log ──────────────────────────────────────────────────────── */}
      <div
        style={{ background: C.card, border: `1px solid ${C.border}` }}
        className="rounded-2xl overflow-hidden mb-8"
      >
        <div
          style={{ borderBottom: `1px solid ${C.border}` }}
          className="px-5 py-3 flex items-center justify-between"
        >
          <p style={{ color: C.taupe }} className="text-[10px] tracking-[0.25em] uppercase font-sans">
            Trade Log
          </p>
          {loading && (
            <span style={{ color: C.gold }} className="text-xs font-sans animate-pulse">
              loading…
            </span>
          )}
        </div>

        {/* Desktop */}
        <div className="overflow-x-auto hidden md:block">
          <table className="w-full text-sm font-sans">
            <thead>
              <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                {['Date', 'Ticker', 'Status', 'Entry', 'Exit', 'P&L', 'Setup', 'K / D', 'Vol', 'Exit reason'].map(h => (
                  <th
                    key={h}
                    style={{ color: C.taupe }}
                    className="px-4 py-2 text-left text-[10px] tracking-[0.2em] uppercase font-medium"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {trades.map((t, i) => (
                <tr
                  key={t.id}
                  style={{
                    borderBottom: i < trades.length - 1 ? `1px solid rgba(201,169,110,0.06)` : undefined,
                  }}
                  className="transition-colors hover:bg-[rgba(201,169,110,0.03)]"
                >
                  <td className="px-4 py-3 whitespace-nowrap" style={{ color: C.taupe }}>
                    {format(parseISO(t.date), 'MMM d')}
                    <span className="text-[10px] ml-1.5 opacity-50">{t.time_et}</span>
                  </td>
                  <td className="px-4 py-3 font-semibold" style={{ color: C.cream }}>
                    {t.ticker}
                    {t.deep_curl && <span style={{ color: C.gold }} className="ml-1 text-xs">⭐</span>}
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                  <td className="px-4 py-3" style={{ color: C.cream }}>${t.entry_price?.toFixed(3)}</td>
                  <td className="px-4 py-3" style={{ color: C.taupe }}>
                    {t.exit_price ? `$${t.exit_price.toFixed(3)}` : '—'}
                  </td>
                  <td className={`px-4 py-3 font-semibold ${pnlColor(t.realized_pnl)}`}>
                    {t.realized_pnl !== null
                      ? `${t.realized_pnl >= 0 ? '+' : ''}$${t.realized_pnl.toFixed(2)}`
                      : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <ScoreDots score={t.setup_score ?? 0} max={t.setup_max ?? 5} />
                  </td>
                  <td className="px-4 py-3 text-xs" style={{ color: C.taupe }}>
                    {t.k_value?.toFixed(0)} / {t.d_value?.toFixed(0)}
                  </td>
                  <td className="px-4 py-3 text-xs" style={{ color: C.taupe }}>
                    {t.vol_ratio?.toFixed(1)}×
                  </td>
                  <td className="px-4 py-3 text-xs max-w-[180px] truncate" style={{ color: C.taupe }}>
                    {t.exit_reason ?? t.blockers ?? '—'}
                  </td>
                </tr>
              ))}
              {!loading && trades.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center font-display italic text-lg" style={{ color: C.taupe }}>
                    No trades in the last {range} days.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile cards */}
        <div className="md:hidden divide-y" style={{ borderColor: 'rgba(201,169,110,0.08)' }}>
          {trades.map(t => (
            <div key={t.id} className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold" style={{ color: C.cream }}>{t.ticker}</span>
                  {t.deep_curl && <span style={{ color: C.gold }}>⭐</span>}
                  <StatusBadge status={t.status} />
                </div>
                <span className={`font-semibold ${pnlColor(t.realized_pnl)}`}>
                  {t.realized_pnl !== null
                    ? `${t.realized_pnl >= 0 ? '+' : ''}$${t.realized_pnl.toFixed(2)}`
                    : 'open'}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs" style={{ color: C.taupe }}>
                <span>{format(parseISO(t.date), 'MMM d')} {t.time_et}</span>
                <span>in ${t.entry_price?.toFixed(3)}{t.exit_price ? ` → $${t.exit_price.toFixed(3)}` : ''}</span>
                <span>{t.vol_ratio?.toFixed(1)}× vol</span>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <ScoreDots score={t.setup_score ?? 0} max={t.setup_max ?? 5} />
                {t.exit_reason && (
                  <span className="text-xs truncate" style={{ color: C.taupe }}>{t.exit_reason}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Self-Audit ─────────────────────────────────────────────────────── */}
      <div
        style={{ background: C.card, border: `1px solid ${C.border}` }}
        className="rounded-2xl p-5"
      >
        <p style={{ color: C.taupe }} className="text-[10px] tracking-[0.25em] uppercase font-sans mb-4">
          Self-Audit
        </p>

        <div className="grid md:grid-cols-3 gap-6 text-sm font-sans">

          {/* Setup quality */}
          <div>
            <p style={{ color: C.gold }} className="text-xs tracking-wider uppercase mb-3">
              Setup Quality
            </p>
            {[5, 4, 3, 2].map(score => {
              const count = trades.filter(t => t.setup_score === score).length
              const won   = trades.filter(t => t.setup_score === score && (t.realized_pnl ?? 0) > 0).length
              const rate  = count > 0 ? Math.round((won / count) * 100) : null
              return (
                <div key={score} className="flex items-center gap-3 mb-2">
                  <ScoreDots score={score} max={5} />
                  <span style={{ color: C.taupe }} className="text-xs">{count} trades</span>
                  {rate !== null && (
                    <span style={{ color: rate >= 70 ? C.win : C.gold }} className="text-xs ml-auto">
                      {rate}% win
                    </span>
                  )}
                </div>
              )
            })}
          </div>

          {/* Deep curl */}
          <div>
            <p style={{ color: C.gold }} className="text-xs tracking-wider uppercase mb-3">
              Deep Curl ⭐
            </p>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span style={{ color: C.cream }}>Deep curl entries</span>
                <span style={{ color: dcRate !== null && (stdRate === null || dcRate > stdRate) ? C.gold : C.taupe }}>
                  {dcRate !== null ? `${dcRate}%` : '—'} ({deepCurlTrades.length})
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span style={{ color: C.taupe }}>Standard entries</span>
                <span style={{ color: C.taupe }}>
                  {stdRate !== null ? `${stdRate}%` : '—'} ({stdTrades.length})
                </span>
              </div>
              <p style={{ color: C.taupe }} className="text-xs mt-3 leading-relaxed">
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
            <p style={{ color: C.gold }} className="text-xs tracking-wider uppercase mb-3">
              Exit Reasons
            </p>
            <div className="space-y-2">
              {Object.entries(exitReasons)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 6)
                .map(([r, n]) => (
                  <div key={r} className="flex justify-between text-xs">
                    <span style={{ color: C.taupe }} className="truncate max-w-[160px]">{r}</span>
                    <span style={{ color: C.goldDim }} className="ml-2 shrink-0">{n}×</span>
                  </div>
                ))}
              {Object.keys(exitReasons).length === 0 && (
                <span style={{ color: C.taupe }} className="text-xs italic">No closed trades yet.</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <GoldDivider />
      <p
        style={{ color: C.taupe }}
        className="text-center text-[10px] tracking-[0.3em] uppercase font-sans"
      >
        Romanticize your discipline &nbsp;·&nbsp; Private &nbsp;·&nbsp; {new Date().getFullYear()}
      </p>

    </div>
  )
}
