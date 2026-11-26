import { NavLink, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { lazy, Suspense, useEffect, useState } from 'react'
import { getRole, getToken, api } from './lib/api'

const Login = lazy(() => import('./pages/Login'))
const Trading = lazy(() => import('./pages/Trading'))
const Portfolio = lazy(() => import('./pages/Portfolio'))
const Leaderboard = lazy(() => import('./pages/Leaderboard'))
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'))

function Guard({ role, children }) {
  return getToken() && (!role || getRole() === role) ? children : <Navigate to="/login" replace />
}

function Layout({ children }) {
  const nav = useNavigate(), path = useLocation()
  const [marketOpen, setMarketOpen] = useState(false)
  useEffect(() => { api('/health').then(v => setMarketOpen(v.market_open)).catch(() => {}) }, [path.pathname])
  const admin = getRole() === 'ADMIN'
  const logout = () => { localStorage.clear(); nav('/login') }
  return <main className="app-shell">
    <header className="topbar">
      <a className="brand" href={admin ? '/admin' : '/'}><span className="brand-mark">G</span><span>GENESIS<small>VIRTUAL EXCHANGE / 2026</small></span></a>
      <nav className="nav">
        {admin ? <><NavLink to="/admin">Control room</NavLink><NavLink to="/leaderboard">Leaderboard</NavLink></> : <><NavLink end to="/">Markets</NavLink><NavLink to="/portfolio">Portfolio</NavLink><NavLink to="/leaderboard">Leaderboard</NavLink></>}
        <button onClick={logout}>Sign out</button>
      </nav>
      <div className="status-pill"><span className={`dot ${marketOpen ? '' : 'off'}`} />{marketOpen ? 'Market open' : 'Market paused'}</div>
    </header>
    {children}
  </main>
}

function Screen({ children }) { return <Guard><Layout>{children}</Layout></Guard> }
export default function App() {
  return <Suspense fallback={<main className="app-shell"><div className="eyebrow">GENESIS 2026</div><div className="empty">Loading workspace…</div></main>}><Routes>
    <Route path="/login" element={<Login />} />
    <Route path="/" element={<Screen><Guard role="PARTICIPANT"><Trading /></Guard></Screen>} />
    <Route path="/portfolio" element={<Screen><Guard role="PARTICIPANT"><Portfolio /></Guard></Screen>} />
    <Route path="/leaderboard" element={<Screen><Leaderboard /></Screen>} />
    <Route path="/admin" element={<Screen><Guard role="ADMIN"><AdminDashboard /></Guard></Screen>} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></Suspense>
}
