import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { authAPI, riskAPI, marketAPI, predictionAPI } from '../services/api';
import StatCard from '../components/StatCard';
import {
  Shield, TrendingUp, Newspaper, Target, PieChart,
  Receipt, Sunset, ArrowRight, Activity, Zap, Globe, BrainCircuit
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const getCached = (key: string) => {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const setCached = (key: string, value: any) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // no-op
  }
};

const SIGNAL_STYLE: Record<string, { cls: string; dotColor: string }> = {
  'STRONG BUY':  { cls: 'signal-strong-buy',  dotColor: 'var(--green)' },
  'BUY':         { cls: 'signal-buy',          dotColor: 'var(--green)' },
  'HOLD':        { cls: 'signal-hold',         dotColor: 'var(--yellow)' },
  'SELL':        { cls: 'signal-sell',         dotColor: 'var(--red)' },
  'STRONG SELL': { cls: 'signal-strong-sell',  dotColor: 'var(--red)' },
};

const modules = [
  { path: '/risk',       label: 'Risk Profile',     icon: Shield,    color: 'var(--accent)',  desc: 'Assess your risk tolerance' },
  { path: '/portfolio',  label: 'Portfolio',         icon: PieChart,  color: 'var(--green)',   desc: '4-algorithm optimization' },
  { path: '/goals',      label: 'Goal Planner',      icon: Target,    color: 'var(--yellow)',  desc: 'Monte Carlo planning' },
  { path: '/retirement', label: 'Retirement',        icon: Sunset,    color: 'var(--purple)',  desc: 'Corpus with inflation' },
  { path: '/tax',        label: 'Tax Optimizer',     icon: Receipt,   color: 'var(--red)',     desc: 'Budget 2024 compliant' },
  { path: '/news',       label: 'News Intelligence', icon: Newspaper, color: 'var(--accent)',  desc: 'FinBERT live sentiment' },
];

const AI_LOG_BASE = [
  'Pulling live market and sentiment packets.',
  'Recomputing portfolio drift and exposure deltas.',
  'Evaluating regime confidence against volatility bands.',
  'Refreshing geopolitical shock-risk weights.',
  'Scoring signal consistency across prediction models.',
  'Updating dashboard priorities from usage behavior.',
];

function LoadingSkeleton() {
  return (
    <div className="space-y-5">
      {[1, 2, 3].map(i => (
        <div key={i} className="card shimmer" style={{ height: 80 }} />
      ))}
    </div>
  );
}

export default function Dashboard() {
  const [user,    setUser]    = useState<any>(() => getCached('dashboard:user'));
  const [risk,    setRisk]    = useState<any>(() => getCached('dashboard:risk'));
  const [market,  setMarket]  = useState<any>(() => getCached('dashboard:market'));
  const [signal,  setSignal]  = useState<any>(() => getCached('dashboard:signal'));
  const [news,    setNews]    = useState<any>(() => getCached('dashboard:news'));
  const [nifty,   setNifty]   = useState<any>(() => getCached('dashboard:nifty'));
  const [aiLog,   setAiLog]   = useState<string[]>([]);
  const [lineCursorIdx, setLineCursorIdx] = useState(0);
  const [loading, setLoading] = useState<boolean>(() => {
    const hasWarmCache = !!(getCached('dashboard:user') || getCached('dashboard:market') || getCached('dashboard:signal'));
    return !hasWarmCache;
  });

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [u, r, m, s, n, nf] = await Promise.allSettled([
          authAPI.me(),
          riskAPI.getMyProfile(),
          marketAPI.summary(),
          predictionAPI.investmentSignal(),
          marketAPI.liveNews(),
          marketAPI.nifty50('1mo'),
        ]);
        if (u.status  === 'fulfilled') {
          setUser(u.value.data);
          setCached('dashboard:user', u.value.data);
        }
        if (r.status  === 'fulfilled') {
          setRisk(r.value.data);
          setCached('dashboard:risk', r.value.data);
        }
        if (m.status  === 'fulfilled') {
          setMarket(m.value.data);
          setCached('dashboard:market', m.value.data);
        }
        if (s.status  === 'fulfilled') {
          setSignal(s.value.data);
          setCached('dashboard:signal', s.value.data);
        }
        if (n.status  === 'fulfilled') {
          setNews(n.value.data);
          setCached('dashboard:news', n.value.data);
        }
        if (nf.status === 'fulfilled') {
          setNifty(nf.value.data);
          setCached('dashboard:nifty', nf.value.data);
        }
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  useEffect(() => {
    const dynamicLines = [
      `Regime: ${signal?.regime || 'Unknown'} | Signal: ${signal?.signal || 'Pending'}`,
      `Market sentiment ${news?.market_sentiment || 'Neutral'} from ${news?.total_articles || 0} articles`,
      `Geo risk level ${news?.geopolitical_risk?.level || 'Low'} | score ${news?.geopolitical_risk?.max_score?.toFixed?.(2) || '0.00'}`,
      `NIFTY datapoints loaded: ${nifty?.history?.length || 0}`,
    ];
    setAiLog([...AI_LOG_BASE.slice(0, 3), ...dynamicLines]);
  }, [signal, news, nifty]);

  useEffect(() => {
    const tick = window.setInterval(() => {
      const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const line = `${t} · ${AI_LOG_BASE[Math.floor(Math.random() * AI_LOG_BASE.length)]}`;
      setAiLog(prev => [line, ...prev].slice(0, 12));
    }, 2600);
    return () => window.clearInterval(tick);
  }, []);

  const usageRisk = Number(localStorage.getItem('dashboard:module:risk') || 0);
  const usagePortfolio = Number(localStorage.getItem('dashboard:module:portfolio') || 0);
  const prioritizeRiskPortfolio = usageRisk + usagePortfolio >= 3;

  const orderedModules = useMemo(() => {
    if (!prioritizeRiskPortfolio) return modules;
    const weight: Record<string, number> = {
      '/risk': 100 + usageRisk,
      '/portfolio': 100 + usagePortfolio,
      '/goals': -5,
    };
    return [...modules].sort((a, b) => (weight[b.path] || 0) - (weight[a.path] || 0));
  }, [prioritizeRiskPortfolio, usageRisk, usagePortfolio]);

  const trackModuleClick = (path: string) => {
    if (path === '/risk' || path === '/portfolio') {
      const key = path === '/risk' ? 'dashboard:module:risk' : 'dashboard:module:portfolio';
      const curr = Number(localStorage.getItem(key) || 0);
      localStorage.setItem(key, String(curr + 1));
    }
  };

  const chartData = nifty?.history?.slice(-30).map((h: any) => ({
    date:  h.date?.slice(5),
    price: Math.round(h.close),
  })) || [];

  useEffect(() => {
    if (chartData.length <= 1) return;
    const timer = window.setInterval(() => {
      setLineCursorIdx(prev => (prev + 1) % chartData.length);
    }, 320);
    return () => window.clearInterval(timer);
  }, [chartData.length]);

  if (loading) return <LoadingSkeleton />;

  const isUp = chartData.length > 1
    ? chartData[chartData.length - 1].price >= chartData[0].price
    : true;

  const signalStyle = SIGNAL_STYLE[signal?.signal] || SIGNAL_STYLE['HOLD'];

  return (
    <div className="space-y-5 max-w-6xl">

      {/* ── Header ─────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display font-bold" style={{ fontSize: 28, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Welcome back, {user?.full_name?.split(' ')[0] || 'Investor'}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
            Live market intelligence · Indian Financial Platform
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="live-dot" />
          <span className="num" style={{ fontSize: 11, color: 'var(--text-dim)' }}>LIVE DATA</span>
        </div>
      </div>

      {/* ── Market Ticker ───────────────────────────────────── */}
      {market && (
        <div className="card glass-card" style={{ padding: '16px 20px' }}>
          <div className="flex items-center gap-2 mb-3">
            <Activity size={12} style={{ color: 'var(--green)' }} />
            <span className="section-title">Live Market</span>
            <span className="live-dot" style={{ width: 6, height: 6 }} />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(market)
              .filter(([k]) => k !== 'from_cache')
              .map(([key, val]: any) => (
                <div key={key}>
                  <p className="section-title mb-1">{key.replace(/_/g, ' ')}</p>
                  <p className="num" style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
                    {typeof val?.price === 'number' ? val.price.toLocaleString('en-IN') : '—'}
                  </p>
                  <p className="num" style={{
                    fontSize: 12,
                    color: val?.direction === 'up' ? 'var(--green)' : 'var(--red)',
                    fontWeight: 600,
                  }}>
                    {val?.change_pct > 0 ? '+' : ''}{val?.change_pct?.toFixed(2)}%
                  </p>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* ── NIFTY Chart + Signal + AI Log ───────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">

        {/* Chart */}
        {chartData.length > 0 && (
          <div className="card glass-card md:col-span-2" style={{ padding: '20px' }}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <TrendingUp size={14} style={{ color: 'var(--cyan)' }} />
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>NIFTY 50</span>
                <span className="badge badge-blue" style={{ fontSize: 10 }}>30D Real Data</span>
              </div>
              <span className="num" style={{
                fontSize: 12,
                color: isUp ? 'var(--green)' : 'var(--red)',
                fontWeight: 600,
              }}>
                {isUp ? '▲' : '▼'} {chartData[chartData.length - 1]?.price?.toLocaleString('en-IN')}
              </span>
            </div>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={chartData}>
                <defs>
                  <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={isUp ? '#00F2FF' : '#c53b4a'} stopOpacity={0.32} />
                    <stop offset="95%" stopColor={isUp ? '#00F2FF' : '#c53b4a'} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="date" tick={{ fill: 'var(--text-dim)', fontSize: 10, fontFamily: 'Roboto Mono' }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: 'var(--text-dim)', fontSize: 10, fontFamily: 'Roboto Mono' }} tickLine={false} axisLine={false} domain={['auto', 'auto']} width={60} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-hover)', borderRadius: 10, fontFamily: 'Roboto Mono' }}
                  labelStyle={{ color: 'var(--text-muted)', fontSize: 10 }}
                  itemStyle={{ color: isUp ? 'var(--green)' : 'var(--red)', fontSize: 12 }}
                />
                <Line
                  type="monotone" dataKey="price"
                  stroke={isUp ? '#00F2FF' : 'var(--red)'}
                  strokeWidth={2} dot={false} activeDot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="transparent"
                  strokeWidth={0}
                  isAnimationActive={false}
                  dot={(props: any) => {
                    const { index, cx, cy } = props;
                    if (index !== lineCursorIdx) return <g />;
                    return (
                      <g>
                        <circle cx={cx} cy={cy} r={8} fill={isUp ? 'rgba(0,242,255,0.18)' : 'rgba(197,59,74,0.2)'} />
                        <circle cx={cx} cy={cy} r={4.5} fill={isUp ? '#00F2FF' : '#c53b4a'} />
                      </g>
                    );
                  }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* AI Signal */}
        {signal && (
          <div className="card glass-card md:col-span-1" style={{
            background: signal.signal?.includes('BUY')
              ? 'linear-gradient(135deg, rgba(16,217,138,0.06), var(--bg-card))'
              : signal.signal?.includes('SELL')
              ? 'linear-gradient(135deg, rgba(255,82,82,0.06), var(--bg-card))'
              : 'linear-gradient(135deg, rgba(255,192,71,0.06), var(--bg-card))',
            borderColor: signal.signal?.includes('BUY')
              ? 'rgba(16,217,138,0.2)'
              : signal.signal?.includes('SELL')
              ? 'rgba(255,82,82,0.2)'
              : 'rgba(255,192,71,0.2)',
          }}>
            <div className="flex items-center gap-2 mb-3">
              <Zap size={12} style={{ color: 'var(--accent)' }} />
              <span className="section-title">AI Signal</span>
            </div>
            <div className={`signal-pill ${signalStyle.cls} mb-4`} style={{ fontSize: 15 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: signalStyle.dotColor, display: 'inline-block', boxShadow: `0 0 6px ${signalStyle.dotColor}` }} />
              {signal.signal}
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.5 }}>
              {signal.recommendation}
            </p>
            <div className="space-y-2">
              {[
                { label: 'Regime',   value: signal.regime },
                { label: 'Score',    value: signal.score },
                { label: 'Geo Risk', value: signal.geo_risk, isRisk: true },
              ].map(row => (
                <div key={row.label} className="flex justify-between items-center">
                  <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>{row.label}</span>
                  <span className="num" style={{
                    fontSize: 11, fontWeight: 600,
                    color: row.isRisk
                      ? (signal.geo_risk > 0.5 ? 'var(--red)' : 'var(--green)')
                      : 'var(--text-primary)',
                  }}>
                    {row.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="card glass-card">
        <div className="flex items-center gap-2 mb-3">
          <BrainCircuit size={14} style={{ color: 'var(--accent)' }} />
          <span className="section-title">AI Active Thinking Log</span>
          <span className="badge badge-blue">LIVE</span>
        </div>
        <div className="max-h-44 overflow-y-auto space-y-2 pr-1">
          {aiLog.map((line, i) => (
            <p key={`${line}-${i}`} className={`num ${i === 0 ? 'typing-cursor' : ''}`} style={{ fontSize: 11, color: i === 0 ? 'var(--text-primary)' : 'var(--text-muted)' }}>
              {line}
            </p>
          ))}
        </div>
      </div>

      {/* ── Stat Row ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="neon-gradient-border rounded-2xl">
          <StatCard
            title="Risk Profile"
            value={risk?.profile_type || 'Not assessed'}
            subtitle={risk ? `Score: ${risk.score}/100` : 'Complete your assessment'}
            icon={<Shield size={16} />}
            color="blue"
            mono={false}
          />
        </div>
        <StatCard
          title="Market Sentiment"
          value={news?.market_sentiment || '—'}
          subtitle={news ? `${news.total_articles} articles · FinBERT` : ''}
          icon={<Newspaper size={16} />}
          color={news?.market_sentiment === 'Bullish' ? 'green' : news?.market_sentiment === 'Bearish' ? 'red' : 'yellow'}
          mono={false}
        />
        <StatCard
          title="Geo Risk Level"
          value={news?.geopolitical_risk?.level || 'Unknown'}
          subtitle={`Score: ${news?.geopolitical_risk?.max_score?.toFixed(2) || '0'}`}
          icon={<Globe size={16} />}
          color={news?.geopolitical_risk?.level === 'Critical' || news?.geopolitical_risk?.level === 'High' ? 'red' : 'yellow'}
          mono={false}
        />
      </div>

      {/* ── Module Grid ─────────────────────────────────────── */}
      <div>
        <p className="section-title mb-4">Platform Modules</p>
        {prioritizeRiskPortfolio && (
          <p className="num mb-3" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Adaptive layout active: prioritizing Risk and Portfolio based on usage behavior.
          </p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {orderedModules.map(({ path, label, icon: Icon, color, desc }, idx) => (
            <Link
              key={path}
              to={path}
              onClick={() => trackModuleClick(path)}
              style={{ textDecoration: 'none' }}
            >
              <div
                className="card"
                style={{
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  ...(prioritizeRiskPortfolio && idx < 2
                    ? { borderColor: 'var(--border-hover)', boxShadow: '0 0 0 1px var(--border-hover)' }
                    : {}),
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)';
                  (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-hover)';
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.transform = 'translateY(0)';
                  (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)';
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div style={{
                      width: 36, height: 36, borderRadius: 10,
                      background: `${color}14`,
                      border: `1px solid ${color}30`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: color,
                    }}>
                      <Icon size={16} />
                    </div>
                    <div>
                      <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{label}</p>
                      <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>{desc}</p>
                    </div>
                  </div>
                  <ArrowRight size={14} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* ── Onboarding CTA ──────────────────────────────────── */}
      {!risk && (
        <div className="card card-blue">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 14 }}>
                Complete Your Risk Assessment
              </p>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                Get personalized AI-driven investment recommendations based on your profile.
              </p>
            </div>
            <Link to="/risk">
              <button className="btn-primary" style={{ whiteSpace: 'nowrap', fontSize: 13 }}>
                Start Now <ArrowRight size={14} />
              </button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
