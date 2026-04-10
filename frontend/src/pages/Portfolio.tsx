import React, { useState, useEffect, useCallback } from 'react';
import { portfolioAPI, predictionAPI, marketAPI, riskAPI } from '../services/api';
import toast from 'react-hot-toast';
import { PieChart as PieIcon, Zap, Brain, Shield, Wallet, RefreshCw, Search } from 'lucide-react';
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

const DEFENSIVE_KW = ['bluechip', 'large cap', 'tax saver', 'elss', 'large cap fund'];
const AGGRESSIVE_KW = ['small cap', 'mid-cap', 'mid cap', 'emerging', 'opportunities fund'];
const BALANCED_KW = ['flexi', 'flexi cap'];

type FundRow = { fund: any; score: number; reason: string };

type RelatedFund = {
  scheme_code: string;
  scheme_name: string;
  matchedQuery: string;
  anchorName: string;
};

/** Search phrases derived from a recommended fund (AMC, name prefix, category). */
function queriesFromRecommendedFund(fund: any): string[] {
  const out: string[] = [];
  const fh = String(fund.fund_house || '').trim();
  if (fh) {
    const w = fh.split(/\s+/);
    if (w.length >= 2) out.push(w.slice(0, 2).join(' '));
    else out.push(w[0]);
  }
  let name = String(fund.scheme_name || '');
  name = name
    .replace(/\s*-\s*Direct.*$/i, '')
    .replace(/\s*-\s*Regular.*$/i, '')
    .replace(/\s*(Growth|IDCW|Payout).*/i, '')
    .trim();
  const words = name.split(/\s+/).filter(x => x.length > 1 && !/^(direct|plan|fund)$/i.test(x));
  if (words.length >= 2) out.push(words.slice(0, 2).join(' '));
  const cat = name.match(/\b(large\s+cap|mid\s+cap|small\s+cap|flexi\s+cap|elss|tax\s+saver)\b/i);
  if (cat) out.push(cat[0].replace(/\s+/g, ' '));
  return [...new Set(out.map(s => s.trim()).filter(Boolean))].slice(0, 4);
}

async function discoverRelatedFunds(ranked: FundRow[]): Promise<RelatedFund[]> {
  if (!ranked.length) return [];

  const exclude = new Set(ranked.map(r => String(r.fund.scheme_code)));
  const queue: { q: string; anchor: string }[] = [];
  for (const row of ranked.slice(0, 5)) {
    const anchor = String(row.fund.scheme_name || 'Recommendation');
    for (const q of queriesFromRecommendedFund(row.fund)) {
      queue.push({ q, anchor });
    }
  }

  const seenQ = new Set<string>();
  const ordered = queue.filter(({ q }) => {
    if (seenQ.has(q)) return false;
    seenQ.add(q);
    return true;
  }).slice(0, 10);

  const out: RelatedFund[] = [];
  const seenCodes = new Set<string>(exclude);

  for (const { q, anchor } of ordered) {
    try {
      const res = await marketAPI.searchFunds(q);
      const results = res.data?.results || [];
      for (const item of results) {
        const code = String(item.scheme_code);
        if (seenCodes.has(code)) continue;
        seenCodes.add(code);
        out.push({
          scheme_code: code,
          scheme_name: String(item.scheme_name || ''),
          matchedQuery: q,
          anchorName: anchor,
        });
        if (out.length >= 16) return out;
      }
    } catch {
      /* skip failed query */
    }
  }

  return out;
}

function buildFundSuggestions(funds: any[], riskProfile: string, regime: string): FundRow[] {
  const bearish = regime === 'Bear Market' || regime === 'High Volatility';
  const bullish = regime === 'Bull Market' || regime === 'Recovery';

  const scored = (funds || []).map((fund: any) => {
    const name = String(fund.scheme_name || '').toLowerCase();
    let score = 0;
    const reasons: string[] = [];

    const hasDef = DEFENSIVE_KW.some(k => name.includes(k));
    const hasAgg = AGGRESSIVE_KW.some(k => name.includes(k));
    const hasBal = BALANCED_KW.some(k => name.includes(k));

    if (riskProfile === 'Conservative') {
      if (hasDef) { score += 4; reasons.push('Large-cap / quality tilt'); }
      if (hasAgg) { score -= 2; }
      if (hasBal) { score += 1; reasons.push('Diversified flexi'); }
    } else if (riskProfile === 'Aggressive') {
      if (hasAgg) { score += 4; reasons.push('Higher growth / mid–small cap'); }
      if (hasDef) { score += 0.5; }
      if (hasBal) { score += 2; reasons.push('Flexi cap option'); }
    } else {
      if (hasBal) { score += 3; reasons.push('Balanced flexi'); }
      if (hasDef) { score += 1.5; }
      if (hasAgg) { score += 1.5; }
    }

    if (bearish) {
      if (hasDef) { score += 2; reasons.push('Defensive in current regime'); }
      if (hasAgg) { score -= 1; }
    }
    if (bullish && hasAgg) {
      score += 1.5;
      reasons.push('Regime supports growth sleeves');
    }

    const r1y = Number(fund.return_1y) || 0;
    score += Math.min(1.5, Math.max(-0.5, r1y / 40));

    let reason = reasons[0] || 'Fits a diversified core';
    if (reasons.length > 1) reason = `${reasons[0]} · ${reasons[1]}`;

    return { fund, score, reason };
  });

  return scored
    .sort((a, b) => b.score - a.score || (Number(b.fund.return_1y) || 0) - (Number(a.fund.return_1y) || 0))
    .slice(0, 6);
}

export default function Portfolio() {
  const parseNumberInput = (value: string) => (value === '' ? '' : Number(value));
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
  const [suggestedRows,    setSuggestedRows]     = useState<FundRow[]>([]);
  const [relatedFunds,     setRelatedFunds]      = useState<RelatedFund[]>([]);
  const [loadingFunds,     setLoadingFunds]      = useState(false);
  const [loadingRelated,   setLoadingRelated]   = useState(false);

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

  const loadFundSuggestions = useCallback(async () => {
    setLoadingFunds(true);
    setLoadingRelated(false);
    setRelatedFunds([]);
    try {
      const res = await marketAPI.popularFunds();
      const funds = res.data?.funds || [];
      const ranked = buildFundSuggestions(
        funds,
        riskProfile || 'Moderate',
        regime || 'Sideways/Neutral',
      );
      setSuggestedRows(ranked);
      setLoadingFunds(false);
      setLoadingRelated(true);
      const related = await discoverRelatedFunds(ranked);
      setRelatedFunds(related);
    } catch {
      toast.error('Could not load fund suggestions');
      setSuggestedRows([]);
      setRelatedFunds([]);
    } finally {
      setLoadingFunds(false);
      setLoadingRelated(false);
    }
  }, [riskProfile, regime]);

  useEffect(() => {
    if (loadingAuto || !riskProfile) return;
    loadFundSuggestions();
  }, [loadingAuto, riskProfile, regime, loadFundSuggestions]);

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

  const normalizedAllocation = result
    ? (() => {
        const allocation = result.allocation || {};
        if (Object.keys(allocation).length > 0) {
          return Object.fromEntries(
            Object.entries(allocation).map(([k, v]: any) => [k, Number(v) || 0]),
          );
        }
        const allocated = result.allocated_amounts || {};
        const total = Number(Object.values(allocated).reduce((sum: number, x: any) => sum + (Number(x) || 0), 0));
        return Object.fromEntries(
          Object.entries(allocated).map(([k, v]: any) => [k, total > 0 ? ((Number(v) || 0) / total) * 100 : 0]),
        );
      })()
    : {};

  const computedAllocatedAmounts = Object.fromEntries(
    Object.entries(normalizedAllocation).map(([k, pct]: any) => [
      k,
      Math.round(((Number(pct) || 0) / 100) * (Number(investmentAmount) || 0)),
    ]),
  );

  const pieData = result
    ? Object.entries(normalizedAllocation).map(([k, pct]: any) => ({
        name: k.replace(/_/g, ' '),
        percent: Number(pct) || 0,
        amount: computedAllocatedAmounts[k] || 0,
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
                  onChange={e => setInvestmentAmount(parseNumberInput(e.target.value) as any)} />
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

              {/* Suggested mutual funds */}
              <div className="card border border-emerald-500/20">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2">
                    <Wallet className="text-emerald-400 shrink-0" size={20} />
                    <div>
                      <h3 className="font-semibold text-white">Suggested mutual funds</h3>
                      <p className="text-slate-500 text-xs mt-0.5">
                        Ranked for your <span className={ps.text}>{riskProfile}</span> profile and{' '}
                        <span className={rs.text}>{regime}</span> regime (Indian AMCs, live NAV where available).
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={loadFundSuggestions}
                    disabled={loadingFunds || loadingRelated}
                    className="btn-secondary shrink-0 flex items-center gap-1.5 text-xs py-2 px-3"
                  >
                    <RefreshCw size={14} className={loadingFunds || loadingRelated ? 'animate-spin' : ''} />
                    Refresh
                  </button>
                </div>
                {loadingFunds && suggestedRows.length === 0 ? (
                  <p className="text-slate-500 text-sm animate-pulse">Loading fund suggestions…</p>
                ) : suggestedRows.length === 0 ? (
                  <p className="text-slate-500 text-sm">No suggestions available.</p>
                ) : (
                  <div className="space-y-2">
                    {suggestedRows.map(({ fund, reason }, i) => (
                      <div
                        key={`${fund.scheme_code}-${i}`}
                        className="flex flex-wrap items-start justify-between gap-2 p-3 rounded-xl bg-slate-800/50 border border-slate-700/80"
                      >
                        <div className="min-w-0 flex-1">
                          <p className="text-white text-sm font-medium truncate" title={fund.scheme_name}>
                            {fund.scheme_name || 'Fund'}
                          </p>
                          <p className="text-slate-500 text-xs mt-0.5">
                            Scheme {fund.scheme_code}
                            {fund.fund_house ? ` · ${fund.fund_house}` : ''}
                          </p>
                          <p className="text-emerald-400/90 text-xs mt-1">{reason}</p>
                        </div>
                        <div className="text-right shrink-0">
                          <p className="text-slate-400 text-xs">1Y return</p>
                          <p className="text-white font-mono text-sm">
                            {fund.error ? '—' : `${Number(fund.return_1y ?? 0).toFixed(1)}%`}
                          </p>
                          <p className="text-slate-500 text-xs mt-0.5">
                            Vol. {fund.error ? '—' : `${Number(fund.volatility ?? 0).toFixed(1)}%`}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <p className="text-slate-600 text-[11px] mt-3">
                  Illustrative only — not investment advice. Verify scheme details and consult a financial advisor.
                </p>
              </div>

              {/* Related schemes from MF search (aligned with recommendations) */}
              {suggestedRows.length > 0 && (
                <div className="card border border-sky-500/15">
                  <div className="flex items-center gap-2 mb-2">
                    <Search className="text-sky-400 shrink-0" size={18} />
                    <div>
                      <h3 className="font-semibold text-white text-sm">Possible schemes (same AMC / category)</h3>
                      <p className="text-slate-500 text-xs mt-0.5">
                        Pulled from live MF search using each top recommendation’s fund house and name keywords.
                        Excludes schemes already listed above.
                      </p>
                    </div>
                  </div>
                  {loadingRelated && relatedFunds.length === 0 ? (
                    <p className="text-slate-500 text-xs animate-pulse py-2">Finding related schemes…</p>
                  ) : relatedFunds.length === 0 ? (
                    <p className="text-slate-500 text-xs py-2">No extra matches from search (try Refresh).</p>
                  ) : (
                    <ul className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
                      {relatedFunds.map((r) => (
                        <li
                          key={r.scheme_code}
                          className="text-xs text-slate-300 border border-slate-700/60 rounded-lg px-3 py-2 bg-slate-800/40"
                        >
                          <span className="text-white font-medium">{r.scheme_name}</span>
                          <span className="text-slate-500"> · {r.scheme_code}</span>
                          <p className="text-slate-500 mt-0.5">
                            Search “{r.matchedQuery}” · aligned with “{r.anchorName}”
                          </p>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </>
          )}

          {result && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="card">
                <h3 className="font-semibold text-white mb-4">Allocation Chart</h3>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" outerRadius={100} dataKey="amount"
                      label={({ name, value }) => `${name} ₹${(Number(value || 0) / 100000).toFixed(1)}L`} labelLine={false}>
                      {pieData.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip
                      formatter={(_: any, __: any, payload: any) => {
                        const p = payload?.payload;
                        if (!p) return ['—', ''];
                        return [`₹${(p.amount || 0).toLocaleString('en-IN')} (${(p.percent || 0).toFixed(1)}%)`, p.name];
                      }}
                    />
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
                  {Object.entries(computedAllocatedAmounts).map(([k, v]: any) => (
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