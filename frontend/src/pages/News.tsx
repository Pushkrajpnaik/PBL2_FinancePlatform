import React, { useEffect, useState } from 'react';
import { marketAPI, newsAPI } from '../services/api';
import { Newspaper, AlertTriangle, TrendingUp, TrendingDown, Globe, RefreshCw } from 'lucide-react';

const normalizeSentiment = (value?: string) => {
  const v = (value || '').toLowerCase();
  if (v.includes('pos')) return 'Positive';
  if (v.includes('neg')) return 'Negative';
  return 'Neutral';
};

const getStakeholderImpact = (article: any) => {
  const sentiment = normalizeSentiment(article?.sentiment);
  const score = Number(article?.finbert_score ?? article?.compound_score ?? 0);
  const confidence = Number(article?.finbert_confidence ?? 0);
  const riskLevel = article?.risk_level?.level || 'Neutral';
  const geoLevel = article?.geopolitical_risk?.level || 'Low';
  const sectors = Array.isArray(article?.sectors_detected) ? article.sectors_detected : [];

  const sectorText = sectors.length ? sectors.join(', ') : 'general market';
  const scoreStrength = Math.abs(score);
  const hasHighRisk = riskLevel === 'High' || geoLevel === 'Critical' || geoLevel === 'High';
  const hasClearSignal = scoreStrength >= 0.2 && confidence >= 0.55;

  if (hasHighRisk) {
    return {
      target: 'Investors & Owners',
      why: `High risk signal from FinBERT in ${sectorText}; potential downside needs allocation and business exposure review.`,
      finbertView: sentiment,
    };
  }

  if (sentiment === 'Positive' && hasClearSignal) {
    return {
      target: 'Owners',
      why: `FinBERT confidence is strong (${(confidence * 100).toFixed(0)}%) with positive tone in ${sectorText}, suggesting business momentum.`,
      finbertView: 'Positive',
    };
  }

  if (sentiment === 'Negative' && hasClearSignal) {
    return {
      target: 'Investors',
      why: `FinBERT reads negative with strong conviction in ${sectorText}, which can pressure valuations and near-term returns.`,
      finbertView: 'Negative',
    };
  }

  return {
    target: 'Investors & Owners',
    why: `FinBERT sentiment is mixed/low-conviction for ${sectorText}; wait for confirmation before major decisions.`,
    finbertView: 'Neutral',
  };
};

const getAnalysisImpact = (analysis: any) => {
  const sentiment = normalizeSentiment(analysis?.sentiment);
  const score = Number(analysis?.finbert_score ?? 0);
  const confidence = Number(analysis?.finbert_confidence ?? 0);
  const riskLevel = analysis?.risk_level?.level || 'Neutral';
  const geoLevel = analysis?.geopolitical_risk?.level || 'Low';
  const sectors = Array.isArray(analysis?.sectors_detected) ? analysis.sectors_detected : [];
  const sectorText = sectors.length ? sectors.join(', ') : 'general market';

  if (riskLevel === 'High' || geoLevel === 'Critical' || geoLevel === 'High') {
    return {
      target: 'Investors & Owners',
      why: `FinBERT flags elevated risk in ${sectorText}, so both portfolio positioning and business exposure need attention.`,
      finbertView: sentiment,
    };
  }

  if (sentiment === 'Positive' && Math.abs(score) >= 0.2 && confidence >= 0.55) {
    return {
      target: 'Owners',
      why: `Positive FinBERT signal with decent confidence indicates potential business momentum and operating upside.`,
      finbertView: 'Positive',
    };
  }

  if (sentiment === 'Negative' && Math.abs(score) >= 0.2 && confidence >= 0.55) {
    return {
      target: 'Investors',
      why: `Negative FinBERT signal with strong conviction can weigh on sentiment, valuations, and near-term investor returns.`,
      finbertView: 'Negative',
    };
  }

  return {
    target: 'Investors & Owners',
    why: `FinBERT is neutral or low conviction, so treat this as watchlist information until more confirmation appears.`,
    finbertView: 'Neutral',
  };
};

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

export default function News() {
  const [sentiment,  setSentiment]  = useState<any>(() => getCached('news:sentiment'));
  const [loading,    setLoading]    = useState<boolean>(() => !getCached('news:sentiment'));
  const [refreshing, setRefreshing] = useState(false);
  const [text,       setText]       = useState('');
  const [analysis,   setAnalysis]   = useState<any>(null);

  const fetchData = async (forceRefresh = false) => {
    try {
      const [s] = await Promise.allSettled([
        marketAPI.liveNews(forceRefresh),
      ]);
      if (s.status === 'fulfilled') {
        setSentiment(s.value.data);
        setCached('news:sentiment', s.value.data);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData(true);
  };

  const analyzeText = async () => {
    if (!text) return;
    const res = await newsAPI.analyzeText(text);
    setAnalysis(res.data);
  };

  if (loading) return <div className="text-slate-400 animate-pulse">Loading live news...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold flex items-center gap-2" style={{ fontSize: 28, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            <Newspaper className="text-blue-500" /> News Intelligence
          </h1>
          <p className="text-slate-400 mt-1">Live FinBERT sentiment analysis from Indian financial news</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          {refreshing ? 'Refreshing...' : 'Refresh News'}
        </button>
      </div>

      {/* Market Sentiment Overview */}
      {sentiment && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <p className="text-slate-400 text-sm">Market Sentiment</p>
            <p className={`text-2xl font-bold mt-1 ${
              sentiment.market_sentiment === 'Bullish' ? 'text-green-400' :
              sentiment.market_sentiment === 'Bearish' ? 'text-red-400' : 'text-yellow-400'
            }`}>{sentiment.market_sentiment}</p>
            <p className="text-slate-500 text-xs mt-1">Score: {sentiment.overall_score?.toFixed(4)}</p>
          </div>
          <div className="card">
            <p className="text-slate-400 text-sm">Articles Analyzed</p>
            <p className="text-2xl font-bold text-white mt-1">{sentiment.total_articles}</p>
            <p className="text-slate-500 text-xs mt-1">{sentiment.model_used || 'FinBERT'}</p>
          </div>
          <div className="card">
            <p className="text-slate-400 text-sm">Risk Level</p>
            <p className={`text-2xl font-bold mt-1 ${
              sentiment.risk_level?.level === 'Low' ? 'text-green-400' :
              sentiment.risk_level?.level === 'High' ? 'text-red-400' : 'text-yellow-400'
            }`}>{sentiment.risk_level?.level || 'Neutral'}</p>
          </div>
          <div className="card border border-red-500/30">
            <p className="text-slate-400 text-sm flex items-center gap-1">
              <Globe size={12} /> Geo Risk
            </p>
            <p className={`text-2xl font-bold mt-1 ${
              sentiment.geopolitical_risk?.level === 'Critical' ? 'text-red-400' :
              sentiment.geopolitical_risk?.level === 'High' ? 'text-orange-400' : 'text-yellow-400'
            }`}>{sentiment.geopolitical_risk?.level || 'Low'}</p>
            <p className="text-slate-500 text-xs mt-1">Score: {sentiment.geopolitical_risk?.max_score?.toFixed(2)}</p>
          </div>
        </div>
      )}

      {/* Sector Sentiment */}
      {sentiment?.sector_sentiment && (
        <div className="card">
          <h3 className="font-semibold text-white mb-4">Sector Sentiment (Live)</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(sentiment.sector_sentiment).map(([sector, data]: any) => (
              <div key={sector} className={`p-3 rounded-lg border ${
                data.sentiment === 'Positive' ? 'border-green-500/30 bg-green-500/5' :
                data.sentiment === 'Negative' ? 'border-red-500/30 bg-red-500/5' :
                'border-slate-700 bg-slate-700/30'
              }`}>
                <p className="text-slate-400 text-xs capitalize">{sector}</p>
                <p className={`font-semibold text-sm mt-1 ${
                  data.sentiment === 'Positive' ? 'text-green-400' :
                  data.sentiment === 'Negative' ? 'text-red-400' : 'text-yellow-400'
                }`}>{data.sentiment}</p>
                <p className="text-slate-500 text-xs">{data.articles} articles</p>
                <p className={`text-xs font-medium mt-1 ${
                  data.signal === 'OVERWEIGHT' ? 'text-green-400' :
                  data.signal === 'UNDERWEIGHT' ? 'text-red-400' : 'text-slate-400'
                }`}>{data.signal}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Alerts */}
      {sentiment?.risk_alerts?.length > 0 && (
        <div className="card border border-red-500/30">
          <h3 className="font-semibold text-white flex items-center gap-2 mb-4">
            <AlertTriangle className="text-red-400" size={18} />
            Risk Alerts ({sentiment.total_risk_alerts})
          </h3>
          <div className="space-y-3">
            {sentiment.risk_alerts.slice(0, 5).map((a: any, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-700/50 rounded-lg">
                <div className={`w-2 h-2 rounded-full mt-2 shrink-0 ${
                  a.risk_level?.level === 'High' ? 'bg-red-400' : 'bg-orange-400'
                }`} />
                <div className="flex-1">
                  <p className="text-white text-sm font-medium">{a.title}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <p className="text-slate-400 text-xs">{a.source}</p>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      a.geopolitical_risk?.level === 'Critical' ? 'bg-red-500/20 text-red-400' :
                      a.geopolitical_risk?.level === 'High' ? 'bg-orange-500/20 text-orange-400' :
                      'bg-slate-700 text-slate-400'
                    }`}>{a.geopolitical_risk?.level || 'Low'} Geo Risk</span>
                  </div>
                  <p className="text-blue-400 text-xs mt-1">{a.risk_level?.action}</p>
                </div>
                <span className={`text-sm font-bold shrink-0 ${a.compound_score > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {a.compound_score?.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analyze Custom Text */}
      <div className="card">
        <h3 className="font-semibold text-white mb-3">Analyze Any News with FinBERT</h3>
        <div className="flex gap-2">
          <input
            className="input-field flex-1"
            placeholder="Enter a news headline to analyze with FinBERT..."
            value={text}
            onChange={e => setText(e.target.value)}
          />
          <button onClick={analyzeText} className="btn-primary shrink-0">Analyze</button>
        </div>
        {analysis && (
          <div className="mt-4 p-4 bg-slate-700/50 rounded-lg">
            {(() => {
              const impact = getAnalysisImpact(analysis);
              return (
                <>
            <div className="flex items-center gap-3">
              <span className="text-2xl">
                {analysis.sentiment === 'Positive' ? '📈' : analysis.sentiment === 'Negative' ? '📉' : '➡️'}
              </span>
              <div className="flex-1">
                <p className={`font-semibold ${
                  analysis.sentiment === 'Positive' ? 'text-green-400' :
                  analysis.sentiment === 'Negative' ? 'text-red-400' : 'text-yellow-400'
                }`}>{analysis.sentiment}</p>
                <p className="text-slate-400 text-sm">
                  FinBERT Score: {analysis.finbert_score?.toFixed(4)} |
                  Confidence: {(analysis.finbert_confidence * 100)?.toFixed(1)}% |
                  Model: {analysis.model_used}
                </p>
              </div>
              <div className="text-right">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  analysis.risk_level?.level === 'Low' ? 'badge-green' :
                  analysis.risk_level?.level === 'High' ? 'badge-red' : 'badge-yellow'
                }`}>{analysis.risk_level?.level} Risk</span>
                {analysis.geopolitical_risk?.level !== 'Low' && (
                  <p className="text-orange-400 text-xs mt-1">⚠️ Geo Risk: {analysis.geopolitical_risk?.level}</p>
                )}
              </div>
            </div>
            <div className="mt-3 border-t border-slate-600/50 pt-3">
              <p className="text-xs text-slate-300">
                FinBERT: <span className={`font-medium ${
                  impact.finbertView === 'Positive' ? 'text-green-400' :
                  impact.finbertView === 'Negative' ? 'text-red-400' : 'text-yellow-400'
                }`}>{impact.finbertView}</span>
                {' '}for <span className="text-blue-300 font-medium">{impact.target}</span>
              </p>
              <p className="text-xs text-slate-400 mt-1">{impact.why}</p>
            </div>
                </>
              );
            })()}
          </div>
        )}
      </div>

      {/* Latest News Feed */}
      {sentiment?.articles && (
        <div className="card">
          <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
            Live News Feed
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
          </h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {sentiment.articles.slice(0, 15).map((n: any, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-700/50 rounded-lg">
                <div className="shrink-0 mt-1">
                  {n.sentiment === 'Positive' ?
                    <TrendingUp size={16} className="text-green-400" /> :
                    n.sentiment === 'Negative' ?
                    <TrendingDown size={16} className="text-red-400" /> :
                    <span className="text-yellow-400 text-xs font-bold">→</span>
                  }
                </div>
                <div className="flex-1 min-w-0">
                  {(() => {
                    const impact = getStakeholderImpact(n);
                    return (
                      <>
                  <p className="text-white text-sm truncate">{n.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-slate-400 text-xs">{n.source}</p>
                    <span className="text-slate-600 text-xs">•</span>
                    <p className="text-slate-500 text-xs">{n.sectors_detected?.join(', ')}</p>
                  </div>
                  <div className="mt-2 space-y-1">
                    <p className="text-xs text-slate-300">
                      FinBERT: <span className={`font-medium ${
                        impact.finbertView === 'Positive' ? 'text-green-400' :
                        impact.finbertView === 'Negative' ? 'text-red-400' : 'text-yellow-400'
                      }`}>{impact.finbertView}</span>
                      {' '}for <span className="text-blue-300 font-medium">{impact.target}</span>
                    </p>
                    <p className="text-xs text-slate-400">{impact.why}</p>
                  </div>
                      </>
                    );
                  })()}
                </div>
                <div className="shrink-0 text-right">
                  <span className={`text-xs px-2 py-1 rounded ${
                    n.sentiment === 'Positive' ? 'badge-green' :
                    n.sentiment === 'Negative' ? 'badge-red' : 'badge-yellow'
                  }`}>{n.sentiment}</span>
                  <p className="text-slate-500 text-xs mt-1">{n.compound_score?.toFixed(3)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}