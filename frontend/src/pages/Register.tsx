import React, { useState } from 'react';
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
