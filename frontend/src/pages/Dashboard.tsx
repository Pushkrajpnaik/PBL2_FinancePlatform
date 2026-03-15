import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { authAPI, riskAPI, marketAPI, predictionAPI } from '../services/api';
import StatCard from '../components/StatCard';
import { Shield, TrendingUp, Newspaper, Target, PieChart, Receipt, Sunset, ArrowRight, AlertTriangle, Activity } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function Dashboard() {
  const [user,    setUser]    = useState<any>(null);
  const [risk,    setRisk]    = useState<any>(null);
  const [market,  setMarket]  = useState<any>(null);
  const [signal,  setSignal]  = useState<any>(null);
  const [news,    setNews]    = useState<any>(null);
  const [nifty,   setNifty]   = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [u, r, m, s, n, nf] = await Promise.allSettled([
          authAPI.me(),
          riskAPI.getMyProfile(),
          marketAPI.summary(),
          predictionAPI.investmentSignal(),
          marketAPI.liveNews(),
          marketAPI.nifty50("1mo"),
        ]);
        if (u.status  === 'fulfilled') setUser(u.value.data);
        if (r.status  === 'fulfilled') setRisk(r.value.data);
        if (m.status  === 'fulfilled') setMarket(m.value.data);
        if (s.status  === 'fulfilled') setSignal(s.value.data);
        if (n.status  === 'fulfilled') setNews(n.value.data);
        if (nf.status === 'fulfilled') setNifty(nf.value.data);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-slate-400 animate-pulse text-lg">Loading live data...</div>
    </div>
  );

  const modules = [
    { path: '/risk',       label: 'Risk Profile',     icon: Shield,    color: 'blue',   desc: 'Assess your risk tolerance' },
    { path: '/portfolio',  label: 'Portfolio',         icon: PieChart,  color: 'green',  desc: 'AI-optimized with real data' },
    { path: '/goals',      label: 'Goal Planner',      icon: Target,    color: 'yellow', desc: 'Monte Carlo goal planning' },
    { path: '/retirement', label: 'Retirement',        icon: Sunset,    color: 'purple', desc: 'Corpus planning with inflation' },
    { path: '/tax',        label: 'Tax Optimizer',     icon: Receipt,   color: 'red',    desc: 'After-tax return optimization' },
    { path: '/news',       label: 'News Intelligence', icon: Newspaper, color: 'blue',   desc: 'FinBERT live sentiment' },
  ];

  const colorMap: any = {
    blue:   'bg-blue-500/20 text-blue-400',
    green:  'bg-green-500/20 text-green-400',
    red:    'bg-red-500/20 text-red-400',
    yellow: 'bg-yellow-500/20 text-yellow-400',
    purple: 'bg-purple-500/20 text-purple-400',
  };

  const signalColors: any = {
    'STRONG BUY':  'text-green-400 bg-green-500/20',
    'BUY':         'text-green-300 bg-green-500/10',
    'HOLD':        'text-yellow-400 bg-yellow-500/20',
    'SELL':        'text-orange-400 bg-orange-500/20',
    'STRONG SELL': 'text-red-400 bg-red-500/20',
  };

  // Prepare NIFTY chart data
  const chartData = nifty?.history?.slice(-20).map((h: any) => ({
    date:  h.date?.slice(5),
    price: h.close,
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Welcome back, {user?.full_name?.split(' ')[0] || 'Investor'} 👋
          </h1>
          <p className="text-slate-400 mt-1">Live market intelligence platform</p>
        </div>
        <div className="text-right">
          <p className="text-slate-500 text-xs">Last updated</p>
          <p className="text-slate-400 text-sm">{new Date().toLocaleTimeString()}</p>
        </div>
      </div>

      {/* Live Market Summary */}
      {market && (
        <div className="card">
          <h2 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
            <Activity size={14} className="text-green-400" />
            LIVE MARKET
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(market).filter(([k]) => k !== 'from_cache').map(([key, val]: any) => (
              <div key={key} className="text-center">
                <p className="text-slate-500 text-xs uppercase">{key.replace('_', ' ')}</p>
                <p className="text-white font-bold text-lg mt-1">
                  {typeof val?.price === 'number' ? val.price.toLocaleString() : '-'}
                </p>
                <p className={`text-sm font-medium ${val?.direction === 'up' ? 'text-green-400' : 'text-red-400'}`}>
                  {val?.change_pct > 0 ? '+' : ''}{val?.change_pct?.toFixed(2)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* NIFTY50 Chart */}
      {chartData.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={16} className="text-blue-400" />
            NIFTY50 — Last 20 Days (Real Data)
          </h2>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                labelStyle={{ color: '#94a3b8' }}
                itemStyle={{ color: '#60a5fa' }}
              />
              <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Investment Signal */}
      {signal && (
        <div className={`card border ${
          signal.signal?.includes('BUY')  ? 'border-green-500/30 bg-green-500/5' :
          signal.signal?.includes('SELL') ? 'border-red-500/30 bg-red-500/5' :
          'border-yellow-500/30 bg-yellow-500/5'
        }`}>
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className={`px-4 py-2 rounded-lg font-bold text-lg ${signalColors[signal.signal] || 'text-yellow-400 bg-yellow-500/20'}`}>
                {signal.signal}
              </div>
              <div>
                <p className="text-white font-semibold">AI Investment Signal</p>
                <p className="text-slate-400 text-sm mt-1">{signal.recommendation}</p>
                <div className="flex gap-4 mt-2">
                  <span className="text-xs text-slate-500">Regime: <span className="text-white">{signal.regime}</span></span>
                  <span className="text-xs text-slate-500">Score: <span className="text-white">{signal.score}</span></span>
                  <span className="text-xs text-slate-500">Geo Risk: <span className={signal.geo_risk > 0.5 ? 'text-red-400' : 'text-green-400'}>{signal.geo_risk}</span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Risk Profile"
          value={risk?.profile_type || 'Not assessed'}
          subtitle={risk ? `Score: ${risk.score}/100` : 'Complete assessment'}
          icon={<Shield size={20} />}
          color="blue"
        />
        <StatCard
          title="Market Sentiment"
          value={news?.market_sentiment || 'Loading...'}
          subtitle={news ? `${news.total_articles} articles • FinBERT` : ''}
          icon={<Newspaper size={20} />}
          color={news?.market_sentiment === 'Bullish' ? 'green' : news?.market_sentiment === 'Bearish' ? 'red' : 'yellow'}
        />
        <StatCard
          title="Geo Risk"
          value={news?.geopolitical_risk?.level || 'Unknown'}
          subtitle={`Score: ${news?.geopolitical_risk?.max_score?.toFixed(2) || 0}`}
          icon={<AlertTriangle size={20} />}
          color={news?.geopolitical_risk?.level === 'Critical' ? 'red' : news?.geopolitical_risk?.level === 'High' ? 'red' : 'yellow'}
        />
      </div>

      {/* Risk Alerts */}
      {news?.risk_alerts?.length > 0 && (
        <div className="card border border-red-500/30 bg-red-500/5">
          <h3 className="font-semibold text-white flex items-center gap-2 mb-3">
            <AlertTriangle className="text-red-400" size={16} />
            Risk Alerts ({news.total_risk_alerts})
          </h3>
          <div className="space-y-2">
            {news.risk_alerts.slice(0, 3).map((a: any, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-700/50 rounded-lg">
                <div className="w-2 h-2 rounded-full mt-2 shrink-0 bg-red-400" />
                <div>
                  <p className="text-white text-sm font-medium">{a.title}</p>
                  <p className="text-slate-400 text-xs mt-1">{a.source} • {a.risk_level?.level} Risk</p>
                  <p className="text-blue-400 text-xs mt-1">{a.risk_level?.action}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modules Grid */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Platform Modules</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {modules.map(({ path, label, icon: Icon, color, desc }) => (
            <Link key={path} to={path} className="card group hover:border-slate-500 transition-all cursor-pointer">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${colorMap[color]}`}><Icon size={20} /></div>
                  <div>
                    <h3 className="font-semibold text-white">{label}</h3>
                    <p className="text-slate-400 text-sm mt-1">{desc}</p>
                  </div>
                </div>
                <ArrowRight size={16} className="text-slate-600 group-hover:text-slate-400 mt-1" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {!risk && (
        <div className="card border border-blue-500/30 bg-blue-500/5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-white">Complete Your Risk Assessment</h3>
              <p className="text-slate-400 text-sm mt-1">Get personalized AI recommendations.</p>
            </div>
            <Link to="/risk" className="btn-primary shrink-0">Start Now</Link>
          </div>
        </div>
      )}
    </div>
  );
}