import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { authAPI, riskAPI, predictionAPI, newsAPI } from '../services/api';
import StatCard from '../components/StatCard';
import { Shield, TrendingUp, Newspaper, Target, PieChart, Receipt, Sunset, ArrowRight } from 'lucide-react';
export default function Dashboard() {
  const [user,setUser]=useState<any>(null);
  const [risk,setRisk]=useState<any>(null);
  const [regime,setRegime]=useState<any>(null);
  const [news,setNews]=useState<any>(null);
  const [loading,setLoading]=useState(true);
  useEffect(()=>{
    Promise.allSettled([authAPI.me(),riskAPI.getMyProfile(),predictionAPI.marketRegime(),newsAPI.marketSentiment()])
      .then(([u,r,reg,n])=>{
        if(u.status==='fulfilled') setUser(u.value.data);
        if(r.status==='fulfilled') setRisk(r.value.data);
        if(reg.status==='fulfilled') setRegime(reg.value.data);
        if(n.status==='fulfilled') setNews(n.value.data);
        setLoading(false);
      });
  },[]);
  if(loading) return <div className="flex items-center justify-center h-64"><div className="text-slate-400 animate-pulse">Loading dashboard...</div></div>;
  const modules = [
    {path:'/risk',label:'Risk Profile',icon:Shield,color:'blue',desc:'Assess your risk tolerance'},
    {path:'/portfolio',label:'Portfolio',icon:PieChart,color:'green',desc:'Optimize your investments'},
    {path:'/goals',label:'Goal Planner',icon:Target,color:'yellow',desc:'Plan your financial goals'},
    {path:'/retirement',label:'Retirement',icon:Sunset,color:'purple',desc:'Plan your retirement corpus'},
    {path:'/tax',label:'Tax Optimizer',icon:Receipt,color:'red',desc:'Minimize your tax liability'},
    {path:'/news',label:'News Intelligence',icon:Newspaper,color:'blue',desc:'AI-powered market news'},
  ];
  const colorMap: any = {blue:'bg-blue-500/20 text-blue-400',green:'bg-green-500/20 text-green-400',red:'bg-red-500/20 text-red-400',yellow:'bg-yellow-500/20 text-yellow-400',purple:'bg-purple-500/20 text-purple-400'};
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Welcome back, {user?.full_name?.split(' ')[0]||'Investor'} 👋</h1>
        <p className="text-slate-400 mt-1">Your AI-powered financial intelligence platform</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Risk Profile" value={risk?.profile_type||'Not assessed'} subtitle={risk?`Score: ${risk.score}/100`:'Complete assessment'} icon={<Shield size={20}/>} color="blue"/>
        <StatCard title="Market Regime" value={regime?.regime||'Loading...'} subtitle={regime?`${regime.confidence}% confidence`:''} icon={<TrendingUp size={20}/>} color={regime?.color==='green'?'green':regime?.color==='red'?'red':'yellow'}/>
        <StatCard title="Market Sentiment" value={news?.market_sentiment||'Loading...'} subtitle={news?`${news.total_articles} articles analyzed`:''} icon={<Newspaper size={20}/>} color="purple"/>
      </div>
      {regime && (
        <div className={`card border ${regime.color==='green'?'border-green-500/30 bg-green-500/5':regime.color==='red'?'border-red-500/30 bg-red-500/5':'border-yellow-500/30 bg-yellow-500/5'}`}>
          <div className="flex items-start gap-3">
            <div className="text-2xl">{regime.color==='green'?'🟢':regime.color==='red'?'🔴':'🟡'}</div>
            <div>
              <h3 className="font-semibold text-white">{regime.regime} Detected</h3>
              <p className="text-slate-400 text-sm mt-1">{regime.description}</p>
              <p className="text-blue-400 text-sm mt-1 font-medium">→ {regime.action}</p>
            </div>
          </div>
        </div>
      )}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Platform Modules</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {modules.map(({path,label,icon:Icon,color,desc})=>(
            <Link key={path} to={path} className="card group hover:border-slate-500 transition-all cursor-pointer">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg transition-all ${colorMap[color]}`}><Icon size={20}/></div>
                  <div><h3 className="font-semibold text-white">{label}</h3><p className="text-slate-400 text-sm mt-1">{desc}</p></div>
                </div>
                <ArrowRight size={16} className="text-slate-600 group-hover:text-slate-400 transition-all mt-1"/>
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
              <p className="text-slate-400 text-sm mt-1">Get personalized investment recommendations.</p>
            </div>
            <Link to="/risk" className="btn-primary shrink-0">Start Now</Link>
          </div>
        </div>
      )}
    </div>
  );
}
