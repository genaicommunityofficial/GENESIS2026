import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { api, getRole, getToken } from '../lib/api'

export default function Login() {
  const [mode,setMode]=useState('login'),[f,setF]=useState({full_name:'',reg_number:'',email:'',password:''}),[msg,setMsg]=useState(''),[busy,setBusy]=useState(false)
  const nav=useNavigate()
  if(getToken()) return <Navigate to={getRole()==='ADMIN'?'/admin':'/'} replace />
  const submit=async e=>{e.preventDefault();setBusy(true);setMsg('');try{if(mode==='register'){const r=await api('/auth/register',{method:'POST',body:f});setMsg(r.message);setMode('login')}else{const r=await api('/auth/login',{method:'POST',body:{email:f.email,password:f.password}});localStorage.setItem('token',r.token);localStorage.setItem('role',r.role);localStorage.setItem('name',r.name||'');nav(r.role==='ADMIN'?'/admin':'/')}}catch(e){setMsg(e.message)}finally{setBusy(false)}}
  const change=e=>setF({...f,[e.target.name]:e.target.value})
  return <div className="login-layout">
    <section className="login-copy"><div className="brand"><span className="brand-mark">G</span><span>GENESIS<small>VIRTUAL EXCHANGE / 2026</small></span></div><div className="eyebrow" style={{marginTop:62}}>The student trading floor</div><h1>Think in eras.<br/><span className="green">Trade the future.</span></h1><p>A live market simulation across 30 fictional companies and 10 macroeconomic eras. Build your portfolio, manage risk, and see where you rank.</p><div className="metric-grid" style={{gridTemplateColumns:'repeat(3,1fr)',maxWidth:490}}><Mini value="30" label="Companies"/><Mini value="10" label="Market eras"/><Mini value="₹25K" label="Starting capital"/></div></section>
    <section className="card login-card"><div className="eyebrow">Welcome to GENESIS</div><h2 style={{fontSize:24,margin:'8px 0 18px'}}>{mode==='login'?'Sign in to your account':'Create participant account'}</h2>
      <form className="form-grid" onSubmit={submit}>
        {mode==='register'&&<><label>Full name<input name="full_name" required minLength="2" value={f.full_name} onChange={change} placeholder="Your name" /></label><label>Registration number<input name="reg_number" required value={f.reg_number} onChange={change} placeholder="University registration no." /></label></>}
        <label>Email address<input name="email" type="email" required value={f.email} onChange={change} placeholder="you@university.edu" /></label>
        <label>Password<input name="password" type="password" required minLength="8" value={f.password} onChange={change} placeholder="At least 8 characters" /></label>
        {msg&&<div className={`notice ${msg.includes('submitted')?'success':'error'}`}>{msg}</div>}
        <button className="btn primary" type="submit" disabled={busy}>{busy?'Please wait…':mode==='login'?'Sign in':'Submit registration'}</button>
      </form>
      <div className="subtle" style={{textAlign:'center',marginTop:18}}>{mode==='login'?"New to the event? ":'Already registered? '}<button style={{color:'#b6ef67',background:'none',border:0}} onClick={()=>{setMode(mode==='login'?'register':'login');setMsg('')}}>{mode==='login'?'Create an account':'Sign in'}</button></div>
      {mode==='register'&&<p className="subtle" style={{fontSize:10,lineHeight:1.5,margin:'17px 0 0'}}>Participant accounts require administrator approval before trading access is enabled.</p>}
    </section>
  </div>
}
function Mini({value,label}){return <div><div className="metric-value" style={{fontSize:19}}>{value}</div><div className="metric-label" style={{fontSize:8}}>{label}</div></div>}
