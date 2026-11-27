import { useEffect, useMemo, useState } from 'react'
import useSocket from '../hooks/useSocket'
import StockTable from '../components/StockTable'
import OrderModal from '../components/OrderModal'
import PriceChart from '../components/PriceChart'
import { api } from '../lib/api'

const money = n => `₹${Number(n || 0).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2})}`
export default function Trading() {
  const [stocks, setStocks] = useState([]), [selected, setSelected] = useState(null), [portfolio, setPortfolio] = useState(null), [marketOpen,setMarketOpen]=useState(false), [notice,setNotice]=useState('')
  const refresh = () => { api('/stocks').then(setStocks).catch(e=>setNotice(e.message)); api('/portfolio/me').then(setPortfolio).catch(()=>{}) }
  useEffect(() => { refresh(); fetch('/api/health').then(r=>r.json()).then(v=>setMarketOpen(v.market_open)).catch(()=>{}) }, [])
  const connected = useSocket(m => {
    if (m.prices) setStocks(prev => prev.map(s => ({...s,price:m.prices[s.symbol] ?? s.price})))
    if (m.type==='MARKET_STATUS') setMarketOpen(m.open)
    if (m.type==='ERA_TRIGGERED') setNotice(`Scenario applied: ${m.scenario}`)
  })
  const selectedSymbol = selected?.startsWith('ORDER:') ? selected.slice(6) : selected
  const stock = useMemo(()=>stocks.find(s=>s.symbol===selectedSymbol),[stocks,selectedSymbol])
  return <>
    <div className="panel-head" style={{alignItems:'end'}}><div><div className="eyebrow">Participant terminal / live pricing</div><h1>Market overview</h1><div className="subtle">Trade the GENESIS 2026 company universe at real time simulation prices.</div></div><div className="status-pill"><span className={`dot ${connected?'':'off'}`} />{connected?'Live connection':'Reconnecting'}</div></div>
    {notice && <div className="notice">{notice}<button className="btn small" style={{float:'right'}} onClick={()=>setNotice('')}>Dismiss</button></div>}
    {!marketOpen && <div className="notice">Trading is paused by the event administrator. Prices and your portfolio remain available.</div>}
    <div className="metric-grid">
      <Metric label="Net worth" value={money(portfolio?.net_worth)} foot={`${Number(portfolio?.net_worth/25000*100-100||0).toFixed(2)}% overall return`} />
      <Metric label="Available cash" value={money(portfolio?.balance)} foot="Unreserved buying power" />
      <Metric label="Locked collateral" value={money(portfolio?.collateral_locked)} foot="Reserved against short positions" />
      <Metric label="Open positions" value={portfolio?.positions?.length ?? '—'} foot={`${stocks.length || 30} listed companies`} />
    </div>
    <div className="market-grid">
      <section className="card panel"><StockTable stocks={stocks} onSelect={s=>setSelected(s.symbol)} /></section>
      <aside className="card panel">
        <div className="eyebrow">Selected instrument</div>
        {stock ? <>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'start',marginTop:7}}><div><h2 style={{marginBottom:3}}>{stock.name}</h2><span className="mono muted">{stock.symbol} · {stock.sector}</span></div><span className="tag">{stock.pe_ratio ? `${stock.pe_ratio}× P/E` : 'Growth'}</span></div>
          <div className="metric-value" style={{marginTop:18}}>{money(stock.price)}</div>
          <div className="subtle">Reference price {money(stock.anchor_price)}</div>
          <PriceChart symbol={stock.symbol} price={stock.price} />
          <button className="btn primary" style={{width:'100%',marginTop:8}} disabled={!marketOpen} onClick={()=>setSelected(`ORDER:${stock.symbol}`)}>Place an order</button>
        </> : <div className="empty">Choose a company from the market list to view its live chart and place an order.</div>}
      </aside>
    </div>
    {selected?.startsWith('ORDER:') && stock && <OrderModal stock={stock} onClose={()=>setSelected(stock.symbol)} onFilled={refresh} />}
  </>
}
function Metric({label,value,foot}) { return <div className="card metric"><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-foot">{foot}</div></div> }
