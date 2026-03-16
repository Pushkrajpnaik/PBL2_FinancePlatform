import React, { useState, useEffect } from 'react';
import { portfolioAPI, predictionAPI, marketAPI, riskAPI } from '../services/api';
import toast from 'react-hot-toast';
import { PieChart as PieIcon, Zap, Brain, Shield } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Legend } from 'recharts';

const COLORS = ['#3b82f6','#22c55e','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#f97316'];

const getRecommendedMethod = (regime: string): string => {
  switch (regime) {
    case 'Bear Market':      return 'cvar';
    case 'High Volatility':  return 'cvar';
    case 'Bull Market':      return 'markowitz';
    case 'Recovery':         return 'risk_parity';
    default:                 return 'risk_parity';
  }
};

const METHOD_LABELS: any = {
  markowitz:       'Markowitz Mean-Variance',
  risk_parity:     'Risk Parity',
  cvar:            'CVaR (Conditional Value at Risk)',
  black_litterman: 'Black-Litterman',
};

const METHOD_REASONS: any = {
  markowitz:   'maximizes returns in Bull Market conditions',
  risk_parity: 'distributes risk equally — best for neutral/recovery markets',
  cvar:        'minimizes worst-case losses — best for Bear Market protection',
  black_litterman: 'blends market equilibrium with outlook',
};

const REGIME_STYLE: any = {
  'Bull Market':      { text: 'text-green-400',  border: 'border-green-500/30',  bg: 'bg-green-500/5'  },
  'Bear Market':      { text: 'text-red-400',    border: 'border-red-500/30',    bg: 'bg-red-500/5'    },
  'High Volatility':  { text: 'text-yellow-400', border: 'border-yellow-500/30', bg: 'bg-yellow-500/5' },
  'Recovery':         { text: 'text-blue-400',   border: 'border-blue-500/30',   bg: 'bg-blue-500/5'   },
  'Sideways/Neutral': { text: 'text-slate-400',  border: 'border-slate-500/30',  bg: 'bg-slate-500/5'  },
};

const PROFILE_STYLE: any = {
  Conservative: { text: 'text-blue-400',   border: 'border-blue-500/30',   bg: 'bg-blue-500/5'   },
  Moderate:     { text: 'text-yellow-400', border: 'border-yellow-500/30', bg: 'bg-yellow-500/5' },
  Aggressive:   { text: 'text-red-400',    border: 'border-red-500/30',    bg: 'bg-red-500/5'    },
};

export default function Portfolio() {
  const [investmentAmount, setInvestmentAmount] = useState(1000000);
  const [result,           setResult]           = useState<any>(null);
  const [dynamicResult,    setDynamic]           = useState<any>(null);
  const [backtest,         setBacktest]          = useState<any>(null);
  const [equityCurve,      setEquityCurve]       = useState<any>(null);
  const [loading,          setLoading]           = useState(false);
  const [activeTab,        setActiveTab]         = useState('optimize');
  const [regime,           setRegime]            = useState('');
  const [regimeConf,       setRegimeConf]        = useState(0);
  const [method,           setMethod]            = useState('risk_parity');
  const [riskProfile,      setRiskProfile]       = useState('');
  const [riskScore,        setRiskScore]         = useState(0);
  const [loadingAuto,      setLoadingAuto]       = useState(true);

  useEffect(() => {
    const fetchAutoData = async () => {
      try {
        const [regimeRes, profileRes] = await Promise.allSettled([
          marketAPI.realRegime(),
          riskAPI.getMyProfile(),
        ]);
        if (regimeRes.status === 'fulfilled') {
          const r = regimeRes.value.data?.regime || 'Sideways/Neutral';
          const c = regimeRes.value.data?.confidence || 0;
          setRegime(r);
          setRegimeConf(c);
          setMethod(getRecommendedMethod(r));
        }
        if (profileRes.status === 'fulfilled') {
          setRiskProfile(profileRes.value.data?.profile_type || 'Moderate');
          setRiskScore(profileRes.value.data?.score || 0);
        } else {
          setRiskProfile('Moderate');
        }
      } catch {
        setRegime('Sideways/Neutral');
        setRiskProfile('Moderate');
      } finally {
        setLoadingAuto(false);
      }
    };
    fetchAutoData();
  }, []);

  const handleOptimize = async () => {
    setLoading(true);
    try {
      const r = await portfolioAPI.optimize({
        risk_profile:      riskProfile,
        method:            method,
        investment_amount: investmentAmount,
      });
      setResult(r.data);
      toast.success('Portfolio optimized!');
    } catch {
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
    } catch {
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
    } catch {
      toast.error('Backtest failed');
    } finally {
      setLoading(false);
    }
  };

  const pieData = result
    ? Object.entries(result.allocation || {}).map(([k, v]: any) => ({
        name: k.replace(/_/g, ' '), value: v,
      }))
    : [];

  const rs = REGIME_STYLE[regime]       || REGIME_STYLE['Sideways/Neutral'];
  const ps = PROFILE_STYLE[riskProfile] || PROFILE_STYLE['Moderate'];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <PieIcon className="text-green-500" /> Portfolio Optimizer
        </h1>
        <p className="text-slate-400 mt-1">
          Fully automated — risk profile and method auto-detected
        </p>
      </div>

      <div className="flex gap-2 border-b border-slate-700">
        {['optimize','backtest'].map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize transition-all ${
              activeTab === t ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-400 hover:text-white'
            }`}>{t}</button>
        ))}
      </div>

      {activeTab === 'optimize' && (
        <div className="space-y-4">
          {loadingAuto ? (
            <div className="card animate-pulse text-slate-400">
              Detecting market regime and loading your risk profile...
            </div>
          ) : (
            <>
              {/* Auto-detected cards — no dropdowns */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className={`card border ${ps.border} ${ps.bg}`}>
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-700 rounded-lg shrink-0">
                      <Shield size={20} className={ps.text} />
                    </div>
                    <div className="flex-1">
                      <p className="text-slate-400 text-xs">Your Risk Profile (from questionnaire)</p>
                      <p className={`text-xl font-bold ${ps.text}`}>{riskProfile}</p>
                      <p className="text-slate-500 text-xs">Score: {riskScore.toFixed(1)}/100</p>
                    </div>
                    <span className="px-2 py-1 text-xs bg-blue-500/20 text-blue-400 rounded-full">Auto</span>
                  </div>
                </div>

                <div className={`card border ${rs.border} ${rs.bg}`}>
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-700 rounded-lg shrink-0">
                      <Brain size={20} className={rs.text} />
                    </div>
                    <div className="flex-1">
                      <p className="text-slate-400 text-xs">Market Regime → Algorithm</p>
                      <p className={`text-xl font-bold ${rs.text}`}>{regime}</p>
                      <p className="text-slate-500 text-xs">
                        {regimeConf.toFixed(1)}% confidence → {METHOD_LABELS[method]}
                      </p>
                    </div>
                    <span className="px-2 py-1 text-xs bg-blue-500/20 text-blue-400 rounded-full">Auto</span>
                  </div>
                </div>
              </div>

              {/* Only investment amount from user */}
              <div className="card">
                <h3 className="font-semibold text-white mb-4">Investment Amount (₹)</h3>
                <input type="number" className="input-field" value={investmentAmount}
                  onChange={e => setInvestmentAmount(Number(e.target.value))} />
                <div className="mt-3 p-3 bg-slate-700/30 rounded-lg">
                  <p className="text-slate-400 text-sm">
                    Optimizing
                    <span className={`font-semibold mx-1 ${ps.text}`}>{riskProfile}</span>
                    portfolio using
                    <span className={`font-semibold mx-1 ${rs.text}`}>{METHOD_LABELS[method]}</span>
                    for
                    <span className={`font-semibold mx-1 ${rs.text}`}>{regime}</span>
                  </p>
                  <p className="text-slate-500 text-xs mt-1">
                    Why {METHOD_LABELS[method]}? {METHOD_REASONS[method]}
                  </p>
                </div>
                <div className="flex gap-3 mt-4">
                  <button onClick={handleOptimize} disabled={loading} className="btn-primary">
                    {loading ? 'Optimizing...' : 'Optimize Portfolio'}
                  </button>
                  <button onClick={handleDynamic} disabled={loading}
                    className="btn-secondary flex items-center gap-2">
                    <Zap size={16} />
                    {loading ? 'Loading...' : 'Dynamic Portfolio'}
                  </button>
                </div>
              </div>
            </>
          )}

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
                <h3 className="font-semibold text-white mb-3">Results</h3>
                <div className="space-y-3 mb-4">
                  {[
                    { label: 'Method Used',    value: result.method,                color: 'text-white text-sm'  },
                    { label: 'Risk Profile',   value: riskProfile,                  color: ps.text               },
                    { label: 'Market Regime',  value: regime,                       color: rs.text               },
                    { label: 'Expected Return',value: `${result.expected_return}%`, color: 'text-green-400'      },
                    { label: 'Expected Risk',  value: `${result.expected_risk}%`,   color: 'text-yellow-400'     },
                    { label: 'Sharpe Ratio',   value: result.sharpe_ratio,          color: 'text-blue-400'       },
                  ].map(row => (
                    <div key={row.label} className="flex justify-between">
                      <span className="text-slate-400">{row.label}</span>
                      <span className={`font-medium ${row.color}`}>{row.value}</span>
                    </div>
                  ))}
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
                Dynamic Portfolio — Real Data + News Signal
              </h3>
              <p className="text-slate-400 text-sm mb-4">
                {riskProfile} profile • Live market data • News-adjusted
              </p>
              <div className="grid grid-cols-3 gap-3">
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
            <p className="text-slate-400 text-sm mb-4">Walk-forward validated on 739 days of actual data</p>
            <button onClick={handleBacktest} disabled={loading} className="btn-primary">
              {loading ? 'Running backtest...' : 'Run Backtest (3 Years Real Data)'}
            </button>
          </div>

          {backtest && (
            <div className="space-y-4">
              <div className="card">
                <h3 className="font-semibold text-white mb-4">Strategy Rankings</h3>
                <div className="space-y-2">
                  {backtest.ranked?.map((r: any) => (
                    <div key={r.strategy} className={`flex items-center justify-between p-3 rounded-lg ${
                      r.rank === 1 ? 'bg-green-500/10 border border-green-500/30' : 'bg-slate-700/50'
                    }`}>
                      <div className="flex items-center gap-3">
                        <span className={`text-lg font-bold ${r.rank === 1 ? 'text-green-400' : 'text-slate-400'}`}>
                          #{r.rank}
                        </span>
                        <div>
                          <p className="text-white font-medium capitalize">{r.strategy.replace(/_/g, ' ')}</p>
                          {r.rank === 1 && <span className="text-xs text-green-400">Best Strategy ✓</span>}
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
                  <h3 className="font-semibold text-white mb-4">Equity Curve vs Benchmark</h3>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="p-3 bg-blue-500/10 rounded-lg">
                      <p className="text-slate-400 text-sm">Strategy Return</p>
                      <p className="text-blue-400 text-xl font-bold">
                        {equityCurve.strategy_metrics?.total_return?.toFixed(2)}%
                      </p>
                      <p className="text-slate-500 text-xs">
                        Sharpe: {equityCurve.strategy_metrics?.sharpe_ratio?.toFixed(3)}
                      </p>
                    </div>
                    <div className="p-3 bg-slate-700/50 rounded-lg">
                      <p className="text-slate-400 text-sm">Buy & Hold</p>
                      <p className="text-white text-xl font-bold">
                        {equityCurve.benchmark_metrics?.total_return?.toFixed(2)}%
                      </p>
                      <p className="text-slate-500 text-xs">
                        Sharpe: {equityCurve.benchmark_metrics?.sharpe_ratio?.toFixed(3)}
                      </p>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={equityCurve.equity_curve || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
                      <Legend />
                      <Line type="monotone" dataKey="strategy_value" stroke="#3b82f6"
                        strokeWidth={2} dot={false} name="Strategy" />
                      <Line type="monotone" dataKey="benchmark_value" stroke="#94a3b8"
                        strokeWidth={1} dot={false} name="Benchmark" strokeDasharray="4 4" />
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