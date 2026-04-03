import { useState, useEffect, useMemo } from 'react'
import { Package, RefreshCw, Download, TrendingUp, Layers, BarChart2, AlertCircle } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer
} from 'recharts'

// ---------------------------------------------------------------------------
// Sample data (used when backend is not running)
// ---------------------------------------------------------------------------
const SAMPLE_DATA = [
  { id:1, source:'Amazon FBA',         sku:'SKU-001', product_name:'Wireless Earbuds Pro',  quantity:320, location:'Amazon FBA Warehouse',  scraped_at:'2024-03-01T10:00:00Z' },
  { id:2, source:'Amazon FBA',         sku:'SKU-002', product_name:'Phone Stand Deluxe',     quantity:85,  location:'Amazon FBA Warehouse',  scraped_at:'2024-03-01T10:00:00Z' },
  { id:3, source:'Amazon FBA',         sku:'SKU-003', product_name:'USB-C Hub 7-in-1',       quantity:142, location:'Amazon FBA Warehouse',  scraped_at:'2024-03-01T10:00:00Z' },
  { id:4, source:'TikTok FBT',         sku:'SKU-001', product_name:'Wireless Earbuds Pro',  quantity:210, location:'TikTok Warehouse',       scraped_at:'2024-03-01T10:00:00Z' },
  { id:5, source:'TikTok FBT',         sku:'SKU-002', product_name:'Phone Stand Deluxe',     quantity:60,  location:'TikTok Warehouse',       scraped_at:'2024-03-01T10:00:00Z' },
  { id:6, source:'LogicPod / QuickBox',sku:'SKU-001', product_name:'Wireless Earbuds Pro',  quantity:500, location:'Warehouse A - Shelf 3',  scraped_at:'2024-03-01T10:00:00Z' },
  { id:7, source:'LogicPod / QuickBox',sku:'SKU-002', product_name:'Phone Stand Deluxe',     quantity:200, location:'Warehouse A - Shelf 7',  scraped_at:'2024-03-01T10:00:00Z' },
  { id:8, source:'LogicPod / QuickBox',sku:'SKU-003', product_name:'USB-C Hub 7-in-1',       quantity:310, location:'Warehouse B - Shelf 2',  scraped_at:'2024-03-01T10:00:00Z' },
  { id:9, source:'Amazon FBA',         sku:'SKU-001', product_name:'Wireless Earbuds Pro',  quantity:290, location:'Amazon FBA Warehouse',  scraped_at:'2024-03-08T10:00:00Z' },
  { id:10,source:'TikTok FBT',         sku:'SKU-001', product_name:'Wireless Earbuds Pro',  quantity:175, location:'TikTok Warehouse',       scraped_at:'2024-03-08T10:00:00Z' },
  { id:11,source:'LogicPod / QuickBox',sku:'SKU-001', product_name:'Wireless Earbuds Pro',  quantity:480, location:'Warehouse A - Shelf 3',  scraped_at:'2024-03-08T10:00:00Z' },
]

// ---------------------------------------------------------------------------
// Color palette per channel
// ---------------------------------------------------------------------------
const CHANNEL_COLORS = {
  'Amazon FBA':          '#f59e0b',
  'TikTok FBT':          '#6366f1',
  'LogicPod / QuickBox': '#10b981',
}
const FALLBACK_COLORS = ['#4f6ef7','#f43f5e','#8b5cf6','#06b6d4','#84cc16']

function channelColor(source, index = 0) {
  return CHANNEL_COLORS[source] ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length]
}

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------
function fmt(n) { return Number(n).toLocaleString() }

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function KPICard({ icon: Icon, label, value, sub, color = 'brand' }) {
  const bg = { brand:'bg-brand-500', amber:'bg-amber-500', emerald:'bg-emerald-500', violet:'bg-violet-500' }
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100 flex items-start gap-4">
      <div className={`${bg[color]} p-3 rounded-xl text-white shrink-0`}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-slate-800 mt-0.5">{value}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

function FilterPill({ label, options, value, onChange }) {
  return (
    <div className="flex flex-col gap-1 min-w-[160px]">
      <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</label>
      <select
        multiple
        value={value}
        onChange={e => onChange([...e.target.selectedOptions].map(o => o.value))}
        className="border border-slate-200 rounded-xl px-3 py-2 text-sm bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500 h-24"
      >
        {options.map(o => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
      <button
        onClick={() => onChange(options)}
        className="text-xs text-brand-500 hover:underline text-left"
      >
        Select all
      </button>
    </div>
  )
}

function SectionCard({ title, children }) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
      <h2 className="text-sm font-semibold text-slate-700 mb-4 uppercase tracking-wide">{title}</h2>
      {children}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main App
// ---------------------------------------------------------------------------

export default function App() {
  const [data, setData]           = useState([])
  const [loading, setLoading]     = useState(true)
  const [scraping, setScraping]   = useState(false)
  const [usingMock, setUsingMock] = useState(false)
  const [lastScrape, setLastScrape] = useState(null)

  // filters
  const [selChannels, setSelChannels] = useState([])
  const [selSKUs, setSelSKUs]         = useState([])
  const [startDate, setStartDate]     = useState('')
  const [endDate, setEndDate]         = useState('')

  // ---- data fetching ----
  async function fetchData() {
    setLoading(true)
    try {
      const res = await fetch('/api/inventory')
      if (!res.ok) throw new Error('no backend')
      const json = await res.json()
      setData(json.records ?? [])
      setUsingMock(false)
    } catch {
      setData(SAMPLE_DATA)
      setUsingMock(true)
    } finally {
      setLoading(false)
    }
  }

  async function triggerScrape() {
    setScraping(true)
    try {
      await fetch('/api/scrape', { method: 'POST' })
      await fetchData()
    } catch {
      // backend not running — just refresh mock
      await fetchData()
    } finally {
      setScraping(false)
      setLastScrape(new Date())
    }
  }

  async function triggerExport() {
    try {
      const res = await fetch('/api/export')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'inventory.xlsx'; a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert('Export requires the Python backend to be running.')
    }
  }

  useEffect(() => { fetchData() }, [])

  // ---- derive filter options ----
  const allChannels = useMemo(() => [...new Set(data.map(r => r.source))].sort(), [data])
  const allSKUs     = useMemo(() => [...new Set(data.map(r => r.sku))].sort(), [data])
  const allDates    = useMemo(() => data.map(r => r.scraped_at?.slice(0,10)).filter(Boolean).sort(), [data])

  useEffect(() => { if (allChannels.length && !selChannels.length) setSelChannels(allChannels) }, [allChannels])
  useEffect(() => { if (allSKUs.length && !selSKUs.length)         setSelSKUs(allSKUs) }, [allSKUs])
  useEffect(() => {
    if (allDates.length && !startDate) setStartDate(allDates[0])
    if (allDates.length && !endDate)   setEndDate(allDates[allDates.length - 1])
  }, [allDates])

  // ---- filtered data ----
  const filtered = useMemo(() => data.filter(r =>
    selChannels.includes(r.source) &&
    selSKUs.includes(r.sku) &&
    (!startDate || r.scraped_at?.slice(0,10) >= startDate) &&
    (!endDate   || r.scraped_at?.slice(0,10) <= endDate)
  ), [data, selChannels, selSKUs, startDate, endDate])

  // ---- latest snapshot ----
  const latestTs      = useMemo(() => filtered.reduce((m,r) => r.scraped_at > m ? r.scraped_at : m, ''), [filtered])
  const latestSnap    = useMemo(() => filtered.filter(r => r.scraped_at === latestTs), [filtered, latestTs])
  const totalUnits    = useMemo(() => latestSnap.reduce((s,r) => s + (r.quantity||0), 0), [latestSnap])

  // ---- chart data: inventory by channel (latest) ----
  const byChannel = useMemo(() => {
    const map = {}
    latestSnap.forEach(r => { map[r.source] = (map[r.source]||0) + (r.quantity||0) })
    return Object.entries(map).map(([source, quantity]) => ({ source, quantity }))
  }, [latestSnap])

  // ---- chart data: inventory by SKU grouped by channel (latest) ----
  const bySKU = useMemo(() => {
    const map = {}
    latestSnap.forEach(r => {
      if (!map[r.sku]) map[r.sku] = { sku: r.sku }
      map[r.sku][r.source] = (map[r.sku][r.source]||0) + (r.quantity||0)
    })
    return Object.values(map)
  }, [latestSnap])

  // ---- chart data: time series ----
  const timeSeries = useMemo(() => {
    const map = {}
    filtered.forEach(r => {
      const day = r.scraped_at?.slice(0,10) ?? 'unknown'
      if (!map[day]) map[day] = { date: day }
      map[day][r.source] = (map[day][r.source]||0) + (r.quantity||0)
    })
    return Object.values(map).sort((a,b) => a.date.localeCompare(b.date))
  }, [filtered])

  // ---- table: sorted newest first ----
  const tableRows = useMemo(() =>
    [...filtered].sort((a,b) => (b.scraped_at??'').localeCompare(a.scraped_at??'')),
  [filtered])

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="flex flex-col items-center gap-3">
        <RefreshCw className="animate-spin text-brand-500" size={32} />
        <p className="text-slate-500 font-medium">Loading inventory…</p>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-50">
      {/* ── Top nav ── */}
      <header className="bg-white border-b border-slate-100 px-8 py-4 flex items-center justify-between sticky top-0 z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="bg-brand-500 p-2 rounded-xl">
            <Package className="text-white" size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-800 leading-none">Inventory Dashboard</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              {lastScrape ? `Last scraped ${lastScrape.toLocaleTimeString()}` : (usingMock ? 'Showing sample data — connect backend to see live data' : `${filtered.length} records loaded`)}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={triggerScrape}
            disabled={scraping}
            className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium px-4 py-2 rounded-xl transition disabled:opacity-60"
          >
            <RefreshCw size={15} className={scraping ? 'animate-spin' : ''} />
            {scraping ? 'Scraping…' : 'Scrape now'}
          </button>
          <button
            onClick={triggerExport}
            className="flex items-center gap-2 border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-medium px-4 py-2 rounded-xl transition"
          >
            <Download size={15} />
            Export Excel
          </button>
        </div>
      </header>

      {usingMock && (
        <div className="mx-8 mt-4 flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-3 rounded-xl">
          <AlertCircle size={16} />
          <span>Backend not detected — displaying sample data. Run <code className="font-mono bg-amber-100 px-1 rounded">python api.py</code> to connect live data.</span>
        </div>
      )}

      <main className="px-8 py-6 max-w-screen-2xl mx-auto space-y-6">

        {/* ── KPI cards ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard icon={Package}    label="Total Units"       value={fmt(totalUnits)}        sub="latest snapshot"  color="brand"   />
          <KPICard icon={Layers}     label="SKUs Tracked"      value={allSKUs.length}         sub="unique SKUs"       color="violet"  />
          <KPICard icon={BarChart2}  label="Channels"          value={allChannels.length}     sub="connected"         color="amber"   />
          <KPICard icon={TrendingUp} label="Snapshots"         value={[...new Set(data.map(r=>r.scraped_at))].length} sub="total runs" color="emerald" />
        </div>

        {/* ── Filters ── */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <h2 className="text-sm font-semibold text-slate-700 mb-4 uppercase tracking-wide">Filters</h2>
          <div className="flex flex-wrap gap-6 items-start">
            <FilterPill label="Channel" options={allChannels} value={selChannels} onChange={setSelChannels} />
            <FilterPill label="SKU"     options={allSKUs}     value={selSKUs}     onChange={setSelSKUs}     />
            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Date range</label>
              <div className="flex items-center gap-2">
                <input type="date" value={startDate} onChange={e=>setStartDate(e.target.value)}
                  className="border border-slate-200 rounded-xl px-3 py-2 text-sm bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500" />
                <span className="text-slate-400 text-sm">to</span>
                <input type="date" value={endDate} onChange={e=>setEndDate(e.target.value)}
                  className="border border-slate-200 rounded-xl px-3 py-2 text-sm bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500" />
              </div>
            </div>
          </div>
        </div>

        {/* ── Charts row 1 ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          <SectionCard title="Current stock by channel">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={byChannel} barCategoryGap="30%">
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="source" tick={{ fontSize:12, fill:'#64748b' }} />
                <YAxis tick={{ fontSize:12, fill:'#64748b' }} />
                <Tooltip formatter={v => fmt(v)} contentStyle={{ borderRadius:12, border:'1px solid #e2e8f0', boxShadow:'0 4px 6px -1px rgb(0 0 0/0.1)' }} />
                <Bar dataKey="quantity" radius={[6,6,0,0]} label={{ position:'top', fontSize:11, fill:'#64748b', formatter: v => fmt(v) }}>
                  {byChannel.map((entry, i) => (
                    <Cell key={entry.source} fill={channelColor(entry.source, i)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </SectionCard>

          <SectionCard title="Stock distribution by channel">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={byChannel} dataKey="quantity" nameKey="source" cx="50%" cy="50%" innerRadius={65} outerRadius={100} paddingAngle={3} label={({ source, percent }) => `${source} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                  {byChannel.map((entry, i) => (
                    <Cell key={entry.source} fill={channelColor(entry.source, i)} />
                  ))}
                </Pie>
                <Tooltip formatter={v => fmt(v)} contentStyle={{ borderRadius:12, border:'1px solid #e2e8f0' }} />
              </PieChart>
            </ResponsiveContainer>
          </SectionCard>
        </div>

        {/* ── Chart: by SKU grouped by channel ── */}
        <SectionCard title="Current stock by SKU & channel">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={bySKU} barCategoryGap="25%" barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="sku" tick={{ fontSize:12, fill:'#64748b' }} />
              <YAxis tick={{ fontSize:12, fill:'#64748b' }} />
              <Tooltip formatter={v => fmt(v)} contentStyle={{ borderRadius:12, border:'1px solid #e2e8f0', boxShadow:'0 4px 6px -1px rgb(0 0 0/0.1)' }} />
              <Legend wrapperStyle={{ fontSize:13 }} />
              {selChannels.map((ch, i) => (
                <Bar key={ch} dataKey={ch} fill={channelColor(ch, i)} radius={[4,4,0,0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </SectionCard>

        {/* ── Chart: time series ── */}
        {timeSeries.length > 1 && (
          <SectionCard title="Inventory over time by channel">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={timeSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize:12, fill:'#64748b' }} />
                <YAxis tick={{ fontSize:12, fill:'#64748b' }} />
                <Tooltip formatter={v => fmt(v)} contentStyle={{ borderRadius:12, border:'1px solid #e2e8f0' }} />
                <Legend wrapperStyle={{ fontSize:13 }} />
                {selChannels.map((ch, i) => (
                  <Line key={ch} type="monotone" dataKey={ch} stroke={channelColor(ch, i)} strokeWidth={2} dot={{ r:4 }} activeDot={{ r:6 }} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </SectionCard>
        )}

        {/* ── Raw data table ── */}
        <SectionCard title={`All records (${tableRows.length})`}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  {['Date','Channel','SKU','Product','Quantity','Location'].map(h => (
                    <th key={h} className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wide pb-3 pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableRows.slice(0, 100).map(row => (
                  <tr key={row.id} className="border-b border-slate-50 hover:bg-slate-50 transition">
                    <td className="py-3 pr-4 text-slate-500 text-xs font-mono">{row.scraped_at?.slice(0,16).replace('T',' ')}</td>
                    <td className="py-3 pr-4">
                      <span className="inline-flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: channelColor(row.source) }} />
                        <span className="text-slate-700 font-medium">{row.source}</span>
                      </span>
                    </td>
                    <td className="py-3 pr-4 font-mono text-slate-600">{row.sku}</td>
                    <td className="py-3 pr-4 text-slate-700 max-w-[220px] truncate">{row.product_name}</td>
                    <td className="py-3 pr-4 text-slate-800 font-semibold">{fmt(row.quantity)}</td>
                    <td className="py-3 pr-4 text-slate-500 text-xs">{row.location}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {tableRows.length > 100 && (
              <p className="text-xs text-slate-400 mt-3 text-center">Showing first 100 of {tableRows.length} records</p>
            )}
          </div>
        </SectionCard>

      </main>
    </div>
  )
}
