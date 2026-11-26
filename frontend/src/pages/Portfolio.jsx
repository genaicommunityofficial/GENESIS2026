import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import useSocket from '../hooks/useSocket'
const money=n=>`₹${Number(n||0).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2})}`
export default function Portfolio(){
 const [data,setData]=useState(null),[msg,setMsg]=useState(''),[busy,setBusy]=useState(false)
 const load=()=>api('/portfolio/me').then(setData).catch(e=>setMsg(e.message))
 useEffect(()=>{load()},[])
 useSocket(message=>{
  if(!message.prices)return
  setData(old=>{
   if(!old)return old
   const positions=old.positions.map(p=>{const current=message.prices[p.symbol]??p.current_price;return {...p,current_price:current,market_value:current*p.quantity,unrealized_pnl:p.quantity*(p.side==='LONG'?current-p.avg_entry_price:p.avg_entry_price-current)}})
   const longs=positions.filter(p=>p.side==='LONG').reduce((n,p)=>n+p.market_value,0)
   const shorts=positions.filter(p=>p.side==='SHORT').reduce((n,p)=>n+p.market_value,0)
   const pnl=positions.reduce((n,p)=>n+p.unrealized_pnl,0)
   return {...old,positions,unrealized_pnl:pnl,net_worth:old.balance+old.collateral_locked+longs-shorts}
  })
 })
 const topup=async()=>{setBusy(true);try{const r=await api('/topup/request',{method:'POST'});setMsg('Top-up request submitted for admin review.')}catch(e){setMsg(e.message)}finally{setBusy(false)}}
 if(!data)return <><div className="eyebrow">Account / portfolio</div><h1>Your portfolio</h1><div className="empty">{msg||'Loading account…'}</div></>
 return <>
  <div className="panel-head" style={{alignItems:'end'}}><div><div className="eyebrow">Account / risk & performance</div><h1>Your portfolio</h1><div className="subtle">Position values update with the live market.</div></div><button className="btn" disabled={busy} onClick={topup}>Request ₹5,000 top-up</button></div>
  {msg&&<div className="notice">{msg}</div>}
  <div className="metric-grid"><Metric label="Net worth" value={money(data.net_worth)} foot={`Starting funds ${money(data.total_credited)}`} /><Metric label="Available cash" value={money(data.balance)} foot="Free cash balance" /><Metric label="Short collateral" value={money(data.collateral_locked)} foot="100% collateralized" /><Metric label="Unrealized P&L" value={money(data.unrealized_pnl)} positive={data.unrealized_pnl>=0} foot="Across open positions" /></div>
  <section className="card panel"><div className="panel-head"><div><div className="eyebrow">Holdings</div><h2 style={{margin:'6px 0'}}>Open positions</h2></div><span className="tag">{data.positions.length} positions</span></div>
   {data.positions.length?<div className="table-wrap"><table><thead><tr><th>Company</th><th>Type</th><th className="text-right">Qty</th><th className="text-right">Avg. entry</th><th className="text-right">Market value</th><th className="text-right">Unrealized P&L</th></tr></thead><tbody>{data.positions.map(p=><tr key={p.symbol}><td><div className="stock-name">{p.name}</div><div className="stock-symbol">{p.symbol} · {p.sector}</div></td><td><span className="tag">{p.side}</span></td><td className="text-right mono">{p.quantity}</td><td className="text-right mono">{money(p.avg_entry_price)}</td><td className="text-right mono">{money(p.market_value)}</td><td className={`text-right mono ${p.unrealized_pnl>=0?'green':'red'}`}>{money(p.unrealized_pnl)}</td></tr>)}</tbody></table></div>:<div className="empty">No open positions yet. Browse the market and place your first order.</div>}
  </section>
  <section className="card panel" style={{marginTop:16}}><div className="panel-head"><div><div className="eyebrow">Activity</div><h2 style={{margin:'6px 0'}}>Recent transactions</h2></div></div>{data.transactions.length?<div className="table-wrap"><table><thead><tr><th>Instrument</th><th>Action</th><th className="text-right">Qty</th><th className="text-right">Price</th><th className="text-right">Realized P&L</th><th>Time</th></tr></thead><tbody>{data.transactions.map((t,i)=><tr key={i}><td className="mono">{t.symbol}</td><td><span className="tag">{t.side}{t.forced?' · forced':''}</span></td><td className="text-right mono">{t.quantity}</td><td className="text-right mono">{money(t.price)}</td><td className={`text-right mono ${t.realized_pnl>=0?'green':'red'}`}>{money(t.realized_pnl)}</td><td className="muted">{new Date(t.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>:<div className="empty">Completed orders will appear here.</div>}</section>
 </>
}
function Metric({label,value,foot,positive}){return <div className="card metric"><div className="metric-label">{label}</div><div className={`metric-value ${positive===undefined?'':positive?'green':'red'}`}>{value}</div><div className="metric-foot">{foot}</div></div>}
