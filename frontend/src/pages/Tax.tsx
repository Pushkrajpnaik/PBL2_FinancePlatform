import React, { useState } from 'react';
import { taxAPI } from '../services/api';
import toast from 'react-hot-toast';
import { Receipt } from 'lucide-react';
export default function Tax() {
  const [activeTab,setActiveTab]=useState('capital_gains');
  const [cgForm,setCgForm]=useState({asset_type:'equity',purchase_price:100000,sale_price:150000,holding_days:400,annual_income:1200000,tax_regime:'new_regime'});
  const [s80cForm,setS80cForm]=useState({annual_income:1200000,current_investments:{elss:50000,ppf:30000},tax_regime:'old_regime'});
  const [cgResult,setCgResult]=useState<any>(null);
  const [s80cResult,setS80cResult]=useState<any>(null);
  const [loading,setLoading]=useState(false);
  const calcCG = async () => {
    setLoading(true);
    try{ const res=await taxAPI.capitalGains(cgForm); setCgResult(res.data); toast.success('Tax calculated!'); }
    catch(err:any){ toast.error('Calculation failed'); }
    finally{ setLoading(false); }
  };
  const calc80C = async () => {
    setLoading(true);
    try{ const res=await taxAPI.optimize80c(s80cForm); setS80cResult(res.data); toast.success('80C optimized!'); }
    catch(err:any){ toast.error('Optimization failed'); }
    finally{ setLoading(false); }
  };
  const tabs=[{id:'capital_gains',label:'Capital Gains'},{id:'80c',label:'Section 80C'}];
  return (
    <div className="space-y-6 max-w-4xl">
      <div><h1 className="text-2xl font-bold text-white flex items-center gap-2"><Receipt className="text-red-500"/> Tax Optimizer</h1><p className="text-slate-400 mt-1">Minimize your tax liability legally</p></div>
      <div className="flex gap-2 border-b border-slate-700">
        {tabs.map(t=><button key={t.id} onClick={()=>setActiveTab(t.id)} className={`px-4 py-2 text-sm font-medium transition-all ${activeTab===t.id?'text-blue-400 border-b-2 border-blue-400':'text-slate-400 hover:text-white'}`}>{t.label}</button>)}
      </div>
      {activeTab==='capital_gains'&&(
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Capital Gains Tax Calculator</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div><label className="label">Asset Type</label>
                <select className="input-field" value={cgForm.asset_type} onChange={e=>setCgForm({...cgForm,asset_type:e.target.value})}>
                  <option value="equity">Equity</option><option value="debt">Debt</option><option value="gold">Gold</option>
                </select>
              </div>
              <div><label className="label">Tax Regime</label>
                <select className="input-field" value={cgForm.tax_regime} onChange={e=>setCgForm({...cgForm,tax_regime:e.target.value})}>
                  <option value="new_regime">New Regime</option><option value="old_regime">Old Regime</option>
                </select>
              </div>
              <div><label className="label">Purchase Price (₹)</label><input type="number" className="input-field" value={cgForm.purchase_price} onChange={e=>setCgForm({...cgForm,purchase_price:Number(e.target.value)})}/></div>
              <div><label className="label">Sale Price (₹)</label><input type="number" className="input-field" value={cgForm.sale_price} onChange={e=>setCgForm({...cgForm,sale_price:Number(e.target.value)})}/></div>
              <div><label className="label">Holding Days</label><input type="number" className="input-field" value={cgForm.holding_days} onChange={e=>setCgForm({...cgForm,holding_days:Number(e.target.value)})}/></div>
              <div><label className="label">Annual Income (₹)</label><input type="number" className="input-field" value={cgForm.annual_income} onChange={e=>setCgForm({...cgForm,annual_income:Number(e.target.value)})}/></div>
            </div>
            <button onClick={calcCG} disabled={loading} className="btn-primary mt-4">{loading?'Calculating...':'Calculate Tax'}</button>
          </div>
          {cgResult&&(
            <div className="card">
              <h3 className="font-semibold text-white mb-4">Tax Calculation Result</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div><p className="text-slate-400 text-sm">Gain</p><p className="text-green-400 text-xl font-bold">₹{cgResult.gain?.toLocaleString()}</p></div>
                <div><p className="text-slate-400 text-sm">Gain Type</p><p className="text-white font-medium">{cgResult.gain_type}</p></div>
                <div><p className="text-slate-400 text-sm">Tax Rate</p><p className="text-yellow-400 text-xl font-bold">{cgResult.tax_rate}%</p></div>
                <div><p className="text-slate-400 text-sm">Total Tax</p><p className="text-red-400 text-xl font-bold">₹{cgResult.total_tax?.toLocaleString()}</p></div>
              </div>
              <div className="mt-4 p-4 bg-slate-700/50 rounded-lg flex justify-between">
                <span className="text-slate-400">Net Proceeds After Tax</span>
                <span className="text-green-400 font-bold text-lg">₹{cgResult.net_proceeds?.toLocaleString()}</span>
              </div>
            </div>
          )}
        </div>
      )}
      {activeTab==='80c'&&(
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Section 80C Optimizer</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div><label className="label">Annual Income (₹)</label><input type="number" className="input-field" value={s80cForm.annual_income} onChange={e=>setS80cForm({...s80cForm,annual_income:Number(e.target.value)})}/></div>
              <div><label className="label">Tax Regime</label>
                <select className="input-field" value={s80cForm.tax_regime} onChange={e=>setS80cForm({...s80cForm,tax_regime:e.target.value})}>
                  <option value="old_regime">Old Regime</option><option value="new_regime">New Regime</option>
                </select>
              </div>
              <div><label className="label">ELSS Investment (₹)</label><input type="number" className="input-field" value={s80cForm.current_investments.elss} onChange={e=>setS80cForm({...s80cForm,current_investments:{...s80cForm.current_investments,elss:Number(e.target.value)}})}/></div>
              <div><label className="label">PPF Investment (₹)</label><input type="number" className="input-field" value={s80cForm.current_investments.ppf} onChange={e=>setS80cForm({...s80cForm,current_investments:{...s80cForm.current_investments,ppf:Number(e.target.value)}})}/></div>
            </div>
            <button onClick={calc80C} disabled={loading} className="btn-primary mt-4">{loading?'Optimizing...':'Optimize 80C'}</button>
          </div>
          {s80cResult&&(
            <div className="card">
              <h3 className="font-semibold text-white mb-4">80C Optimization Result</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div><p className="text-slate-400 text-sm">Tax Before 80C</p><p className="text-red-400 text-xl font-bold">₹{s80cResult.tax_before_80c?.toLocaleString()}</p></div>
                <div><p className="text-slate-400 text-sm">Tax After 80C</p><p className="text-green-400 text-xl font-bold">₹{s80cResult.tax_after_80c?.toLocaleString()}</p></div>
                <div><p className="text-slate-400 text-sm">Tax Saved</p><p className="text-blue-400 text-xl font-bold">₹{s80cResult.tax_saved?.toLocaleString()}</p></div>
                <div><p className="text-slate-400 text-sm">Remaining Limit</p><p className="text-yellow-400 text-xl font-bold">₹{s80cResult.remaining_80c_limit?.toLocaleString()}</p></div>
              </div>
              {s80cResult.recommendations?.length>0&&(
                <div><p className="text-slate-400 text-sm mb-3">Recommendations to maximize savings:</p>
                  <div className="space-y-2">
                    {s80cResult.recommendations.map((r:any,i:number)=>(
                      <div key={i} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                        <div><p className="text-white font-medium">{r.instrument}</p><p className="text-slate-400 text-xs">{r.benefit} • Lock-in: {r.lock_in}</p></div>
                        <span className="text-green-400 font-medium">₹{r.amount?.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
