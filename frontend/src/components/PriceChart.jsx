import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts'

export default function PriceChart({ symbol, price }) {
  const [hist, setHist] = useState([])
  useEffect(() => { setHist([]) }, [symbol])
  useEffect(() => { if (price) setHist(h => [...h.slice(-120), { t: h.length, price }]) }, [price])
  return <div style={{ height: 240 }}><ResponsiveContainer>
    <LineChart data={hist} margin={{top:8,right:8,bottom:0,left:0}}><CartesianGrid stroke="#24342d" vertical={false} /><XAxis dataKey="t" hide /><YAxis domain={['auto', 'auto']} width={48} tick={{fill:'#78877f',fontSize:9}} tickFormatter={v=>`₹${v}`} axisLine={false} tickLine={false} />
      <Tooltip contentStyle={{background:'#101914',border:'1px solid #304238',borderRadius:8,color:'#eaf0ec'}} formatter={v=>[`₹${Number(v).toFixed(2)}`,'Price']} labelFormatter={()=>symbol} /><Line dataKey="price" dot={false} type="monotone" stroke="#b6ef67" strokeWidth={2} activeDot={{r:3,fill:'#b6ef67'}} /></LineChart></ResponsiveContainer></div>
}
