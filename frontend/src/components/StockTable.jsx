import { useMemo, useState } from 'react'
const money = n => `₹${Number(n||0).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2})}`
export default function StockTable({ stocks, onSelect }) {
  const [query,setQuery]=useState(''),[sector,setSector]=useState('All')
  const sectors=['All',...new Set(stocks.map(s=>s.sector))]
  const visible=useMemo(()=>stocks.filter(s=>(sector==='All'||s.sector===sector)&&`${s.symbol} ${s.name} ${s.sector}`.toLowerCase().includes(query.toLowerCase())),[stocks,query,sector])
  return <>
    <div className="panel-head"><div><div className="eyebrow">Exchange / equities</div><h2 style={{margin:'6px 0'}}>Listed companies <span className="muted" style={{fontSize:12}}>({stocks.length})</span></h2></div><input className="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search ticker or name" /></div>
    <div className="filters">{sectors.map(s=><button key={s} onClick={()=>setSector(s)} className={`chip ${s===sector?'active':''}`}>{s==='All'?'All sectors':s}</button>)}</div>
    <div className="table-wrap"><table><thead><tr><th>Company</th><th>Sector</th><th className="text-right">Last price</th><th className="text-right">Change</th><th></th></tr></thead><tbody>
      {visible.map(s=>{const change=(s.price/s.anchor_price-1)*100;return <tr key={s.symbol} onClick={()=>onSelect(s)} style={{cursor:'pointer'}}><td><div className="stock-name">{s.name}</div><div className="stock-symbol">{s.symbol}</div></td><td><span className="tag">{s.sector}</span></td><td className="text-right mono">{money(s.price)}</td><td className={`text-right mono ${change>=0?'green':'red'}`}>{change>=0?'+':''}{change.toFixed(2)}%</td><td className="text-right"><button className="btn small">View</button></td></tr>})}
      {!visible.length&&<tr><td colSpan="5" className="empty">No companies match this search.</td></tr>}
    </tbody></table></div>
  </>
}
