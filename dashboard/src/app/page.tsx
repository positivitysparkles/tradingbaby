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

function pnlColor(v: number | null) {
  if (v === null) return 'text-slate-400'
  return v >= 0 ? 'text-green-400' : 'text-red-400'
}

function ScoreDots({ score, max }: { score: number; max: number }) {
  return (
    <span className="flex gap-1 items-center">
      {Array.from({ length: max }).map((_, i) => (
        <span
          key={i}
          className={`w-2 h-2 rounded-full ${i < score ? 'bg-violet-400' : 'bg-slate-700'}`}
        />
      ))}
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    open:    'bg-blue-900/60 text-blue-300 border border-blue-700',
    closed:  'bg-slate-800 text-slate-300 border border-slate-600',
    stopped: 'bg-red-900/60 text-red-300 border border-red-700',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${map[status] ?? map.closed}`}>
      {status}
    </span>
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

  // ── Derived stats ─────────────────────────────────────────────────────────
  const closed   = trades.filter(t => t.status !== 'open' && t.realized_pnl !== null)
  const open     = trades.filter(t => t.status === 'open')
  const netPnl   = closed.reduce((s, t) => s + (t.realized_pnl ?? 0), 0)
  const wins     = closed.filter(t => (t.realized_pnl ?? 0) > 0).length
  const winRate  = closed.length ? Math.round((wins / closed.length) * 100) : 0
  const avgWin   = wins ? closed.filter(t => (t.realized_pnl ?? 0) > 0).reduce((s, t) => s + (t.realized_pnl ?? 0), 0) / wins : 0
  const losers   = closed.filter(t => (t.realized_pnl ?? 0) < 0)
  const avgLoss  = losers.length ? losers.reduce((s, t) => s + (t.realized_pnl ?? 0), 0) / losers.length : 0
  const deepCurls = trades.filter(t => t.deep_curl).length

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

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-200 p-4 md:p-8 max-w-6xl mx-auto">

      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            W118 <span className="text-violet-400">Curl if Flow</span>
          </h1>
          <p className="text-slate-500 text-sm mt-0.5">Private P&L Dashboard</p>
        </div>
        <div className="flex gap-2">
          {([7, 30, 90] as const).map(r => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                range === r
                  ? 'bg-violet-700 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {r}d
            </button>
          ))}
          <button
            onClick={load}
            className="px-3 py-1 rounded text-sm bg-slate-800 text-slate-400 hover:bg-slate-700 transition-colors ml-2"
          >
            ↻
          </button>
        </div>
      </div>

      {/* ── KPI cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          {
            label: 'Net P&L',
            value: `${netPnl >= 0 ? '+' : ''}$${netPnl.toFixed(2)}`,
            color: netPnl >= 0 ? 'text-green-400' : 'text-red-400',
            sub: `${closed.length} closed trades`,
          },
          {
            label: 'Win Rate',
            value: `${winRate}%`,
            color: winRate >= 60 ? 'text-green-400' : winRate >= 40 ? 'text-yellow-400' : 'text-red-400',
            sub: `${wins}W / ${losers.length}L`,
          },
          {
            label: 'Avg Win',
            value: `+$${avgWin.toFixed(2)}`,
            color: 'text-green-400',
            sub: `Avg Loss: $${avgLoss.toFixed(2)}`,
          },
          {
            label: 'Open Now',
            value: `${open.length}`,
            color: 'text-blue-400',
            sub: `${deepCurls} deep curls total`,
          },
        ].map(card => (
          <div key={card.label} className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">{card.label}</p>
            <p className={`text-2xl font-semibold ${card.color}`}>{card.value}</p>
            <p className="text-xs text-slate-500 mt-1">{card.sub}</p>
          </div>
        ))}
      </div>

      {/* ── Cumulative P&L chart ── */}
      {chartData.length > 1 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 mb-8">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-4">Cumulative P&L</p>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#7c3aed" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#7c3aed" stopOpacity={0}   />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                     tickFormatter={v => `$${v}`} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }}
                labelStyle={{ color: '#94a3b8' }}
                formatter={(v: number) => [`$${v.toFixed(2)}`, 'P&L']}
              />
              <Area type="monotone" dataKey="pnl" stroke="#7c3aed" strokeWidth={2}
                    fill="url(#pnlGrad)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Trade table ── */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
          <p className="text-xs text-slate-500 uppercase tracking-wider">Trade Log</p>
          {loading && <span className="text-xs text-violet-400 animate-pulse">loading…</span>}
        </div>

        {/* Desktop table */}
        <div className="overflow-x-auto hidden md:block">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-500 border-b border-slate-800">
                {['Date', 'Ticker', 'Status', 'Entry', 'Exit', 'P&L', 'Setup', 'K/D', 'Vol', 'Notes'].map(h => (
                  <th key={h} className="px-3 py-2 text-left font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {trades.map(t => (
                <tr key={t.id} className="border-b border-slate-800/50 hover:bg-slate-800/40 transition-colors">
                  <td className="px-3 py-2.5 text-slate-400 whitespace-nowrap">
                    {format(parseISO(t.date), 'MMM d')}
                    <span className="text-slate-600 text-xs ml-1">{t.time_et}</span>
                  </td>
                  <td className="px-3 py-2.5 font-semibold text-white">
                    {t.ticker}
                    {t.deep_curl && <span className="ml-1 text-yellow-400">⭐</span>}
                  </td>
                  <td className="px-3 py-2.5"><StatusBadge status={t.status} /></td>
                  <td className="px-3 py-2.5 text-slate-300">${t.entry_price?.toFixed(3)}</td>
                  <td className="px-3 py-2.5 text-slate-300">
                    {t.exit_price ? `$${t.exit_price.toFixed(3)}` : '—'}
                  </td>
                  <td className={`px-3 py-2.5 font-semibold ${pnlColor(t.realized_pnl)}`}>
                    {t.realized_pnl !== null
                      ? `${t.realized_pnl >= 0 ? '+' : ''}$${t.realized_pnl.toFixed(2)}`
                      : '—'}
                  </td>
                  <td className="px-3 py-2.5">
                    <ScoreDots score={t.setup_score ?? 0} max={t.setup_max ?? 5} />
                  </td>
                  <td className="px-3 py-2.5 text-slate-400">
                    {t.k_value?.toFixed(0)}/{t.d_value?.toFixed(0)}
                  </td>
                  <td className="px-3 py-2.5 text-slate-400">
                    {t.vol_ratio?.toFixed(1)}x
                  </td>
                  <td className="px-3 py-2.5 text-slate-500 text-xs max-w-[160px] truncate">
                    {t.exit_reason ?? t.blockers ?? '—'}
                  </td>
                </tr>
              ))}
              {!loading && trades.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-3 py-8 text-center text-slate-600">
                    No trades in the last {range} days.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile cards */}
        <div className="md:hidden divide-y divide-slate-800">
          {trades.map(t => (
            <div key={t.id} className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white">{t.ticker}</span>
                  {t.deep_curl && <span className="text-yellow-400">⭐</span>}
                  <StatusBadge status={t.status} />
                </div>
                <span className={`font-semibold ${pnlColor(t.realized_pnl)}`}>
                  {t.realized_pnl !== null
                    ? `${t.realized_pnl >= 0 ? '+' : ''}$${t.realized_pnl.toFixed(2)}`
                    : 'open'}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-500">
                <span>{format(parseISO(t.date), 'MMM d')} {t.time_et}</span>
                <span>in ${t.entry_price?.toFixed(3)}{t.exit_price ? ` → $${t.exit_price.toFixed(3)}` : ''}</span>
                <span>{t.vol_ratio?.toFixed(1)}x vol</span>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <ScoreDots score={t.setup_score ?? 0} max={t.setup_max ?? 5} />
                {t.exit_reason && (
                  <span className="text-xs text-slate-600 truncate">{t.exit_reason}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Self-audit section ── */}
      <div className="mt-8 bg-slate-900/80 border border-slate-800 rounded-xl p-4">
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Self-Audit Notes</p>
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-slate-400 mb-2 font-medium">Setup Quality</p>
            {[5, 4, 3].map(score => {
              const count = trades.filter(t => t.setup_score === score).length
              const won   = trades.filter(t => t.setup_score === score && (t.realized_pnl ?? 0) > 0).length
              return (
                <div key={score} className="flex items-center gap-2 mb-1 text-xs">
                  <ScoreDots score={score} max={5} />
                  <span className="text-slate-500">{count} trades</span>
                  {count > 0 && <span className="text-green-500">{won}W</span>}
                </div>
              )
            })}
          </div>
          <div>
            <p className="text-slate-400 mb-2 font-medium">Deep Curl Performance</p>
            {(() => {
              const dc     = closed.filter(t => t.deep_curl)
              const dcWins = dc.filter(t => (t.realized_pnl ?? 0) > 0).length
              const dcRate = dc.length ? Math.round((dcWins / dc.length) * 100) : 0
              const ndc    = closed.filter(t => !t.deep_curl)
              const ndcW   = ndc.filter(t => (t.realized_pnl ?? 0) > 0).length
              const ndcRate= ndc.length ? Math.round((ndcW / ndc.length) * 100) : 0
              return (
                <div className="text-xs text-slate-400 space-y-1">
                  <div className="flex justify-between">
                    <span>⭐ Deep curl</span>
                    <span className="text-yellow-400">{dcRate}% win ({dc.length} trades)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Standard</span>
                    <span className="text-slate-300">{ndcRate}% win ({ndc.length} trades)</span>
                  </div>
                  <p className="text-slate-600 mt-2">
                    {dc.length < 5 ? 'Need more data to draw conclusions.' :
                     dcRate > ndcRate ? '⭐ Deep curls outperforming — consider prioritizing.' :
                     'Deep curls not showing edge yet.'}
                  </p>
                </div>
              )
            })()}
          </div>
          <div>
            <p className="text-slate-400 mb-2 font-medium">Exit Reasons</p>
            {(() => {
              const reasons: Record<string, number> = {}
              closed.forEach(t => {
                const k = t.exit_reason ?? 'unknown'
                reasons[k] = (reasons[k] ?? 0) + 1
              })
              return (
                <div className="text-xs text-slate-400 space-y-1">
                  {Object.entries(reasons)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 5)
                    .map(([r, n]) => (
                      <div key={r} className="flex justify-between">
                        <span className="truncate max-w-[160px]">{r}</span>
                        <span className="text-slate-500 ml-2">{n}×</span>
                      </div>
                    ))}
                  {Object.keys(reasons).length === 0 && (
                    <span className="text-slate-600">No closed trades yet.</span>
                  )}
                </div>
              )
            })()}
          </div>
        </div>
      </div>

      <p className="text-center text-slate-700 text-xs mt-8">
        W118 · Private · {new Date().getFullYear()}
      </p>
    </div>
  )
}
