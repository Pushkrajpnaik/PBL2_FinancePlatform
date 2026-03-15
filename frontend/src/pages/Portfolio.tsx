import React, { useState } from 'react';
import { portfolioAPI } from '../services/api';
import toast from 'react-hot-toast';
import { PieChart } from 'lucide-react';
import { PieChart as RechartsPie, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
const COLORS = ['#3b82f6','#22c55e','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#f97316'];
export default function Portfolio() {
  const [form,setForm]=useState({risk_profile:'Moderate',method:'markowitz',investment_amount:1000000});
  const [result,setResult]=useState<any>(null);
  const [allResults,setAllResults]=useState<any>(null);
  const [loading,setLoading]=useState(false);
  const handleOptimize = async () => {
    setLoading(true);
    try{
      const [r1,r2]=await Promise.all([portfolioAPI.optimize(form),portfolioAPI.optimizeAll(form)]);
      setResult(r1.data); setAllResults(r2.data);
      toast.success('Portfolio optimized!');
    }catch(err:any){toast.error('Optimization failed');}
    finally{setLoading(false);}
  };
  const pieData = result ? Object.entries(result.allocation).map(([k,v]:any)=>({name:k.replace(/_/g,' '),value:v})) : [];
  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold text-white flex items-center gap-2"><PieChart className="text-green-500"/> Portfolio Optimizer</h1><p className="text-slate-400 mt-1">AI-powered portfolio optimization using 4 algorithms</p></div>
      <div className="card">
        <h3 className="font-semibold text-white mb-4">Configure Portfolio</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div><label className="label">Risk Profile</label>
            <select className="input-field" value={form.risk_profile} onChange={e=>setForm({...form,risk_profile:e.target.value})}>
              <option>Conservative</option><option>Moderate</option><option>Aggressive</option>
            </select>
          </div>
          <div><label className="label">Method</label>
            <select className="input-field" value={form.method} onChange={e=>setForm({...form,method:e.target.value})}>
              <option value="markowitz">Markowitz</option><option value="risk_parity">Risk Parity</option><option value="cvar">CVaR</option><option value="black_litterman">Black-Litterman</option>
            </select>
          </div>
          <div><label className="label">Investment Amount (₹)</label>
            <input type="number" className="input-field" value={form.investment_amount} onChange={e=>setForm({...form,investment_amount:Number(e.target.value)})}/>
          </div>
        </div>
        <button onClick={handleOptimize} disabled={loading} className="btn-primary mt-4">{loading?'Optimizing...':'Optimize Portfolio'}</button>
      </div>
      {result&&(
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Allocation Chart</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsPie><Pie data={pieData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({name,value})=>`${name} ${value}%`}>
                {pieData.map((_:any,i:number)=><Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
              </Pie><Tooltip/></RechartsPie>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Results</h3>
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-slate-400">Method</span><span className="text-white font-medium">{result.method}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Expected Return</span><span className="text-green-400 font-medium">{result.expected_return}%</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Expected Risk</span><span className="text-yellow-400 font-medium">{result.expected_risk}%</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Sharpe Ratio</span><span className="text-blue-400 font-medium">{result.sharpe_ratio}</span></div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-700">
              <p className="text-slate-400 text-sm mb-2">Allocated Amounts</p>
              {result.allocated_amounts&&Object.entries(result.allocated_amounts).map(([k,v]:any)=>(
                <div key={k} className="flex justify-between text-sm mb-1"><span className="text-slate-300 capitalize">{k.replace(/_/g,' ')}</span><span className="text-white">₹{v.toLocaleString()}</span></div>
              ))}
            </div>
          </div>
        </div>
      )}
      {allResults&&(
        <div className="card">
          <h3 className="font-semibold text-white mb-4">Algorithm Comparison</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {['markowitz','risk_parity','cvar','black_litterman'].map(m=>{
              const r=allResults[m];
              const isRecommended=allResults.recommended?.method===r?.method;
              return r?(
                <div key={m} className={`p-4 rounded-lg border ${isRecommended?'border-green-500/50 bg-green-500/5':'border-slate-700 bg-slate-700/50'}`}>
                  {isRecommended&&<span className="badge-green mb-2 block">Recommended</span>}
                  <p className="text-white font-medium text-sm capitalize">{m.replace(/_/g,' ')}</p>
                  <p className="text-green-400 text-sm mt-1">Return: {r.expected_return}%</p>
                  <p className="text-yellow-400 text-sm">Risk: {r.expected_risk}%</p>
                  <p className="text-blue-400 text-sm">Sharpe: {r.sharpe_ratio}</p>
                </div>
              ):null;
            })}
          </div>
        </div>
      )}
    </div>
  );
}
