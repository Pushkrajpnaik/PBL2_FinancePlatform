import os

BASE = r"C:\Users\sidha\ai-finance-platform\frontend\src"

files = {}

# ─── tailwind.config.js ───────────────────────────────────────────────────────
files[r"C:\Users\sidha\ai-finance-platform\frontend\tailwind.config.js"] = r"""/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
}
"""

# ─── postcss.config.js ────────────────────────────────────────────────────────
files[r"C:\Users\sidha\ai-finance-platform\frontend\postcss.config.js"] = r"""module.exports = {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
"""

# ─── tsconfig.json ────────────────────────────────────────────────────────────
files[r"C:\Users\sidha\ai-finance-platform\frontend\tsconfig.json"] = r"""{
  "compilerOptions": {
    "target": "es6",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": false,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "typeRoots": ["./node_modules/@types"]
  },
  "include": ["src"],
  "exclude": ["node_modules"]
}
"""

# ─── index.css ────────────────────────────────────────────────────────────────
files[BASE + r"\index.css"] = r"""@tailwind base;
@tailwind components;
@tailwind utilities;

* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0f172a; color: #e2e8f0; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #1e293b; }
::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
.card { @apply bg-slate-800 rounded-xl p-6 border border-slate-700; }
.btn-primary { @apply bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200; }
.btn-secondary { @apply bg-slate-700 hover:bg-slate-600 text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200; }
.input-field { @apply w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500; }
.label { @apply block text-sm font-medium text-slate-400 mb-1; }
.badge-green { @apply bg-green-500/20 text-green-400 px-2 py-1 rounded-full text-xs font-medium; }
.badge-red { @apply bg-red-500/20 text-red-400 px-2 py-1 rounded-full text-xs font-medium; }
.badge-yellow { @apply bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded-full text-xs font-medium; }
.badge-blue { @apply bg-blue-500/20 text-blue-400 px-2 py-1 rounded-full text-xs font-medium; }
"""

# ─── services/api.ts ──────────────────────────────────────────────────────────
os.makedirs(BASE + r"\services", exist_ok=True)
files[BASE + r"\services\api.ts"] = r"""import axios from 'axios';
const API_BASE = 'http://localhost:8000/api/v1';
const api = axios.create({ baseURL: API_BASE, headers: { 'Content-Type': 'application/json' } });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) { localStorage.removeItem('token'); window.location.href = '/login'; }
    return Promise.reject(error);
  }
);
export const authAPI = {
  register: (data: any) => api.post('/auth/register', data),
  login:    (data: any) => api.post('/auth/login', data),
  me:       ()          => api.get('/users/me'),
};
export const riskAPI = {
  getQuestionnaire: ()          => api.get('/risk/questionnaire'),
  assess:           (data: any) => api.post('/risk/assess', data),
  getMyProfile:     ()          => api.get('/risk/me'),
};
export const simulationAPI = {
  run:   (data: any) => api.post('/simulation/run', data),
  quick: ()          => api.post('/simulation/quick'),
};
export const portfolioAPI = {
  optimize:    (data: any) => api.post('/portfolio/optimize', data),
  optimizeAll: (data: any) => api.post('/portfolio/optimize/all', data),
  myPortfolio: ()          => api.get('/portfolio/my-portfolio'),
};
export const goalsAPI = {
  getTemplates: ()          => api.get('/goals/templates'),
  analyze:      (data: any) => api.post('/goals/analyze', data),
  save:         (data: any) => api.post('/goals/save', data),
  myGoals:      ()          => api.get('/goals/my-goals'),
};
export const retirementAPI = {
  calculate: (data: any) => api.post('/retirement/calculate', data),
  save:      (data: any) => api.post('/retirement/save', data),
  myPlan:    ()          => api.get('/retirement/my-plan'),
};
export const taxAPI = {
  capitalGains:       (data: any) => api.post('/tax/capital-gains', data),
  optimize80c:        (data: any) => api.post('/tax/optimize-80c', data),
  afterTaxComparison: (data: any) => api.post('/tax/after-tax-comparison', data),
  getRules:           ()          => api.get('/tax/rules'),
};
export const newsAPI = {
  marketSentiment: ()               => api.get('/news/market-sentiment'),
  latest:          (cat: string)    => api.get(`/news/latest?category=${cat}`),
  analyzeText:     (text: string)   => api.post('/news/analyze-text', { text }),
  riskAlerts:      ()               => api.get('/news/risk-alerts'),
  sectorSentiment: (sector: string) => api.get(`/news/sector-sentiment/${sector}`),
};
export const predictionAPI = {
  marketRegime:            () => api.get('/prediction/market-regime'),
  regimeAdjustedPortfolio: () => api.get('/prediction/regime-adjusted-portfolio'),
};
export default api;
"""

# ─── components/StatCard.tsx ──────────────────────────────────────────────────
os.makedirs(BASE + r"\components", exist_ok=True)
files[BASE + r"\components\StatCard.tsx"] = r"""import React from 'react';
interface StatCardProps { title: string; value: string; subtitle?: string; icon?: React.ReactNode; color?: 'blue'|'green'|'red'|'yellow'|'purple'; }
const colorMap: any = { blue:'bg-blue-500/20 text-blue-400', green:'bg-green-500/20 text-green-400', red:'bg-red-500/20 text-red-400', yellow:'bg-yellow-500/20 text-yellow-400', purple:'bg-purple-500/20 text-purple-400' };
export default function StatCard({ title, value, subtitle, icon, color='blue' }: StatCardProps) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {subtitle && <p className="text-slate-500 text-xs mt-1">{subtitle}</p>}
        </div>
        {icon && <div className={`p-3 rounded-lg ${colorMap[color]}`}>{icon}</div>}
      </div>
    </div>
  );
}
"""

# ─── components/Layout.tsx ────────────────────────────────────────────────────
files[BASE + r"\components\Layout.tsx"] = r"""import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Shield, PieChart, Target, Sunset, Receipt, Newspaper, LogOut, Menu, X, TrendingUp } from 'lucide-react';
const navItems = [
  { path:'/',           label:'Dashboard',    icon:LayoutDashboard },
  { path:'/risk',       label:'Risk Profile', icon:Shield },
  { path:'/portfolio',  label:'Portfolio',    icon:PieChart },
  { path:'/goals',      label:'Goals',        icon:Target },
  { path:'/retirement', label:'Retirement',   icon:Sunset },
  { path:'/tax',        label:'Tax',          icon:Receipt },
  { path:'/news',       label:'News',         icon:Newspaper },
];
export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(true);
  const logout = () => { localStorage.removeItem('token'); navigate('/login'); };
  return (
    <div className="flex h-screen bg-slate-900 overflow-hidden">
      <aside className={`${open?'w-64':'w-16'} bg-slate-800 border-r border-slate-700 flex flex-col transition-all duration-300`}>
        <div className="flex items-center gap-3 p-4 border-b border-slate-700">
          <TrendingUp className="text-blue-500 shrink-0" size={24} />
          {open && <span className="font-bold text-white text-sm">AI Finance Platform</span>}
        </div>
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link key={path} to={path} className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${location.pathname===path?'bg-blue-600 text-white':'text-slate-400 hover:bg-slate-700 hover:text-white'}`}>
              <Icon size={18} className="shrink-0" />
              {open && <span className="text-sm font-medium">{label}</span>}
            </Link>
          ))}
        </nav>
        <div className="p-2 border-t border-slate-700 space-y-1">
          <button onClick={()=>setOpen(!open)} className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-400 hover:bg-slate-700 hover:text-white w-full transition-all">
            {open?<X size={18}/>:<Menu size={18}/>}
            {open && <span className="text-sm">Collapse</span>}
          </button>
          <button onClick={logout} className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-400 hover:bg-red-500/20 hover:text-red-400 w-full transition-all">
            <LogOut size={18} className="shrink-0" />
            {open && <span className="text-sm">Logout</span>}
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
"""

# ─── pages/Login.tsx ──────────────────────────────────────────────────────────
os.makedirs(BASE + r"\pages", exist_ok=True)
files[BASE + r"\pages\Login.tsx"] = r"""import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';
import { TrendingUp, Mail, Lock } from 'lucide-react';
export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email:'', password:'' });
  const [loading, setLoading] = useState(false);
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true);
    try {
      const res = await authAPI.login(form);
      localStorage.setItem('token', res.data.access_token);
      toast.success('Welcome back!');
      navigate('/');
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Login failed'); }
    finally { setLoading(false); }
  };
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <TrendingUp className="text-blue-500" size={32} />
            <span className="text-2xl font-bold text-white">AI Finance</span>
          </div>
          <p className="text-slate-400">Your autonomous wealth manager</p>
        </div>
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-6">Sign In</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-3 text-slate-400" />
                <input type="email" className="input-field pl-9" placeholder="you@example.com" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} required />
              </div>
            </div>
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-3 text-slate-400" />
                <input type="password" className="input-field pl-9" placeholder="••••••••" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} required />
              </div>
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading}>{loading?'Signing in...':'Sign In'}</button>
          </form>
          <p className="text-center text-slate-400 text-sm mt-4">Don't have an account? <Link to="/register" className="text-blue-400 hover:text-blue-300">Register</Link></p>
        </div>
      </div>
    </div>
  );
}
"""

# ─── pages/Register.tsx ───────────────────────────────────────────────────────
files[BASE + r"\pages\Register.tsx"] = r"""import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';
import { TrendingUp, Mail, Lock, User } from 'lucide-react';
export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email:'', full_name:'', password:'' });
  const [loading, setLoading] = useState(false);
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true);
    try {
      await authAPI.register(form);
      toast.success('Account created! Please login.');
      navigate('/login');
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Registration failed'); }
    finally { setLoading(false); }
  };
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <TrendingUp className="text-blue-500" size={32} />
            <span className="text-2xl font-bold text-white">AI Finance</span>
          </div>
          <p className="text-slate-400">Create your account</p>
        </div>
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-6">Create Account</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Full Name</label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-3 text-slate-400" />
                <input type="text" className="input-field pl-9" placeholder="John Doe" value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})} required />
              </div>
            </div>
            <div>
              <label className="label">Email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-3 text-slate-400" />
                <input type="email" className="input-field pl-9" placeholder="you@example.com" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} required />
              </div>
            </div>
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-3 text-slate-400" />
                <input type="password" className="input-field pl-9" placeholder="••••••••" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} required />
              </div>
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading}>{loading?'Creating account...':'Create Account'}</button>
          </form>
          <p className="text-center text-slate-400 text-sm mt-4">Already have an account? <Link to="/login" className="text-blue-400 hover:text-blue-300">Sign In</Link></p>
        </div>
      </div>
    </div>
  );
}
"""

# ─── pages/Dashboard.tsx ──────────────────────────────────────────────────────
files[BASE + r"\pages\Dashboard.tsx"] = r"""import React, { useEffect, useState } from 'react';
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
"""

# ─── pages/RiskProfile.tsx ────────────────────────────────────────────────────
files[BASE + r"\pages\RiskProfile.tsx"] = r"""import React, { useState, useEffect } from 'react';
import { riskAPI } from '../services/api';
import toast from 'react-hot-toast';
import { Shield, CheckCircle } from 'lucide-react';
export default function RiskProfile() {
  const [questionnaire,setQuestionnaire]=useState<any>(null);
  const [answers,setAnswers]=useState<any>({});
  const [result,setResult]=useState<any>(null);
  const [loading,setLoading]=useState(false);
  const [saved,setSaved]=useState<any>(null);
  useEffect(()=>{
    riskAPI.getQuestionnaire().then(r=>setQuestionnaire(r.data));
    riskAPI.getMyProfile().then(r=>setSaved(r.data)).catch(()=>{});
  },[]);
  const handleSubmit = async () => {
    if(Object.keys(answers).length<10){toast.error('Please answer all 10 questions');return;}
    setLoading(true);
    try{const res=await riskAPI.assess(answers);setResult(res.data);setSaved(res.data);toast.success('Risk profile assessed!');}
    catch(err:any){toast.error('Assessment failed');}
    finally{setLoading(false);}
  };
  const profileColors:any={Conservative:'text-blue-400',Moderate:'text-yellow-400',Aggressive:'text-red-400'};
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2"><Shield className="text-blue-500"/> Risk Profile Assessment</h1>
        <p className="text-slate-400 mt-1">Answer 10 questions to get your personalized risk profile</p>
      </div>
      {saved&&!result&&(
        <div className="card border border-blue-500/30">
          <h3 className="font-semibold text-white mb-2">Your Current Profile</h3>
          <div className="flex items-center gap-4">
            <div><p className={`text-3xl font-bold ${profileColors[saved.profile_type]}`}>{saved.profile_type}</p><p className="text-slate-400 text-sm">Score: {saved.score}/100</p></div>
            <div className="flex-1"><p className="text-slate-300 text-sm">{saved.description}</p></div>
          </div>
        </div>
      )}
      {result&&(
        <div className="card border border-green-500/30 bg-green-500/5">
          <div className="flex items-center gap-2 mb-4"><CheckCircle className="text-green-400" size={20}/><h3 className="font-semibold text-white">Assessment Complete!</h3></div>
          <div className="grid grid-cols-2 gap-4">
            <div><p className="text-slate-400 text-sm">Your Profile</p><p className={`text-3xl font-bold ${profileColors[result.profile_type]}`}>{result.profile_type}</p><p className="text-slate-400 text-sm mt-1">Score: {result.score}/100</p></div>
            <div><p className="text-slate-400 text-sm mb-2">Recommended Allocation</p>
              {Object.entries(result.recommended_allocation).map(([k,v]:any)=>(
                <div key={k} className="flex justify-between text-sm mb-1"><span className="text-slate-300 capitalize">{k.replace(/_/g,' ')}</span><span className="text-white font-medium">{v}%</span></div>
              ))}
            </div>
          </div>
          <p className="text-slate-400 text-sm mt-4">{result.description}</p>
        </div>
      )}
      {questionnaire&&(
        <div className="space-y-4">
          {questionnaire.questions.map((q:any,i:number)=>(
            <div key={q.id} className="card">
              <p className="text-white font-medium mb-3">{i+1}. {q.question}</p>
              <div className="space-y-2">
                {Object.entries(q.options).map(([val,label]:any)=>(
                  <button key={val} onClick={()=>setAnswers({...answers,[q.id]:parseInt(val)})} className={`w-full text-left px-4 py-2 rounded-lg text-sm transition-all ${answers[q.id]===parseInt(val)?'bg-blue-600 text-white':'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}>{label}</button>
                ))}
              </div>
            </div>
          ))}
          <button onClick={handleSubmit} disabled={loading} className="btn-primary w-full py-3 text-lg">
            {loading?'Analyzing...':`Submit Assessment (${Object.keys(answers).length}/10)`}
          </button>
        </div>
      )}
    </div>
  );
}
"""

# ─── pages/Portfolio.tsx ──────────────────────────────────────────────────────
files[BASE + r"\pages\Portfolio.tsx"] = r"""import React, { useState } from 'react';
import { portfolioAPI } from '../services/api';
import toast from 'react-hot-toast';
import { PieChart } from 'lucide-react';
import { PieChart as RechartsPie, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
const COLORS = ['#3b82f6','#22c55e','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#f97316'];
export default function Portfolio() {
  const [form,setForm]=useState({risk_profile:'Moderate',method:'markowitz',investment_amount:1000000});
  const [result,setResult]=useState<any>(null);
  const [allResults,setAllResults]=useState<any>(null);
  const [loading,setLoading]=useState(false);
  const handleOptimize = async () => {
    setLoading(true);
    try{
      const [r1,r2]=await Promise.all([portfolioAPI.optimize(form),portfolioAPI.optimizeAll(form)]);
      setResult(r1.data); setAllResults(r2.data);
      toast.success('Portfolio optimized!');
    }catch(err:any){toast.error('Optimization failed');}
    finally{setLoading(false);}
  };
  const pieData = result ? Object.entries(result.allocation).map(([k,v]:any)=>({name:k.replace(/_/g,' '),value:v})) : [];
  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold text-white flex items-center gap-2"><PieChart className="text-green-500"/> Portfolio Optimizer</h1><p className="text-slate-400 mt-1">AI-powered portfolio optimization using 4 algorithms</p></div>
      <div className="card">
        <h3 className="font-semibold text-white mb-4">Configure Portfolio</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div><label className="label">Risk Profile</label>
            <select className="input-field" value={form.risk_profile} onChange={e=>setForm({...form,risk_profile:e.target.value})}>
              <option>Conservative</option><option>Moderate</option><option>Aggressive</option>
            </select>
          </div>
          <div><label className="label">Method</label>
            <select className="input-field" value={form.method} onChange={e=>setForm({...form,method:e.target.value})}>
              <option value="markowitz">Markowitz</option><option value="risk_parity">Risk Parity</option><option value="cvar">CVaR</option><option value="black_litterman">Black-Litterman</option>
            </select>
          </div>
          <div><label className="label">Investment Amount (₹)</label>
            <input type="number" className="input-field" value={form.investment_amount} onChange={e=>setForm({...form,investment_amount:Number(e.target.value)})}/>
          </div>
        </div>
        <button onClick={handleOptimize} disabled={loading} className="btn-primary mt-4">{loading?'Optimizing...':'Optimize Portfolio'}</button>
      </div>
      {result&&(
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Allocation Chart</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsPie><Pie data={pieData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({name,value})=>`${name} ${value}%`}>
                {pieData.map((_:any,i:number)=><Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
              </Pie><Tooltip/></RechartsPie>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Results</h3>
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-slate-400">Method</span><span className="text-white font-medium">{result.method}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Expected Return</span><span className="text-green-400 font-medium">{result.expected_return}%</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Expected Risk</span><span className="text-yellow-400 font-medium">{result.expected_risk}%</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Sharpe Ratio</span><span className="text-blue-400 font-medium">{result.sharpe_ratio}</span></div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-700">
              <p className="text-slate-400 text-sm mb-2">Allocated Amounts</p>
              {result.allocated_amounts&&Object.entries(result.allocated_amounts).map(([k,v]:any)=>(
                <div key={k} className="flex justify-between text-sm mb-1"><span className="text-slate-300 capitalize">{k.replace(/_/g,' ')}</span><span className="text-white">₹{v.toLocaleString()}</span></div>
              ))}
            </div>
          </div>
        </div>
      )}
      {allResults&&(
        <div className="card">
          <h3 className="font-semibold text-white mb-4">Algorithm Comparison</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {['markowitz','risk_parity','cvar','black_litterman'].map(m=>{
              const r=allResults[m];
              const isRecommended=allResults.recommended?.method===r?.method;
              return r?(
                <div key={m} className={`p-4 rounded-lg border ${isRecommended?'border-green-500/50 bg-green-500/5':'border-slate-700 bg-slate-700/50'}`}>
                  {isRecommended&&<span className="badge-green mb-2 block">Recommended</span>}
                  <p className="text-white font-medium text-sm capitalize">{m.replace(/_/g,' ')}</p>
                  <p className="text-green-400 text-sm mt-1">Return: {r.expected_return}%</p>
                  <p className="text-yellow-400 text-sm">Risk: {r.expected_risk}%</p>
                  <p className="text-blue-400 text-sm">Sharpe: {r.sharpe_ratio}</p>
                </div>
              ):null;
            })}
          </div>
        </div>
      )}
    </div>
  );
}
"""

# ─── pages/Goals.tsx ──────────────────────────────────────────────────────────
files[BASE + r"\pages\Goals.tsx"] = r"""import React, { useState, useEffect } from 'react';
import { goalsAPI } from '../services/api';
import toast from 'react-hot-toast';
import { Target, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
export default function Goals() {
  const [form,setForm]=useState({goal_type:'home_purchase',target_amount:5000000,current_savings:500000,monthly_investment:25000,time_horizon_years:7,inflation_rate:6.0,risk_profile:'Moderate'});
  const [result,setResult]=useState<any>(null);
  const [templates,setTemplates]=useState<any[]>([]);
  const [loading,setLoading]=useState(false);
  useEffect(()=>{ goalsAPI.getTemplates().then(r=>setTemplates(r.data.templates)).catch(()=>{}); },[]);
  const handleAnalyze = async () => {
    setLoading(true);
    try{ const res=await goalsAPI.analyze(form); setResult(res.data); toast.success('Goal analyzed!'); }
    catch(err:any){ toast.error('Analysis failed'); }
    finally{ setLoading(false); }
  };
  const handleSave = async () => {
    try{ await goalsAPI.save(form); toast.success('Goal saved!'); }
    catch(err:any){ toast.error('Save failed'); }
  };
  const statusIcon:any={
    'On Track':<CheckCircle className="text-green-400" size={20}/>,
    'Needs Attention':<AlertTriangle className="text-yellow-400" size={20}/>,
    'At Risk':<XCircle className="text-red-400" size={20}/>,
  };
  return (
    <div className="space-y-6 max-w-4xl">
      <div><h1 className="text-2xl font-bold text-white flex items-center gap-2"><Target className="text-yellow-500"/> Goal-Based Investment Planner</h1><p className="text-slate-400 mt-1">Plan and track your financial goals with Monte Carlo simulation</p></div>
      <div className="card">
        <h3 className="font-semibold text-white mb-4">Configure Your Goal</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label className="label">Goal Type</label>
            <select className="input-field" value={form.goal_type} onChange={e=>setForm({...form,goal_type:e.target.value})}>
              {templates.map(t=><option key={t.goal_type} value={t.goal_type}>{t.icon} {t.name}</option>)}
            </select>
          </div>
          <div><label className="label">Risk Profile</label>
            <select className="input-field" value={form.risk_profile} onChange={e=>setForm({...form,risk_profile:e.target.value})}>
              <option>Conservative</option><option>Moderate</option><option>Aggressive</option>
            </select>
          </div>
          <div><label className="label">Target Amount (₹)</label><input type="number" className="input-field" value={form.target_amount} onChange={e=>setForm({...form,target_amount:Number(e.target.value)})}/></div>
          <div><label className="label">Current Savings (₹)</label><input type="number" className="input-field" value={form.current_savings} onChange={e=>setForm({...form,current_savings:Number(e.target.value)})}/></div>
          <div><label className="label">Monthly Investment (₹)</label><input type="number" className="input-field" value={form.monthly_investment} onChange={e=>setForm({...form,monthly_investment:Number(e.target.value)})}/></div>
          <div><label className="label">Time Horizon (Years)</label><input type="number" className="input-field" value={form.time_horizon_years} onChange={e=>setForm({...form,time_horizon_years:Number(e.target.value)})}/></div>
          <div><label className="label">Inflation Rate (%)</label><input type="number" className="input-field" value={form.inflation_rate} onChange={e=>setForm({...form,inflation_rate:Number(e.target.value)})}/></div>
        </div>
        <div className="flex gap-3 mt-4">
          <button onClick={handleAnalyze} disabled={loading} className="btn-primary">{loading?'Analyzing...':'Analyze Goal'}</button>
          {result&&<button onClick={handleSave} className="btn-secondary">Save Goal</button>}
        </div>
      </div>
      {result&&(
        <div className="space-y-4">
          <div className={`card border ${result.recommendation?.color==='green'?'border-green-500/30 bg-green-500/5':result.recommendation?.color==='red'?'border-red-500/30 bg-red-500/5':'border-yellow-500/30 bg-yellow-500/5'}`}>
            <div className="flex items-center gap-3 mb-4">
              {statusIcon[result.recommendation?.status]}
              <h3 className="font-semibold text-white">{result.recommendation?.status}</h3>
            </div>
            <p className="text-slate-300 text-sm">{result.recommendation?.message}</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card"><p className="text-slate-400 text-sm">Success Probability</p><p className="text-2xl font-bold text-white mt-1">{result.success_probability}%</p></div>
            <div className="card"><p className="text-slate-400 text-sm">Required SIP</p><p className="text-2xl font-bold text-white mt-1">₹{result.required_sip?.toLocaleString()}</p></div>
            <div className="card"><p className="text-slate-400 text-sm">Inflation Adjusted Target</p><p className="text-2xl font-bold text-white mt-1">₹{result.inflation_adjusted_target?.toLocaleString()}</p></div>
            <div className="card"><p className="text-slate-400 text-sm">Shortfall Risk</p><p className="text-2xl font-bold text-red-400 mt-1">{result.shortfall_risk}%</p></div>
          </div>
          <div className="card">
            <h3 className="font-semibold text-white mb-4">Monte Carlo Scenarios (10,000 simulations)</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-red-500/10 rounded-lg"><p className="text-slate-400 text-sm">Worst Case</p><p className="text-red-400 text-xl font-bold mt-1">₹{result.monte_carlo?.worst_case?.toLocaleString()}</p></div>
              <div className="text-center p-4 bg-blue-500/10 rounded-lg"><p className="text-slate-400 text-sm">Median</p><p className="text-blue-400 text-xl font-bold mt-1">₹{result.monte_carlo?.median?.toLocaleString()}</p></div>
              <div className="text-center p-4 bg-green-500/10 rounded-lg"><p className="text-slate-400 text-sm">Best Case</p><p className="text-green-400 text-xl font-bold mt-1">₹{result.monte_carlo?.best_case?.toLocaleString()}</p></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
"""

# ─── pages/Retirement.tsx ─────────────────────────────────────────────────────
files[BASE + r"\pages\Retirement.tsx"] = r"""import React, { useState } from 'react';
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
"""

# ─── pages/Tax.tsx ────────────────────────────────────────────────────────────
files[BASE + r"\pages\Tax.tsx"] = r"""import React, { useState } from 'react';
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
"""

# ─── pages/News.tsx ───────────────────────────────────────────────────────────
files[BASE + r"\pages\News.tsx"] = r"""import React, { useEffect, useState } from 'react';
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
"""

# ─── App.tsx ──────────────────────────────────────────────────────────────────
files[BASE + r"\App.tsx"] = r"""import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import RiskProfile from './pages/RiskProfile';
import Portfolio from './pages/Portfolio';
import Goals from './pages/Goals';
import Retirement from './pages/Retirement';
import Tax from './pages/Tax';
import News from './pages/News';
import Layout from './components/Layout';
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  return token ? <>{children}</> : <Navigate to="/login" />;
};
function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{style:{background:'#1e293b',color:'#e2e8f0',border:'1px solid #334155'}}}/>
      <Routes>
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<PrivateRoute><Layout><Dashboard/></Layout></PrivateRoute>}/>
        <Route path="/risk" element={<PrivateRoute><Layout><RiskProfile/></Layout></PrivateRoute>}/>
        <Route path="/portfolio" element={<PrivateRoute><Layout><Portfolio/></Layout></PrivateRoute>}/>
        <Route path="/goals" element={<PrivateRoute><Layout><Goals/></Layout></PrivateRoute>}/>
        <Route path="/retirement" element={<PrivateRoute><Layout><Retirement/></Layout></PrivateRoute>}/>
        <Route path="/tax" element={<PrivateRoute><Layout><Tax/></Layout></PrivateRoute>}/>
        <Route path="/news" element={<PrivateRoute><Layout><News/></Layout></PrivateRoute>}/>
        <Route path="*" element={<Navigate to="/" />}/>
      </Routes>
    </BrowserRouter>
  );
}
export default App;
"""

# ─── Write all files ──────────────────────────────────────────────────────────
for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")

print("\n✅ All frontend files created successfully!")
