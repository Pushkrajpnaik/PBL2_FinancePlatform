import React, { useEffect, useState } from 'react';
import { newsAPI } from '../services/api';
import { Newspaper, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';
export default function News() {
  const [sentiment,setSentiment]=useState<any>(null);
  const [alerts,setAlerts]=useState<any>(null);
  const [latest,setLatest]=useState<any>(null);
  const [loading,setLoading]=useState(true);
  const [text,setText]=useState('');
  const [analysis,setAnalysis]=useState<any>(null);
  useEffect(()=>{
    Promise.allSettled([newsAPI.marketSentiment(),newsAPI.riskAlerts(),newsAPI.latest('all')])
      .then(([s,a,l])=>{
        if(s.status==='fulfilled') setSentiment(s.value.data);
        if(a.status==='fulfilled') setAlerts(a.value.data);
        if(l.status==='fulfilled') setLatest(l.value.data);
        setLoading(false);
      });
  },[]);
  const analyzeText = async () => {
    if(!text) return;
    const res=await newsAPI.analyzeText(text);
    setAnalysis(res.data);
  };
  if(loading) return <div className="text-slate-400 animate-pulse">Loading news...</div>;
  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold text-white flex items-center gap-2"><Newspaper className="text-blue-500"/> News Intelligence</h1><p className="text-slate-400 mt-1">AI-powered financial news sentiment analysis</p></div>
      {sentiment&&(
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card"><p className="text-slate-400 text-sm">Market Sentiment</p><p className={`text-2xl font-bold mt-1 ${sentiment.market_sentiment==='Bullish'?'text-green-400':sentiment.market_sentiment==='Bearish'?'text-red-400':'text-yellow-400'}`}>{sentiment.market_sentiment}</p><p className="text-slate-500 text-xs mt-1">Score: {sentiment.overall_score}</p></div>
          <div className="card"><p className="text-slate-400 text-sm">Articles Analyzed</p><p className="text-2xl font-bold text-white mt-1">{sentiment.total_articles}</p></div>
          <div className="card"><p className="text-slate-400 text-sm">Risk Level</p><p className={`text-2xl font-bold mt-1 ${sentiment.risk_level?.level==='Low'?'text-green-400':sentiment.risk_level?.level==='High'?'text-red-400':'text-yellow-400'}`}>{sentiment.risk_level?.level}</p></div>
        </div>
      )}
      {alerts?.alerts?.length>0&&(
        <div className="card border border-red-500/30">
          <h3 className="font-semibold text-white flex items-center gap-2 mb-4"><AlertTriangle className="text-red-400" size={18}/>Risk Alerts ({alerts.total_alerts})</h3>
          <div className="space-y-3">
            {alerts.alerts.map((a:any,i:number)=>(
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-700/50 rounded-lg">
                <div className={`w-2 h-2 rounded-full mt-2 shrink-0 ${a.risk_level==='High'?'bg-red-400':'bg-orange-400'}`}/>
                <div><p className="text-white text-sm font-medium">{a.title}</p><p className="text-slate-400 text-xs mt-1">{a.source} • {a.risk_level} Risk</p><p className="text-blue-400 text-xs mt-1">{a.action}</p></div>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="card">
        <h3 className="font-semibold text-white mb-3">Analyze Any News Headline</h3>
        <div className="flex gap-2">
          <input className="input-field flex-1" placeholder="Enter a news headline to analyze..." value={text} onChange={e=>setText(e.target.value)}/>
          <button onClick={analyzeText} className="btn-primary shrink-0">Analyze</button>
        </div>
        {analysis&&(
          <div className="mt-4 p-4 bg-slate-700/50 rounded-lg">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{analysis.sentiment==='Positive'?'📈':analysis.sentiment==='Negative'?'📉':'➡️'}</span>
              <div>
                <p className={`font-semibold ${analysis.sentiment==='Positive'?'text-green-400':analysis.sentiment==='Negative'?'text-red-400':'text-yellow-400'}`}>{analysis.sentiment}</p>
                <p className="text-slate-400 text-sm">Score: {analysis.compound_score}</p>
              </div>
              <div className="ml-auto"><span className={`px-2 py-1 rounded text-xs font-medium ${analysis.risk_level?.level==='Low'?'badge-green':analysis.risk_level?.level==='High'?'badge-red':'badge-yellow'}`}>{analysis.risk_level?.level} Risk</span></div>
            </div>
          </div>
        )}
      </div>
      {latest&&(
        <div className="card">
          <h3 className="font-semibold text-white mb-4">Latest News with Sentiment</h3>
          <div className="space-y-3">
            {latest.news.map((n:any,i:number)=>(
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-700/50 rounded-lg">
                <div className="shrink-0 mt-1">{n.sentiment==='Positive'?<TrendingUp size={16} className="text-green-400"/>:n.sentiment==='Negative'?<TrendingDown size={16} className="text-red-400"/>:<span className="text-yellow-400 text-xs">→</span>}</div>
                <div className="flex-1"><p className="text-white text-sm">{n.title}</p><p className="text-slate-400 text-xs mt-1">{n.source}</p></div>
                <span className={`text-xs px-2 py-1 rounded shrink-0 ${n.sentiment==='Positive'?'badge-green':n.sentiment==='Negative'?'badge-red':'badge-yellow'}`}>{n.sentiment}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
