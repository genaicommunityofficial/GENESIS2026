import { useEffect, useState } from 'react'
import { api } from '../lib/api'
const money=n=>`₹${Number(n||0).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2})}`
export default function Leaderboard(){
 const [data,setData]=useState({rankings:[],frozen:false}),[error,setError]=useState('')
 useEffect(()=>{let active=true;const load=()=>api('/leaderboard').then(v=>active&&setData(v)).catch(e=>active&&setError(e.message));load();const t=setInterval(load,5000);return()=>{active=false;clearInterval(t)}},[])
 return <>
  <div className="panel-head" style={{alignItems:'end'}}><div><div className="eyebrow">Competition / standings</div><h1>Leaderboard</h1><div className="subtle">Ranked by portfolio net worth, including open positions and collateral.</div></div><span className="status-pill"><span className={`dot ${data.frozen?'off':''}`} />{data.frozen?'Final standings locked':'Live standings'}</span></div>
  {data.frozen&&<div className="notice">The leaderboard has been frozen by the event administrator. Participant view shows the final snapshot.</div>}{error&&<div className="notice error">{error}</div>}
  <section className="card panel"><div className="table-wrap"><table><thead><tr><th>Rank</th><th>Participant</th><th className="text-right">Net worth</th><th className="text-right">Return</th><th className="text-right">P&L</th></tr></thead><tbody>
   {data.rankings.map(r=><tr key={r.rank}><td><span className={`tag ${r.rank===1?'':'muted'}`}>#{r.rank}</span></td><td><strong>{r.name}</strong></td><td className="text-right mono">{money(r.net_worth)}</td><td className={`text-right mono ${r.pnl_pct>=0?'green':'red'}`}>{r.pnl_pct>=0?'+':''}{Number(r.pnl_pct).toFixed(2)}%</td><td className={`text-right mono ${r.pnl>=0?'green':'red'}`}>{money(r.pnl)}</td></tr>)}
   {!data.rankings.length&&<tr><td colSpan="5" className="empty">Standings will appear once participant wallets are active.</td></tr>}
  </tbody></table></div></section>
 </>
}
