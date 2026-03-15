import React, { useState } from 'react';
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
