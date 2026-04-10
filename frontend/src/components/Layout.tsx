import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Shield, PieChart, Target,
  Sunset, Receipt, Newspaper, LogOut,
  ChevronLeft, ChevronRight, TrendingUp, MoonStar
} from 'lucide-react';

const navItems = [
  { path: '/',           label: 'Dashboard',    icon: LayoutDashboard, accent: '#6ee7ff' },
  { path: '/risk',       label: 'Risk Profile', icon: Shield,          accent: '#8fbaff' },
  { path: '/portfolio',  label: 'Portfolio',    icon: PieChart,        accent: '#2ee9c6' },
  { path: '/goals',      label: 'Goals',        icon: Target,          accent: '#ffc047' },
  { path: '/retirement', label: 'Retirement',   icon: Sunset,          accent: '#8f80ff' },
  { path: '/tax',        label: 'Tax',          icon: Receipt,         accent: '#ef596f' },
  { path: '/news',       label: 'News',         icon: Newspaper,       accent: '#6ee7ff' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const logout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-base)' }}>

      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside
        className="flex flex-col transition-all duration-300 ease-in-out shrink-0"
        style={{
          width: collapsed ? '64px' : '220px',
          background: 'var(--bg-surface)',
          borderRight: '1px solid var(--border)',
        }}
      >
        {/* Logo */}
        <div
          className="flex items-center gap-3 px-4 shrink-0"
          style={{ height: '60px', borderBottom: '1px solid var(--border)' }}
        >
          <div
            className="flex items-center justify-center rounded-xl shrink-0"
            style={{
              width: 32, height: 32,
              background: 'linear-gradient(145deg, #8f80ff, #2ee9c6)',
              boxShadow: '0 0 18px rgba(46,233,198,0.42)',
            }}
          >
            <MoonStar size={16} color="#06242a" strokeWidth={2.5} />
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <p className="font-display text-sm font-bold leading-tight" style={{ color: 'var(--text-primary)' }}>
                Lunara
              </p>
              <p className="text-xs" style={{ color: 'var(--text-dim)' }}>Finance</p>
            </div>
          )}
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {navItems.map(({ path, label, icon: Icon, accent }) => {
            const isActive = location.pathname === path;
            return (
              <Link
                key={path}
                to={path}
                title={collapsed ? label : undefined}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: collapsed ? '10px 12px' : '9px 12px',
                  borderRadius: 12,
                  transition: 'all 0.15s ease',
                  background: isActive ? 'rgba(110,231,255,0.09)' : 'transparent',
                  border: isActive ? '1px solid rgba(110,231,255,0.28)' : '1px solid transparent',
                  color: isActive ? accent : 'var(--text-muted)',
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  textDecoration: 'none',
                  position: 'relative',
                }}
                onMouseEnter={e => {
                  if (!isActive) {
                    (e.currentTarget as HTMLElement).style.background = 'var(--bg-elevated)';
                    (e.currentTarget as HTMLElement).style.color = 'var(--text-primary)';
                  }
                }}
                onMouseLeave={e => {
                  if (!isActive) {
                    (e.currentTarget as HTMLElement).style.background = 'transparent';
                    (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)';
                  }
                }}
              >
                {/* Active bar */}
                {isActive && (
                  <div style={{
                    position: 'absolute', left: 0, top: '20%', bottom: '20%',
                    width: 3, borderRadius: '0 3px 3px 0',
                    background: accent,
                    boxShadow: `0 0 8px ${accent}`,
                  }} />
                )}
                <Icon size={16} strokeWidth={isActive ? 2.5 : 2} style={{ flexShrink: 0 }} />
                {!collapsed && (
                  <span style={{ fontSize: 13, fontWeight: isActive ? 600 : 400 }}>{label}</span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom controls */}
        <div className="px-2 pb-3 space-y-0.5" style={{ borderTop: '1px solid var(--border)', paddingTop: 8 }}>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center gap-2.5 rounded-xl transition-all duration-150"
            style={{
              padding: collapsed ? '9px 12px' : '9px 12px',
              justifyContent: collapsed ? 'center' : 'flex-start',
              color: 'var(--text-dim)',
              background: 'transparent',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.background = 'var(--bg-elevated)';
              (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.background = 'transparent';
              (e.currentTarget as HTMLElement).style.color = 'var(--text-dim)';
            }}
          >
            {collapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
            {!collapsed && <span style={{ fontSize: 12 }}>Collapse</span>}
          </button>

          <button
            onClick={logout}
            className="w-full flex items-center gap-2.5 rounded-xl transition-all duration-150"
            style={{
              padding: '9px 12px',
              justifyContent: collapsed ? 'center' : 'flex-start',
              color: 'var(--text-dim)',
              background: 'transparent',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(255,82,82,0.08)';
              (e.currentTarget as HTMLElement).style.color = 'var(--red)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.background = 'transparent';
              (e.currentTarget as HTMLElement).style.color = 'var(--text-dim)';
            }}
          >
            <LogOut size={15} strokeWidth={2} style={{ flexShrink: 0 }} />
            {!collapsed && <span style={{ fontSize: 12 }}>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────── */}
      <main
        className="flex-1 overflow-y-auto"
        style={{ background: 'var(--bg-base)' }}
      >
        {/* Top bar */}
        <div
          className="sticky top-0 z-10 flex items-center justify-between px-6"
          style={{
            height: 60,
            background: 'rgba(5,11,22,0.86)',
            backdropFilter: 'blur(12px)',
            borderBottom: '1px solid var(--border)',
          }}
        >
          <div className="flex items-center gap-2">
            <TrendingUp size={14} style={{ color: 'var(--accent)' }} />
            <span style={{ fontSize: 12, color: 'var(--text-dim)', fontFamily: 'DM Mono, monospace' }}>
              {navItems.find(n => n.path === location.pathname)?.label || 'Dashboard'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="live-dot" />
            <span style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'DM Mono, monospace' }}>
              LIVE
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'DM Mono, monospace', marginLeft: 8 }}>
              {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>

        {/* Page content */}
        <div className="p-6 page-enter">
          {children}
        </div>
      </main>
    </div>
  );
}
