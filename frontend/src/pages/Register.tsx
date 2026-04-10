import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';
import { MoonStar, Mail, Lock, User, ArrowRight } from 'lucide-react';

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', full_name: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authAPI.register(form);
      toast.success('Account created! Please sign in.');
      navigate('/login');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Registration failed');
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
      <div style={{
        position: 'fixed', inset: 0,
        background: `
          radial-gradient(circle at 18% 24%, rgba(110,231,255,0.08), transparent 36%),
          radial-gradient(circle at 78% 18%, rgba(59,158,255,0.09), transparent 34%),
          radial-gradient(circle at 50% 78%, rgba(143,128,255,0.08), transparent 40%)
        `,
        pointerEvents: 'none',
      }} />

      <div className="w-full max-w-sm animate-fade-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center gap-3 mb-4">
            <div style={{
              width: 44, height: 44,
              background: 'linear-gradient(145deg, #8f80ff, #2ee9c6)',
              borderRadius: 14,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 24px rgba(46,233,198,0.4)',
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
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
            Create your account to get started
          </p>
        </div>

        <div className="card" style={{ borderColor: 'rgba(59,158,255,0.15)' }}>
          <h2 className="font-display font-bold text-lg mb-6" style={{ color: 'var(--text-primary)' }}>
            Create Account
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Full Name</label>
              <div style={{ position: 'relative' }}>
                <User size={14} style={{
                  position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
                  color: 'var(--text-dim)',
                }} />
                <input
                  type="text"
                  className="input-field"
                  style={{ paddingLeft: 38 }}
                  placeholder="Pushkraj Naik"
                  value={form.full_name}
                  onChange={e => setForm({ ...form, full_name: e.target.value })}
                  required
                />
              </div>
            </div>

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
                  style={{ paddingLeft: 38 }}
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
                  style={{ paddingLeft: 38 }}
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
              style={{ height: 44 }}
            >
              {loading ? 'Creating account...' : <><span>Create Account</span> <ArrowRight size={15} /></>}
            </button>
          </form>

          <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border)', textAlign: 'center' }}>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              Already have an account?{' '}
              <Link to="/login" style={{ color: 'var(--accent)', fontWeight: 600 }}>
                Sign in
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
