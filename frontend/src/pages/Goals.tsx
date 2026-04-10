import React, { useState, useEffect } from 'react';
import { goalsAPI, riskAPI } from '../services/api';
import toast from 'react-hot-toast';
import { Target, TrendingUp, Brain, Sunset, Home, GraduationCap, ShieldAlert, Car, Plane, Gem, BriefcaseBusiness } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const GOAL_TEMPLATES = [
  { id: 'retirement', label: 'Retirement',      icon: Sunset,            iconColor: 'text-purple-400', defaultAmount: 10000000, defaultYears: 30 },
  { id: 'home',       label: 'Buy a Home',      icon: Home,              iconColor: 'text-blue-400',   defaultAmount: 5000000,  defaultYears: 10 },
  { id: 'education',  label: 'Child Education', icon: GraduationCap,     iconColor: 'text-cyan-400',   defaultAmount: 2000000,  defaultYears: 15 },
  { id: 'emergency',  label: 'Emergency Fund',  icon: ShieldAlert,       iconColor: 'text-red-400',    defaultAmount: 500000,   defaultYears: 2  },
  { id: 'vehicle',    label: 'Buy a Vehicle',   icon: Car,               iconColor: 'text-orange-400', defaultAmount: 1500000,  defaultYears: 5  },
  { id: 'travel',     label: 'Dream Vacation',  icon: Plane,             iconColor: 'text-sky-400',    defaultAmount: 500000,   defaultYears: 3  },
  { id: 'wedding',    label: 'Wedding',         icon: Gem,               iconColor: 'text-pink-400',   defaultAmount: 3000000,  defaultYears: 5  },
  { id: 'business',   label: 'Start a Business',icon: BriefcaseBusiness, iconColor: 'text-emerald-400',defaultAmount: 2000000,  defaultYears: 7  },
];

// Frontend templates -> backend goal_type values (GoalCreateRequest.goal_type)
const GOAL_TYPE_MAP: Record<string, string> = {
  retirement: 'retirement',
  home: 'home_purchase',
  education: 'child_education',
  emergency: 'emergency_fund',
  vehicle: 'vehicle_purchase',
  travel: 'travel',
  wedding: 'custom',
  business: 'custom',
};

const PROFILE_RETURNS: any = {
  Conservative: { expected_return: 0.08, label: 'Conservative (8% return)'  },
  Moderate:     { expected_return: 0.11, label: 'Moderate (11% return)'      },
  Aggressive:   { expected_return: 0.14, label: 'Aggressive (14% return)'    },
};

const PROFILE_COLORS: any = {
  Conservative: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
  Moderate:     'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
  Aggressive:   'text-red-400 bg-red-500/10 border-red-500/30',
};
const PIE_COLORS = ['#00F2FF', '#C100FF', '#2E865F'];

export default function Goals() {
  const parseNumberInput = (value: string) => (value === '' ? '' : Number(value));
  const [selectedGoal,    setSelectedGoal]    = useState<any>(null);
  const [form,            setForm]            = useState({
    goal_name:          '',
    target_amount:      1000000,
    current_savings:    0,
    monthly_investment: 10000,
    time_horizon_years: 10,
    expected_return:    0.11,
  });
  const [result,          setResult]          = useState<any>(null);
  const [loading,         setLoading]         = useState(false);
  const [riskProfile,     setRiskProfile]     = useState<string>('');
  const [riskScore,       setRiskScore]       = useState<number>(0);
  const [loadingProfile,  setLoadingProfile]  = useState(true);

  useEffect(() => {
    const fetchRiskProfile = async () => {
      try {
        const r       = await riskAPI.getMyProfile();
        const profile = r.data?.profile_type || 'Moderate';
        const score   = r.data?.score || 0;
        setRiskProfile(profile);
        setRiskScore(score);
        setForm(f => ({ ...f, expected_return: PROFILE_RETURNS[profile]?.expected_return || 0.11 }));
      } catch {
        setRiskProfile('Moderate');
        setForm(f => ({ ...f, expected_return: 0.11 }));
      } finally {
        setLoadingProfile(false);
      }
    };
    fetchRiskProfile();
  }, []);

  const selectGoalTemplate = (template: any) => {
    setSelectedGoal(template);
    setForm(f => ({
      ...f,
      goal_name:          template.label,
      target_amount:      template.defaultAmount,
      time_horizon_years: template.defaultYears,
    }));
    setResult(null);
  };

  const handleAnalyze = async () => {
    if (!form.goal_name) {
      toast.error('Please select a goal first');
      return;
    }
    setLoading(true);
    try {
      // Goals API expects GoalCreateRequest fields (not simulation fields)
      const payload = {
        goal_type:          GOAL_TYPE_MAP[selectedGoal?.id] ?? 'custom',
        goal_name:          form.goal_name,
        target_amount:      form.target_amount,
        current_savings:    form.current_savings,
        monthly_investment: form.monthly_investment,
        time_horizon_years: form.time_horizon_years,
        inflation_rate:     6.0,
        risk_profile:       riskProfile || 'Moderate',
      };
      const r = await goalsAPI.analyze(payload);
      setResult(r.data);
      toast.success('Goal analyzed!');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const detailText =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail
                .map((d: any) => d?.msg || d?.message || (typeof d === 'string' ? d : JSON.stringify(d)))
                .join(', ')
            : detail
              ? JSON.stringify(detail)
              : '';
      toast.error(detailText ? `Analysis failed: ${detailText}` : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const profileColorClass = PROFILE_COLORS[riskProfile] || PROFILE_COLORS['Moderate'];

  // /goals/analyze returns GoalAnalysisResponse shape
  const successProb   = result?.success_probability;
  const medianOutcome = result?.monte_carlo?.median;
  const bestCase      = result?.monte_carlo?.best_case;
  const worstCase     = result?.monte_carlo?.worst_case;
  const requiredSip   = result?.required_sip;
  const investedByHorizon = (Number(form.current_savings) || 0) + ((Number(form.monthly_investment) || 0) * 12 * (Number(form.time_horizon_years) || 0));
  const goalPieData = [
    { name: 'Current Savings', value: Number(form.current_savings) || 0 },
    { name: 'Planned Contributions', value: (Number(form.monthly_investment) || 0) * 12 * (Number(form.time_horizon_years) || 0) },
    { name: 'Gap vs Target', value: Math.max(0, (Number(form.target_amount) || 0) - investedByHorizon) },
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Target className="text-yellow-500" /> Goal Planner
        </h1>
        <p className="text-slate-400 mt-1">
          Monte Carlo simulation — returns auto-set from your risk profile
        </p>
      </div>

      {/* Risk Profile Banner */}
      <div className={`card border flex items-center justify-between ${profileColorClass}`}>
        <div className="flex items-center gap-3">
          <Brain size={20} className={profileColorClass.split(' ')[0]} />
          <div>
            <p className="text-white font-semibold">
              {loadingProfile ? 'Loading your risk profile...' : `${riskProfile} Investor`}
            </p>
            {!loadingProfile && (
              <p className="text-slate-400 text-xs mt-0.5">
                Score: {riskScore}/100 •
                Expected Return: {(PROFILE_RETURNS[riskProfile]?.expected_return * 100).toFixed(0)}% p.a. •
                Auto-applied to all goal calculations
              </p>
            )}
          </div>
        </div>
        <span className="px-2 py-1 text-xs rounded-full bg-blue-500/20 text-blue-400">Auto</span>
      </div>

      {/* Goal Templates */}
      <div className="card">
        <h3 className="font-semibold text-white mb-4">Select Your Goal</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {GOAL_TEMPLATES.map(template => (
            <button
              key={template.id}
              onClick={() => selectGoalTemplate(template)}
              className={`p-3 rounded-lg border text-left transition-all ${
                selectedGoal?.id === template.id
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-slate-700 bg-slate-700/30 hover:border-slate-500'
              }`}
            >
              <template.icon
                size={20}
                className={selectedGoal?.id === template.id ? 'text-blue-400' : template.iconColor}
              />
              <p className={`text-sm font-medium mt-1 ${
                selectedGoal?.id === template.id ? 'text-blue-400' : 'text-white'
              }`}>{template.label}</p>
              <p className="text-slate-500 text-xs">
                ₹{(template.defaultAmount / 100000).toFixed(0)}L • {template.defaultYears}yr
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Goal Config Form */}
      {selectedGoal && (
        <div className="card">
          <h3 className="font-semibold text-white mb-4">
            <span className="inline-flex items-center gap-2">
              <selectedGoal.icon size={18} className="text-blue-400" />
              Configure {selectedGoal.label} Goal
            </span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Target Amount (₹)</label>
              <input type="number" className="input-field" value={form.target_amount}
                onChange={e => setForm({ ...form, target_amount: parseNumberInput(e.target.value) as any })} />
            </div>
            <div>
              <label className="label">Current Savings (₹)</label>
              <input type="number" className="input-field" value={form.current_savings}
                onChange={e => setForm({ ...form, current_savings: parseNumberInput(e.target.value) as any })} />
            </div>
            <div>
              <label className="label">Monthly Investment (₹)</label>
              <input type="number" className="input-field" value={form.monthly_investment}
                onChange={e => setForm({ ...form, monthly_investment: parseNumberInput(e.target.value) as any })} />
            </div>
            <div>
              <label className="label">Time Horizon (Years)</label>
              <input type="number" className="input-field" value={form.time_horizon_years}
                onChange={e => setForm({ ...form, time_horizon_years: parseNumberInput(e.target.value) as any })} />
            </div>
          </div>

          {/* Auto return display */}
          <div className="mt-4 p-3 bg-slate-700/50 rounded-lg border border-slate-600">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Expected Annual Return</p>
                <p className="text-white font-bold text-lg">
                  {(form.expected_return * 100).toFixed(0)}% p.a.
                </p>
                <p className="text-slate-500 text-xs mt-1">
                  Auto-set based on your {riskProfile} risk profile
                </p>
              </div>
              <div className={`px-3 py-2 rounded-lg border text-center ${profileColorClass}`}>
                <p className={`font-bold text-sm ${profileColorClass.split(' ')[0]}`}>{riskProfile}</p>
                <p className="text-slate-500 text-xs">Your Profile</p>
              </div>
            </div>
          </div>

          <div className="mt-4 card glass-card">
            <h3 className="font-semibold text-white mb-3">Goal Funding Mix</h3>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={goalPieData} cx="50%" cy="50%" outerRadius={84} dataKey="value"
                  label={({ name, value }) => `${name}: ₹${(Number(value || 0) / 100000).toFixed(1)}L`} labelLine={false}>
                  {goalPieData.map((_: any, i: number) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v: any) => `₹${Number(v || 0).toLocaleString('en-IN')}`} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <button
            onClick={handleAnalyze}
            disabled={loading || loadingProfile}
            className="btn-primary mt-4"
          >
            {loading ? 'Running Monte Carlo...' : 'Analyze Goal (10,000 Simulations)'}
          </button>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">

          {/* Success Probability */}
          {successProb !== undefined && (
            <div className={`card border ${
              successProb >= 80 ? 'border-green-500/30 bg-green-500/5' :
              successProb >= 60 ? 'border-yellow-500/30 bg-yellow-500/5' :
                                  'border-red-500/30 bg-red-500/5'
            }`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Goal Success Probability</p>
                  <p className={`text-4xl font-bold mt-1 ${
                    successProb >= 80 ? 'text-green-400' :
                    successProb >= 60 ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    {successProb?.toFixed(1)}%
                  </p>
                  <p className="text-slate-400 text-sm mt-1">
                    Based on 10,000 Monte Carlo simulations
                  </p>
                </div>
                <TrendingUp size={48} className={
                  successProb >= 80 ? 'text-green-400' :
                  successProb >= 60 ? 'text-yellow-400' : 'text-red-400'
                } />
              </div>
            </div>
          )}

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Median Outcome',     value: medianOutcome  != null ? `₹${(medianOutcome  / 100000).toFixed(1)}L` : '—', color: 'text-blue-400'   },
              { label: 'Best Case (P95)',     value: bestCase       != null ? `₹${(bestCase       / 100000).toFixed(1)}L` : '—', color: 'text-green-400'  },
              { label: 'Worst Case (P5)',     value: worstCase      != null ? `₹${(worstCase      / 100000).toFixed(1)}L` : '—', color: 'text-red-400'    },
              { label: 'Required SIP',       value: requiredSip    != null ? `₹${Math.round(requiredSip).toLocaleString()}/mo` : '—', color: 'text-yellow-400' },
            ].map((stat, i) => (
              <div key={i} className="card">
                <p className="text-slate-400 text-xs">{stat.label}</p>
                <p className={`text-xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
              </div>
            ))}
          </div>

          {/* AI Recommendation */}
          {result.recommendation && (
            <div className="card border border-blue-500/30 bg-blue-500/5">
              <h3 className="font-semibold text-white mb-2">AI Recommendation</h3>
              <p className="text-slate-300 text-sm">{result.recommendation?.message || ''}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
