import React, { useState } from 'react';
import { retirementAPI } from '../services/api';
import toast from 'react-hot-toast';
import { Sunset, TrendingUp, Target, Clock } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const PIE_COLORS = ['#00F2FF', '#2E865F', '#C100FF'];

export default function Retirement() {
  const parseNumberInput = (value: string) => (value === '' ? '' : Number(value));
  const [form, setForm] = useState({
    current_age: 25,
    retirement_age: 60,
    current_monthly_expenses: 40000,
    expected_inflation_rate: 6.0,
    existing_savings: 500000,
    life_expectancy: 85,
    risk_profile: 'Moderate',
  });
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleCalculate = async () => {
    setLoading(true);
    try {
      const res = await retirementAPI.calculate(form);
      setResult(res.data);
      toast.success('Retirement plan calculated!');
    } catch {
      toast.error('Calculation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await retirementAPI.save(form);
      toast.success('Retirement plan saved!');
    } catch {
      toast.error('Save failed');
    }
  };

  const field = (label: string, key: keyof typeof form, type = 'number', isSelect = false, options?: string[]) => (
    <div>
      <label className="label">{label}</label>
      {isSelect ? (
        <select
          className="input-field"
          value={form[key] as string}
          onChange={e => setForm({ ...form, [key]: e.target.value })}
        >
          {options?.map(o => <option key={o}>{o}</option>)}
        </select>
      ) : (
        <input
          type={type}
          className="input-field"
          value={form[key] as any}
          onChange={e => setForm({ ...form, [key]: parseNumberInput(e.target.value) as any })}
        />
      )}
    </div>
  );

  const yearsLeft = form.retirement_age - form.current_age;
  const retirementPieData = result ? [
    { name: 'Existing Savings', value: Number(form.existing_savings) || 0 },
    { name: 'Required SIP Contributions', value: (Number(result?.results?.required_monthly_sip) || 0) * 12 * Math.max(0, yearsLeft) },
    { name: 'Corpus Gap', value: Math.max(0, (Number(result?.results?.required_corpus) || 0) - ((Number(form.existing_savings) || 0) + ((Number(result?.results?.required_monthly_sip) || 0) * 12 * Math.max(0, yearsLeft)))) },
  ].filter(d => d.value > 0) : [];

  return (
    <div className="space-y-5 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="font-display font-bold flex items-center gap-2"
          style={{ fontSize: 28, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
          <Sunset size={22} style={{ color: 'var(--purple)' }} />
          Retirement Planner
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          Calculate your retirement corpus and required monthly SIP
        </p>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Years to Retire', value: `${yearsLeft}y`, color: 'var(--accent)' },
          { label: 'Risk Profile', value: form.risk_profile, color: form.risk_profile === 'Conservative' ? 'var(--accent)' : form.risk_profile === 'Moderate' ? 'var(--yellow)' : 'var(--red)' },
          { label: 'Inflation Rate', value: `${form.expected_inflation_rate}%`, color: 'var(--yellow)' },
        ].map(s => (
          <div key={s.label} className="card" style={{ padding: '14px 16px' }}>
            <p className="section-title mb-1">{s.label}</p>
            <p className="num" style={{ fontSize: 20, fontWeight: 700, color: s.color }}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Form */}
      <div className="card">
        <div className="flex items-center gap-2 mb-5">
          <Clock size={14} style={{ color: 'var(--text-muted)' }} />
          <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>Your Details</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {field('Current Age', 'current_age')}
          {field('Retirement Age', 'retirement_age')}
          {field('Monthly Expenses (₹)', 'current_monthly_expenses')}
          {field('Existing Savings (₹)', 'existing_savings')}
          {field('Expected Inflation (%)', 'expected_inflation_rate')}
          {field('Life Expectancy', 'life_expectancy')}
          {field('Risk Profile', 'risk_profile', 'text', true, ['Conservative', 'Moderate', 'Aggressive'])}
        </div>
        <div className="flex gap-3 mt-5">
          <button onClick={handleCalculate} disabled={loading} className="btn-primary">
            {loading ? 'Calculating...' : 'Calculate Retirement Plan'}
          </button>
          {result && (
            <button onClick={handleSave} className="btn-secondary">Save Plan</button>
          )}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4 animate-fade-up">
          {/* Key metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Required Corpus',       value: `₹${(result.results?.required_corpus / 10000000).toFixed(2)}Cr`, color: 'var(--text-primary)' },
              { label: 'Monthly SIP Required',  value: `₹${result.results?.required_monthly_sip?.toLocaleString('en-IN')}`, color: 'var(--accent)' },
              { label: 'Future Monthly Expense',value: `₹${result.results?.future_monthly_expense?.toLocaleString('en-IN')}`, color: 'var(--yellow)' },
              { label: 'Success Probability',   value: `${result.results?.corpus_achievement_probability}%`, color: 'var(--green)' },
            ].map(m => (
              <div key={m.label} className="card" style={{ padding: '14px 16px' }}>
                <p className="section-title mb-1">{m.label}</p>
                <p className="num" style={{ fontSize: 18, fontWeight: 700, color: m.color }}>{m.value}</p>
              </div>
            ))}
          </div>

          {/* Milestones table */}
          {result.milestones?.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp size={14} style={{ color: 'var(--accent)' }} />
                <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>
                  Corpus Growth Milestones
                </span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Age</th>
                      <th>Years Invested</th>
                      <th>Projected Corpus</th>
                      <th>Phase</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.milestones.map((m: any) => (
                      <tr key={m.age}>
                        <td className="num" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{m.age}</td>
                        <td className="num">{m.years_invested}y</td>
                        <td className="num" style={{ color: 'var(--green)', fontWeight: 600 }}>
                          ₹{(m.projected_corpus / 100000).toFixed(1)}L
                        </td>
                        <td>
                          <span className="badge badge-blue" style={{ fontSize: 10 }}>
                            {m.phase?.replace(/_/g, ' ')}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Recommendation */}
          {result.recommendation && (
            <div className="card card-blue">
              <div className="flex items-center gap-2 mb-2">
                <Target size={14} style={{ color: 'var(--accent)' }} />
                <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>AI Recommendation</span>
              </div>
              <p style={{ fontWeight: 700, fontSize: 14, marginBottom: 6, color:
                result.recommendation?.color === 'green' ? 'var(--green)' :
                result.recommendation?.color === 'red'   ? 'var(--red)' : 'var(--yellow)'
              }}>{result.recommendation?.status}</p>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                {result.recommendation?.message}
              </p>
            </div>
          )}

          <div className="card glass-card">
            <h3 className="font-semibold text-white mb-3">Retirement Corpus Mix</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={retirementPieData} cx="50%" cy="50%" outerRadius={86} dataKey="value"
                  label={({ name, value }) => `${name}: ₹${(Number(value || 0) / 100000).toFixed(1)}L`} labelLine={false}>
                  {retirementPieData.map((_: any, i: number) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v: any) => `₹${Number(v || 0).toLocaleString('en-IN')}`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
