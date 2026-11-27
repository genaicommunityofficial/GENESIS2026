import { useState } from 'react'
import { api } from '../lib/api'
const money = n => `₹${Number(n||0).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2})}`
export default function OrderModal({ stock, onClose, onFilled }) {
  const [qty,setQty]=useState(1),[action,setAction]=useState('BUY'),[msg,setMsg]=useState(''),[busy,setBusy]=useState(false)
  const submit=async()=>{setBusy(true);setMsg('');try{const r=await api('/trade/order',{method:'POST',body:{company_id:stock.id,action,qty:Number(qty)}});setMsg(`Filled ${r.quantity} ${stock.symbol} at ${money(r.price)}.`);onFilled?.()}catch(e){setMsg(e.message)}finally{setBusy(false)}}
  return <div className="modal-backdrop" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><div className="card modal">
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'start'}}><div><div className="eyebrow">Instant dealer execution</div><h2 style={{margin:'6px 0'}}>{stock.symbol} order</h2><div className="subtle">{stock.name}</div></div><button className="btn small" onClick={onClose}>Close</button></div>
    <div className="action-tabs">{['BUY','SELL','SHORT','COVER'].map(a=><button className={action===a?'active':''} key={a} onClick={()=>setAction(a)}>{a}</button>)}</div>
    <label className="form-grid"><span className="muted" style={{fontSize:11}}>Quantity · max 40 shares per company</span><input type="number" min="1" max="40" value={qty} onChange={e=>setQty(Math.max(1,Math.min(40,Number(e.target.value)||1)))} /></label>
    <div className="card" style={{padding:13,margin:'13px 0',background:'#101914'}}><div className="subtle">Execution price</div><div className="mono" style={{marginTop:5}}>{money(stock.price)} / share</div><div className="subtle" style={{marginTop:10}}>{action==='SHORT'?'100% cash collateral reserved':action==='COVER'?'Collateral released and P&L settled':'Estimated order value'} <b style={{float:'right',color:'#eaf0ec'}}>{money(stock.price*qty)}</b></div></div>
    {msg&&<div className={`notice ${msg.startsWith('Filled')?'success':'error'}`}>{msg}</div>}
    <button className="btn primary" style={{width:'100%'}} disabled={busy} onClick={submit}>{busy?'Executing…':`Confirm ${action.toLowerCase()}`}</button>
    <p className="subtle" style={{fontSize:10,lineHeight:1.5,margin:'11px 0 0'}}>Orders fill immediately when the market is open. Long purchases are subject to the 35% concentration limit.</p>
  </div></div>
}
