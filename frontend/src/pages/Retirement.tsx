import React, { useState } from 'react';
import { retirementAPI } from '../services/api';
import toast from 'react-hot-toast';
import { Sunset } from 'lucide-react';
export default function Retirement() {
  const [form,setForm]=useState({current_age:25,retirement_age:60,current_monthly_expenses:40000,expected_inflation_rate:6.0,existing_savings:500000,life_expectancy:85,risk_profile:'Moderate'});
  const [result,setResult]=useState<any>(null);
  const [loading,setLoading]=useState(false);
  const handleCalculate = async () => {
    setLoading(true);
    try{ const res=await retirementAPI.calculate(form); setResult(res.data); toast.success('Retirement plan calculated!'); }
    catch(err:any){ toast.error('Calculation failed'); }
    finally{ setLoading(false); }
  };
  const handleSave = async () => {
    try{ await retirementAPI.save(form); toast.success('Retirement plan saved!'); }
    catch(err:any){ toast.error('Save failed'); }
  };
  return (
    <div className="space-y-6 max-w-4xl">
      <div><h1 className="text-2xl font-bold text-white flex items-center gap-2"><Sunset className="text-purple-500"/> Retirement Planner</h1><p className="text-slate-400 mt-1">Calculate your retirement corpus and monthly SIP requirement</p></div>
      <div className="card">
        <h3 className="font-semibold text-white mb-4">Your Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label className="label">Current Age</label><input type="number" className="input-field" value={form.current_age} onChange={e=>setForm({...form,current_age:Number(e.target.value)})}/></div>
          <div><label className="label">Retirement Age</label><input type="number" className="input-field" value={form.retirement_age} onChange={e=>setForm({...form,retirement_age:Number(e.target.value)})}/></div>
          <div><label className="label">Monthly Expenses (₹)</label><input type="number" className="input-field" value={form.current_monthly_expenses} onChange={e=>setForm({...form,current_monthly_expenses:Number(e.target.value)})}/></div>
          <div><label className="label">Existing Savings (₹)</label><input type="number" className="input-field" value={form.existing_savings} onChange={e=>setForm({...form,existing_savings:Number(e.target.value)})}/></div>
          <div><label className="label">Inflation Rate (%)</label><input type="number" className="input-field" value={form.expected_inflation_rate} onChange={e=>setForm({...form,expected_inflation_rate:Number(e.target.value)})}/></div>
          <div><label className="label">Life Expectancy</label><input type="number" className="input-field" value={form.life_expectancy} onChange={e=>setForm({...form,life_expectancy:Number(e.target.value)})}/></div>
          <div><label className="label">Risk Profile</label>
            <select className="input-field" value={form.risk_profile} onChange={e=>setForm({...form,risk_profile:e.target.value})}>
              <option>Conservative</option><option>Moderate</option><option>Aggressive</option>
            </select>
          </div>
        </div>
        <div className="flex gap-3 mt-4">
          <button onClick={handleCalculate} disabled={loading} className="btn-primary">{loading?'Calculating...':'Calculate Plan'}</button>
          {result&&<button onClick={handleSave} className="btn-secondary">Save Plan</button>}
        </div>
      </div>
      {result&&(
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card"><p className="text-slate-400 text-sm">Required Corpus</p><p className="text-xl font-bold text-white mt-1">₹{(result.results?.required_corpus/10000000).toFixed(2)}Cr</p></div>
            <div className="card"><p className="text-slate-400 text-sm">Monthly SIP Required</p><p className="text-xl font-bold text-white mt-1">₹{result.results?.required_monthly_sip?.toLocaleString()}</p></div>
            <div className="card"><p className="text-slate-400 text-sm">Future Monthly Expense</p><p className="text-xl font-bold text-white mt-1">₹{result.results?.future_monthly_expense?.toLocaleString()}</p></div>
            <div className="card"><p className="text-slate-400 text-sm">Success Probability</p><p className="text-xl font-bold text-green-400 mt-1">{result.results?.corpus_achievement_probability}%</p></div>
          </div>
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Corpus Growth Milestones</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-slate-400 border-b border-slate-700"><th className="text-left py-2">Age</th><th className="text-left py-2">Years Invested</th><th className="text-left py-2">Projected Corpus</th><th className="text-left py-2">Phase</th></tr></thead>
                <tbody>
                  {result.milestones?.map((m:any)=>(
                    <tr key={m.age} className="border-b border-slate-700/50">
                      <td className="py-2 text-white">{m.age}</td>
                      <td className="py-2 text-slate-300">{m.years_invested} yrs</td>
                      <td className="py-2 text-green-400">₹{(m.projected_corpus/100000).toFixed(1)}L</td>
                      <td className="py-2"><span className="badge-blue capitalize">{m.phase?.replace(/_/g,' ')}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="card">
            <h3 className="font-semibold text-white mb-3">Recommendation</h3>
            <p className={`font-semibold ${result.recommendation?.color==='green'?'text-green-400':result.recommendation?.color==='red'?'text-red-400':'text-yellow-400'}`}>{result.recommendation?.status}</p>
            <p className="text-slate-400 text-sm mt-1">{result.recommendation?.message}</p>
          </div>
        </div>
      )}
    </div>
  );
}
