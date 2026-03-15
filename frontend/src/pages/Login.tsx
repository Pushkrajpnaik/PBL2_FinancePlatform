import React, { useState } from 'react';
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
