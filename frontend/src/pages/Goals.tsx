import React, { useState, useEffect } from 'react';
import { goalsAPI } from '../services/api';
import toast from 'react-hot-toast';
import { Target, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
export default function Goals() {
  const [form,setForm]=useState({goal_type:'home_purchase',target_amount:5000000,current_savings:500000,monthly_investment:25000,time_horizon_years:7,inflation_rate:6.0,risk_profile:'Moderate'});
  const [result,setResult]=useState<any>(null);
  const [templates,setTemplates]=useState<any[]>([]);
  const [loading,setLoading]=useState(false);
  useEffect(()=>{ goalsAPI.getTemplates().then(r=>setTemplates(r.data.templates)).catch(()=>{}); },[]);
  const handleAnalyze = async () => {
    setLoading(true);
    try{ const res=await goalsAPI.analyze(form); setResult(res.data); toast.success('Goal analyzed!'); }
    catch(err:any){ toast.error('Analysis failed'); }
    finally{ setLoading(false); }
  };
  const handleSave = async () => {
    try{ await goalsAPI.save(form); toast.success('Goal saved!'); }
    catch(err:any){ toast.error('Save failed'); }
  };
  const statusIcon:any={
    'On Track':<CheckCircle className="text-green-400" size={20}/>,
    'Needs Attention':<AlertTriangle className="text-yellow-400" size={20}/>,
    'At Risk':<XCircle className="text-red-400" size={20}/>,
  };
  return (
    <div className="space-y-6 max-w-4xl">
      <div><h1 className="text-2xl font-bold text-white flex items-center gap-2"><Target className="text-yellow-500"/> Goal-Based Investment Planner</h1><p className="text-slate-400 mt-1">Plan and track your financial goals with Monte Carlo simulation</p></div>
      <div className="card">
        <h3 className="font-semibold text-white mb-4">Configure Your Goal</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label className="label">Goal Type</label>
            <select className="input-field" value={form.goal_type} onChange={e=>setForm({...form,goal_type:e.target.value})}>
              {templates.map(t=><option key={t.goal_type} value={t.goal_type}>{t.icon} {t.name}</option>)}
            </select>
          </div>
          <div><label className="label">Risk Profile</label>
            <select className="input-field" value={form.risk_profile} onChange={e=>setForm({...form,risk_profile:e.target.value})}>
              <option>Conservative</option><option>Moderate</option><option>Aggressive</option>
            </select>
          </div>
          <div><label className="label">Target Amount (₹)</label><input type="number" className="input-field" value={form.target_amount} onChange={e=>setForm({...form,target_amount:Number(e.target.value)})}/></div>
          <div><label className="label">Current Savings (₹)</label><input type="number" className="input-field" value={form.current_savings} onChange={e=>setForm({...form,current_savings:Number(e.target.value)})}/></div>
          <div><label className="label">Monthly Investment (₹)</label><input type="number" className="input-field" value={form.monthly_investment} onChange={e=>setForm({...form,monthly_investment:Number(e.target.value)})}/></div>
          <div><label className="label">Time Horizon (Years)</label><input type="number" className="input-field" value={form.time_horizon_years} onChange={e=>setForm({...form,time_horizon_years:Number(e.target.value)})}/></div>
          <div><label className="label">Inflation Rate (%)</label><input type="number" className="input-field" value={form.inflation_rate} onChange={e=>setForm({...form,inflation_rate:Number(e.target.value)})}/></div>
        </div>
        <div className="flex gap-3 mt-4">
          <button onClick={handleAnalyze} disabled={loading} className="btn-primary">{loading?'Analyzing...':'Analyze Goal'}</button>
          {result&&<button onClick={handleSave} className="btn-secondary">Save Goal</button>}
        </div>
      </div>
      {result&&(
        <div className="space-y-4">
          <div className={`card border ${result.recommendation?.color==='green'?'border-green-500/30 bg-green-500/5':result.recommendation?.color==='red'?'border-red-500/30 bg-red-500/5':'border-yellow-500/30 bg-yellow-500/5'}`}>
            <div className="flex items-center gap-3 mb-4">
              {statusIcon[result.recommendation?.status]}
              <h3 className="font-semibold text-white">{result.recommendation?.status}</h3>
            </div>
            <p className="text-slate-300 text-sm">{result.recommendation?.message}</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card"><p className="text-slate-400 text-sm">Success Probability</p><p className="text-2xl font-bold text-white mt-1">{result.success_probability}%</p></div>
            <div className="card"><p className="text-slate-400 text-sm">Required SIP</p><p className="text-2xl font-bold text-white mt-1">₹{result.required_sip?.toLocaleString()}</p></div>
            <div className="card"><p className="text-slate-400 text-sm">Inflation Adjusted Target</p><p className="text-2xl font-bold text-white mt-1">₹{result.inflation_adjusted_target?.toLocaleString()}</p></div>
            <div className="card"><p className="text-slate-400 text-sm">Shortfall Risk</p><p className="text-2xl font-bold text-red-400 mt-1">{result.shortfall_risk}%</p></div>
          </div>
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Monte Carlo Scenarios (10,000 simulations)</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-red-500/10 rounded-lg"><p className="text-slate-400 text-sm">Worst Case</p><p className="text-red-400 text-xl font-bold mt-1">₹{result.monte_carlo?.worst_case?.toLocaleString()}</p></div>
              <div className="text-center p-4 bg-blue-500/10 rounded-lg"><p className="text-slate-400 text-sm">Median</p><p className="text-blue-400 text-xl font-bold mt-1">₹{result.monte_carlo?.median?.toLocaleString()}</p></div>
              <div className="text-center p-4 bg-green-500/10 rounded-lg"><p className="text-slate-400 text-sm">Best Case</p><p className="text-green-400 text-xl font-bold mt-1">₹{result.monte_carlo?.best_case?.toLocaleString()}</p></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
