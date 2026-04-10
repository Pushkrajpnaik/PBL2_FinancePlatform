import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';
import { MoonStar, Mail, Lock, ArrowRight, Sparkles, ShieldCheck, LineChart, BrainCircuit } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authAPI.login(form);
      localStorage.setItem('token', res.data.access_token);
      toast.success('Welcome back!');
      navigate('/');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{
        background: 'var(--bg-base)',
        backgroundImage: 'radial-gradient(rgba(59,158,255,0.06) 1px, transparent 1px)',
        backgroundSize: '28px 28px',
      }}
    >
      <div
        style={{
          position: 'fixed',
          inset: 0,
          pointerEvents: 'none',
          background: `
            radial-gradient(circle at 18% 24%, rgba(0,242,255,0.08), transparent 36%),
            radial-gradient(circle at 78% 18%, rgba(59,158,255,0.09), transparent 34%),
            radial-gradient(circle at 50% 78%, rgba(193,0,255,0.08), transparent 40%)
          `,
        }}
      />

      <div className="w-full max-w-md animate-fade-up">
        <div className="text-center mb-7">
          <div className="inline-flex items-center justify-center gap-3 mb-3">
            <div style={{
              width: 46, height: 46,
              background: 'linear-gradient(145deg, #8f80ff, #2ee9c6)',
              borderRadius: 15,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 28px rgba(46,233,198,0.45)',
            }}>
              <MoonStar size={20} color="#07242a" strokeWidth={2.5} />
            </div>
            <div className="text-left">
              <p className="font-display font-bold text-lg leading-tight" style={{ color: 'var(--text-primary)' }}>
                Lunara
              </p>
              <p style={{ fontSize: 11, color: 'var(--text-dim)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                Finance
              </p>
            </div>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 8 }}>
            Adaptive intelligence for smarter money decisions
          </p>
          <div className="flex items-center justify-center gap-2 text-xs">
            <span className="badge badge-blue" style={{ border: '1px solid rgba(59,158,255,0.3)' }}>
              <BrainCircuit size={12} /> AI-first
            </span>
            <span className="badge badge-purple" style={{ border: '1px solid rgba(167,139,250,0.3)' }}>
              <Sparkles size={12} /> Dynamic Insights
            </span>
            <span className="badge badge-green" style={{ border: '1px solid rgba(46,134,95,0.28)' }}>
              <ShieldCheck size={12} /> Secure
            </span>
          </div>
        </div>

        <div
          className="card glass-card"
          style={{
            borderColor: 'rgba(59,158,255,0.2)',
            boxShadow: '0 24px 60px rgba(12,18,32,0.55), 0 0 28px rgba(59,158,255,0.14)',
          }}
        >
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="font-display font-bold text-xl" style={{ color: 'var(--text-primary)' }}>
                Welcome Back
              </h2>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                Sign in to continue your wealth command center
              </p>
            </div>
            <span className="badge badge-blue" style={{ fontSize: 10 }}>
              Live
              <span className="live-dot" />
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Email Address</label>
              <div style={{ position: 'relative' }}>
                <Mail size={14} style={{
                  position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
                  color: 'var(--text-dim)',
                }} />
                <input
                  type="email"
                  className="input-field"
                  style={{ paddingLeft: 38, height: 46 }}
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={e => setForm({ ...form, email: e.target.value })}
                  required
                />
              </div>
            </div>

            <div>
              <label className="label">Password</label>
              <div style={{ position: 'relative' }}>
                <Lock size={14} style={{
                  position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
                  color: 'var(--text-dim)',
                }} />
                <input
                  type="password"
                  className="input-field"
                  style={{ paddingLeft: 38, height: 46 }}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn-primary w-full mt-2"
              disabled={loading}
              style={{ height: 46 }}
            >
              {loading ? (
                <span style={{ opacity: 0.8 }}>Signing in...</span>
              ) : (
                <>Sign In <ArrowRight size={15} /></>
              )}
            </button>
          </form>

          <div className="grid grid-cols-3 gap-2 mt-4 mb-1">
            {[
              { icon: LineChart, label: 'Portfolio AI' },
              { icon: BrainCircuit, label: 'Risk Engine' },
              { icon: ShieldCheck, label: 'Protected' },
            ].map((item) => (
              <div key={item.label} className="rounded-xl px-2 py-2 text-center" style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)' }}>
                <item.icon size={13} style={{ color: 'var(--text-muted)', margin: '0 auto 4px' }} />
                <p style={{ fontSize: 10, color: 'var(--text-dim)' }}>{item.label}</p>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)', textAlign: 'center' }}>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              Don't have an account?{' '}
              <Link to="/register" style={{ color: 'var(--accent)', fontWeight: 600 }}>
                Create account
              </Link>
            </p>
          </div>
        </div>

        <p style={{ textAlign: 'center', fontSize: 11, color: 'var(--text-dim)', marginTop: 20 }}>
          Powered by FinBERT · HMM · XGBoost · Monte Carlo
        </p>
      </div>
    </div>
  );
}
