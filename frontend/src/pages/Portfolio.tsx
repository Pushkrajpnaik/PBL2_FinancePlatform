import React, { useState } from 'react';
import { portfolioAPI, predictionAPI } from '../services/api';
import toast from 'react-hot-toast';
import { PieChart as PieIcon, Zap } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Legend } from 'recharts';

const COLORS = ['#3b82f6','#22c55e','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#f97316'];

export default function Portfolio() {
  const [form,          setForm]        = useState({ risk_profile: 'Moderate', method: 'markowitz', investment_amount: 1000000 });
  const [result,        setResult]      = useState<any>(null);
  const [dynamicResult, setDynamic]     = useState<any>(null);
  const [backtest,      setBacktest]    = useState<any>(null);
  const [equityCurve,   setEquityCurve] = useState<any>(null);
  const [loading,       setLoading]     = useState(false);
  const [activeTab,     setActiveTab]   = useState('optimize');

  const handleOptimize = async () => {
    setLoading(true);
    try {
      const r1 = await portfolioAPI.optimize(form);
      setResult(r1.data);
      toast.success('Portfolio optimized!');
    } catch (err: any) {
      toast.error('Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDynamic = async () => {
    setLoading(true);
    try {
      const res = await portfolioAPI.myPortfolio();
      setDynamic(res.data);
      toast.success('Dynamic portfolio loaded!');
    } catch (err: any) {
      toast.error('Dynamic optimization failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBacktest = async () => {
    setLoading(true);
    try {
      const [bt, ec] = await Promise.all([
        predictionAPI.backtestCompare(),
        predictionAPI.equityCurve(),
      ]);
      setBacktest(bt.data);
      setEquityCurve(ec.data);
      toast.success('Backtest complete!');
    } catch (err: any) {
      toast.error('Backtest failed');
    } finally {
      setLoading(false);
    }
  };

  const pieData = result
    ? Object.entries(result.allocation || {}).map(([k, v]: any) => ({ name: k.replace(/_/g, ' '), value: v }))
    : [];

  const tabs = [
    { id: 'optimize', label: 'Optimize' },
    { id: 'backtest', label: 'Backtest' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <PieIcon className="text-green-500" /> Portfolio Optimizer
        </h1>
        <p className="text-slate-400 mt-1">AI-powered optimization with real market data and news signals</p>
      </div>

      <div className="flex gap-2 border-b border-slate-700">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2 text-sm font-medium transition-all ${activeTab === t.id ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-400 hover:text-white'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'optimize' && (
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Configure Portfolio</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="label">Risk Profile</label>
                <select className="input-field" value={form.risk_profile} onChange={e => setForm({ ...form, risk_profile: e.target.value })}>
                  <option>Conservative</option><option>Moderate</option><option>Aggressive</option>
                </select>
              </div>
              <div>
                <label className="label">Method</label>
                <select className="input-field" value={form.method} onChange={e => setForm({ ...form, method: e.target.value })}>
                  <option value="markowitz">Markowitz</option>
                  <option value="risk_parity">Risk Parity</option>
                  <option value="cvar">CVaR</option>
                  <option value="black_litterman">Black-Litterman</option>
                </select>
              </div>
              <div>
                <label className="label">Investment Amount (₹)</label>
                <input type="number" className="input-field" value={form.investment_amount} onChange={e => setForm({ ...form, investment_amount: Number(e.target.value) })} />
              </div>
            </div>
            <div className="flex gap-3 mt-4">
              <button onClick={handleOptimize} disabled={loading} className="btn-primary">
                {loading ? 'Optimizing...' : 'Optimize Portfolio'}
              </button>
              <button onClick={handleDynamic} disabled={loading} className="btn-secondary flex items-center gap-2">
                <Zap size={16} />
                {loading ? 'Loading...' : 'My Dynamic Portfolio'}
              </button>
            </div>
          </div>

          {result && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="card">
                <h3 className="font-semibold text-white mb-4">Allocation Chart</h3>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" outerRadius={100} dataKey="value"
                      label={({ name, value }) => `${name} ${value}%`} labelLine={false}>
                      {pieData.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="card">
                <h3 className="font-semibold text-white mb-4">Results</h3>
                <div className="space-y-3 mb-4">
                  <div className="flex justify-between"><span className="text-slate-400">Method</span><span className="text-white font-medium text-sm">{result.method}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Expected Return</span><span className="text-green-400 font-medium">{result.expected_return}%</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Expected Risk</span><span className="text-yellow-400 font-medium">{result.expected_risk}%</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Sharpe Ratio</span><span className="text-blue-400 font-medium">{result.sharpe_ratio}</span></div>
                </div>
                <div className="pt-4 border-t border-slate-700">
                  <p className="text-slate-400 text-sm mb-2">Allocated Amounts</p>
                  {result.allocated_amounts && Object.entries(result.allocated_amounts).map(([k, v]: any) => (
                    <div key={k} className="flex justify-between text-sm mb-1">
                      <span className="text-slate-300 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className="text-white">₹{v.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {dynamicResult && (
            <div className="card border border-green-500/30 bg-green-500/5">
              <h3 className="font-semibold text-white mb-2 flex items-center gap-2">
                <Zap size={16} className="text-green-400" />
                Your Dynamic Portfolio (Real Data + News Signal)
              </h3>
              <p className="text-slate-400 text-sm mb-4">Based on your {dynamicResult.risk_profile} profile with live market data</p>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(dynamicResult.portfolio?.allocation || {}).map(([k, v]: any) => (
                  <div key={k} className="p-3 bg-slate-700/50 rounded-lg">
                    <p className="text-slate-400 text-xs capitalize">{k.replace(/_/g, ' ')}</p>
                    <p className="text-white font-bold text-lg">{v}%</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'backtest' && (
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-white mb-2">Real NIFTY50 Backtesting</h3>
            <p className="text-slate-400 text-sm mb-4">Walk-forward validated on actual historical data</p>
            <button onClick={handleBacktest} disabled={loading} className="btn-primary">
              {loading ? 'Running backtest...' : 'Run Backtest (3 Years Real Data)'}
            </button>
          </div>

          {backtest && (
            <div className="space-y-4">
              <div className="card">
                <h3 className="font-semibold text-white mb-4">Strategy Rankings (Real NIFTY50 Data)</h3>
                <div className="space-y-2">
                  {backtest.ranked?.map((r: any) => (
                    <div key={r.strategy} className={`flex items-center justify-between p-3 rounded-lg ${r.rank === 1 ? 'bg-green-500/10 border border-green-500/30' : 'bg-slate-700/50'}`}>
                      <div className="flex items-center gap-3">
                        <span className={`text-lg font-bold ${r.rank === 1 ? 'text-green-400' : 'text-slate-400'}`}>#{r.rank}</span>
                        <div>
                          <p className="text-white font-medium capitalize">{r.strategy.replace(/_/g, ' ')}</p>
                          {r.rank === 1 && <span className="badge-green text-xs">Best Strategy</span>}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-green-400 font-bold">{r.return?.toFixed(2)}%</p>
                        <p className="text-slate-400 text-xs">Sharpe: {r.sharpe?.toFixed(3)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {equityCurve && (
                <div className="card">
                  <h3 className="font-semibold text-white mb-4">
                    Equity Curve: {equityCurve.strategy?.replace(/_/g, ' ')} vs Buy & Hold
                  </h3>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="p-3 bg-blue-500/10 rounded-lg">
                      <p className="text-slate-400 text-sm">Strategy Return</p>
                      <p className="text-blue-400 text-xl font-bold">{equityCurve.strategy_metrics?.total_return?.toFixed(2)}%</p>
                      <p className="text-slate-500 text-xs">Sharpe: {equityCurve.strategy_metrics?.sharpe_ratio?.toFixed(3)}</p>
                    </div>
                    <div className="p-3 bg-slate-700/50 rounded-lg">
                      <p className="text-slate-400 text-sm">Benchmark Return</p>
                      <p className="text-white text-xl font-bold">{equityCurve.benchmark_metrics?.total_return?.toFixed(2)}%</p>
                      <p className="text-slate-500 text-xs">Sharpe: {equityCurve.benchmark_metrics?.sharpe_ratio?.toFixed(3)}</p>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={equityCurve.equity_curve || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
                      <Legend />
                      <Line type="monotone" dataKey="strategy_value" stroke="#3b82f6" strokeWidth={2} dot={false} name="Strategy" />
                      <Line type="monotone" dataKey="benchmark_value" stroke="#94a3b8" strokeWidth={1} dot={false} name="Benchmark" strokeDasharray="4 4" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
