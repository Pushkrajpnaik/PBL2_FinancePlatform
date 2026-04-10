import React, { useState } from 'react';
import { taxAPI } from '../services/api';
import toast from 'react-hot-toast';
import { Receipt, TrendingDown, CheckCircle } from 'lucide-react';
import { TaxEngineInput, TaxEngineResult, runTaxOptimizationEngine } from '../lib/taxEngine';

const toInputNumber = (value: string) => (value === '' ? '' : Number(value));
const toApiNumber = (value: any, fallback = 0) =>
  value === '' || value == null || Number.isNaN(Number(value)) ? fallback : Number(value);
const toInputValue = (value: any) => (value === '' ? '' : value);
const sanitizeNumericFields = (obj: any): any => {
  if (obj === '' || obj == null) return 0;
  if (Array.isArray(obj)) return obj.map(sanitizeNumericFields);
  if (typeof obj === 'object') {
    return Object.fromEntries(
      Object.entries(obj).map(([k, v]) => [k, sanitizeNumericFields(v)]),
    );
  }
  return obj;
};

// Derived from tax_strategies.txt (FY 2025-26 quick rules)
const buildRegimeHints = (income: number, regime: string) => {
  const hints: string[] = [];
  if (income <= 1275000 && regime === 'new_regime') {
    hints.push('Income is within the new-regime effective zero-tax zone (including standard deduction), so preserve liquidity over forced deductions.');
  }
  if (income >= 1350000 && income <= 1700000 && regime === 'old_regime') {
    hints.push('At this income range, old regime can outperform if total deductions are high; ensure all 80C/80D/home-loan claims are fully documented.');
  }
  if (income > 2500000 && regime === 'new_regime') {
    hints.push('For higher incomes, compare old vs new using full deduction stack (80C, 80D, home-loan, NPS) before finalizing TDS regime.');
  }
  hints.push('Section 80CCD(2) (employer NPS contribution) remains one of the strongest legal tax levers.');
  return hints;
};

const buildCapitalGainHints = (form: any, result: any) => {
  const hints: string[] = [];
  const gain = Number(result?.gain || 0);
  const holdingDays = Number(form?.holding_days || 0);
  const isEquity = form?.asset_type === 'equity';

  if (isEquity && holdingDays < 365) {
    hints.push('Equity gain is being taxed as STCG; crossing 12 months may significantly reduce rate for listed equity.');
  }
  if (isEquity && gain > 125000) {
    hints.push('Use annual LTCG harvesting: book/rebalance gains up to the exemption threshold each FY to reduce tax drag.');
  }
  hints.push('Consider tax-loss harvesting before March 31 only when transaction costs are lower than tax savings.');
  hints.push('If this is property-related LTCG, evaluate Section 54/54EC/54F routes within timeline limits.');
  return hints;
};

const build80cHints = (form: any, result: any) => {
  const hints: string[] = [];
  const total80c = Number(form?.current_investments?.elss || 0) + Number(form?.current_investments?.ppf || 0);
  const remaining = Number(result?.remaining_80c_limit || 0);

  if (form?.tax_regime === 'new_regime') {
    hints.push('80C generally does not reduce tax in the new regime; evaluate whether old regime would be better before adding lock-ins.');
  } else {
    if (remaining > 0) hints.push(`You still have approximately ₹${remaining.toLocaleString('en-IN')} deductible headroom under Section 80C.`);
    if (total80c < 150000) hints.push('Blend ELSS (liquidity + growth) with PPF (stability) to complete 80C efficiently.');
  }
  hints.push('If available via payroll, add employer NPS (80CCD(2)) as an additional deduction lever.');
  return hints;
};

export default function Tax() {
  const [activeTab, setActiveTab] = useState('capital_gains');
  const [cgForm, setCgForm] = useState<any>({
    asset_type: 'equity', purchase_price: 100000, sale_price: 150000,
    holding_days: 400, annual_income: 1200000, tax_regime: 'new_regime',
  });
  const [s80cForm, setS80cForm] = useState<any>({
    annual_income: 1200000,
    current_investments: { elss: 50000, ppf: 30000 },
    tax_regime: 'old_regime',
  });
  const [cgResult,   setCgResult]   = useState<any>(null);
  const [s80cResult, setS80cResult] = useState<any>(null);
  const [loading,    setLoading]    = useState(false);
  const [engineInput, setEngineInput] = useState<any>({
    employmentType: 'salaried',
    salaryIncome: 1200000,
    businessRevenue: 0,
    businessProfit: 0,
    regimePreference: 'auto',
    existingInvestments: {
      epf: 80000,
      ppf: 30000,
      elss: 20000,
      npsSelf: 0,
      npsEmployer: 0,
      lic: 15000,
      nsc: 0,
      taxSaverFd: 0,
      tuitionFees: 0,
      homeLoanPrincipal: 0,
      ulip: 0,
    },
    businessExpenses: {
      officeRent: 0,
      salaries: 0,
      utilities: 0,
      depreciation: 0,
      travel: 0,
      marketing: 0,
      software: 0,
      professionalFees: 0,
      homeOffice: 0,
      vehicleFuelMaintenance: 0,
      epfEmployerContribution: 0,
    },
    otherIncome: {
      rental: 0,
      capitalGains: 0,
      interest: 20000,
      freelance: 0,
    },
    family: {
      dependents: 0,
      seniorCitizenParents: false,
      spouseIncome: 0,
    },
    existingDeductionsClaimed: {
      section80CUsed: 0,
      section80DUsed: 0,
      section80CCD1BUsed: 0,
      section24BUsed: 0,
      section80EUsed: 0,
      section80GUsed: 0,
    },
    healthInsuranceSelfFamily: 0,
    healthInsuranceParents: 0,
    educationLoanInterest: 0,
    donationsEligible: 0,
    ltaClaim: 0,
    housing: {
      hraReceived: 0,
      annualRentPaid: 0,
      isMetroCity: true,
      basicSalary: 600000,
    },
  });
  const [engineResult, setEngineResult] = useState<TaxEngineResult | null>(null);
  const [engineStep, setEngineStep] = useState(1);

  const calcCG = async () => {
    setLoading(true);
    try {
      const payload = {
        ...cgForm,
        purchase_price: toApiNumber(cgForm.purchase_price),
        sale_price: toApiNumber(cgForm.sale_price),
        holding_days: toApiNumber(cgForm.holding_days),
        annual_income: toApiNumber(cgForm.annual_income),
      };
      const res = await taxAPI.capitalGains(payload);
      setCgResult(res.data);
      toast.success('Tax calculated!');
    }
    catch { toast.error('Calculation failed'); }
    finally { setLoading(false); }
  };

  const calc80C = async () => {
    setLoading(true);
    try {
      const payload = {
        ...s80cForm,
        annual_income: toApiNumber(s80cForm.annual_income),
        current_investments: {
          ...s80cForm.current_investments,
          elss: toApiNumber(s80cForm.current_investments.elss),
          ppf: toApiNumber(s80cForm.current_investments.ppf),
        },
      };
      const res = await taxAPI.optimize80c(payload);
      setS80cResult(res.data);
      toast.success('80C optimized!');
    }
    catch { toast.error('Optimization failed'); }
    finally { setLoading(false); }
  };

  const tabs = [
    { id: 'engine',        label: 'Tax Engine' },
    { id: 'capital_gains', label: 'Capital Gains' },
    { id: '80c',           label: 'Section 80C' },
  ];

  const runEngine = () => {
    const result = runTaxOptimizationEngine(sanitizeNumericFields(engineInput) as TaxEngineInput);
    setEngineResult(result);
    toast.success('Comprehensive tax optimization complete');
  };

  return (
    <div className="space-y-5 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="font-display font-bold flex items-center gap-2"
          style={{ fontSize: 24, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
          <Receipt size={22} style={{ color: 'var(--red)' }} />
          Tax Optimizer
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          Budget 2024 compliant · LTCG 12.5% · STCG 15% · Minimize liability legally
        </p>
      </div>

      {/* Tabs */}
      <div className="tab-bar" style={{ width: 'fit-content' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className={`tab-item ${activeTab === t.id ? 'active' : ''}`}
            style={{ minWidth: 140 }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Capital Gains Tab */}
      {activeTab === 'engine' && (
        <div className="space-y-4 animate-fade-in">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="section-title">Guided Flow</p>
                <p className="text-sm mt-1" style={{ color: 'var(--text-primary)' }}>
                  Step {engineStep} of 4 - Comprehensive Tax Optimizer
                </p>
              </div>
              <div className="tab-bar">
                {[1, 2, 3, 4].map(s => (
                  <button key={s} onClick={() => setEngineStep(s)} className={`tab-item ${engineStep === s ? 'active' : ''}`} style={{ minWidth: 36 }}>
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {engineStep === 1 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Employment Type</label>
                  <select className="input-field" value={engineInput.employmentType}
                    onChange={e => setEngineInput({ ...engineInput, employmentType: e.target.value as any })}>
                    <option value="salaried">Salaried</option>
                    <option value="business">Business Owner / Self-Employed</option>
                    <option value="both">Both</option>
                  </select>
                </div>
                <div>
                  <label className="label">Regime Preference</label>
                  <select className="input-field" value={engineInput.regimePreference}
                    onChange={e => setEngineInput({ ...engineInput, regimePreference: e.target.value as any })}>
                    <option value="auto">Auto Suggest Best</option>
                    <option value="old">Old Regime</option>
                    <option value="new">New Regime</option>
                  </select>
                </div>
                <div>
                  <label className="label">Salary Gross Income (₹)</label>
                  <input className="input-field" type="number" value={toInputValue(engineInput.salaryIncome)}
                    onChange={e => setEngineInput({ ...engineInput, salaryIncome: toInputNumber(e.target.value) })} />
                </div>
                <div>
                  <label className="label">Business Profit (₹)</label>
                  <input className="input-field" type="number" value={toInputValue(engineInput.businessProfit)}
                    onChange={e => setEngineInput({ ...engineInput, businessProfit: toInputNumber(e.target.value) })} />
                </div>
              </div>
            )}

            {engineStep === 2 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">80C Basket Invested (₹)</label>
                  <input className="input-field" type="number"
                    value={toInputValue(engineInput.existingInvestments.epf + engineInput.existingInvestments.ppf + engineInput.existingInvestments.elss + engineInput.existingInvestments.lic)}
                    onChange={e => {
                      const v = toApiNumber(toInputNumber(e.target.value));
                      setEngineInput({
                        ...engineInput,
                        existingInvestments: {
                          ...engineInput.existingInvestments,
                          epf: Math.round(v * 0.4),
                          ppf: Math.round(v * 0.2),
                          elss: Math.round(v * 0.25),
                          lic: Math.round(v * 0.15),
                        },
                      });
                    }}
                  />
                </div>
                <div>
                  <label className="label">NPS Self (₹)</label>
                  <input className="input-field" type="number" value={toInputValue(engineInput.existingInvestments.npsSelf)}
                    onChange={e => setEngineInput({ ...engineInput, existingInvestments: { ...engineInput.existingInvestments, npsSelf: toInputNumber(e.target.value) } })} />
                </div>
                <div>
                  <label className="label">Health Insurance - Self/Family (₹)</label>
                  <input className="input-field" type="number" value={toInputValue(engineInput.healthInsuranceSelfFamily)}
                    onChange={e => setEngineInput({ ...engineInput, healthInsuranceSelfFamily: toInputNumber(e.target.value) })} />
                </div>
                <div>
                  <label className="label">Health Insurance - Parents (₹)</label>
                  <input className="input-field" type="number" value={toInputValue(engineInput.healthInsuranceParents)}
                    onChange={e => setEngineInput({ ...engineInput, healthInsuranceParents: toInputNumber(e.target.value) })} />
                </div>
                <div>
                  <label className="label">Home Loan Interest Claimed u/s 24(b) (₹)</label>
                  <input className="input-field" type="number" value={toInputValue(engineInput.existingDeductionsClaimed.section24BUsed)}
                    onChange={e => setEngineInput({ ...engineInput, existingDeductionsClaimed: { ...engineInput.existingDeductionsClaimed, section24BUsed: toInputNumber(e.target.value) } })} />
                </div>
                <div>
                  <label className="label">Education Loan Interest u/s 80E (₹)</label>
                  <input className="input-field" type="number" value={toInputValue(engineInput.educationLoanInterest)}
                    onChange={e => setEngineInput({ ...engineInput, educationLoanInterest: toInputNumber(e.target.value) })} />
                </div>
              </div>
            )}

            {engineStep === 3 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Business Expenses (Total ₹)</label>
                  <input className="input-field" type="number"
                    value={toInputValue(
                      engineInput.businessExpenses.officeRent +
                      engineInput.businessExpenses.salaries +
                      engineInput.businessExpenses.utilities +
                      engineInput.businessExpenses.depreciation +
                      engineInput.businessExpenses.travel +
                      engineInput.businessExpenses.marketing
                    )}
                    onChange={e => {
                      const v = toApiNumber(toInputNumber(e.target.value));
                      setEngineInput({
                        ...engineInput,
                        businessExpenses: {
                          ...engineInput.businessExpenses,
                          officeRent: Math.round(v * 0.22),
                          salaries: Math.round(v * 0.28),
                          utilities: Math.round(v * 0.08),
                          depreciation: Math.round(v * 0.12),
                          travel: Math.round(v * 0.1),
                          marketing: Math.round(v * 0.1),
                          software: Math.round(v * 0.06),
                          professionalFees: Math.round(v * 0.04),
                        },
                      });
                    }}
                  />
                </div>
                <div>
                  <label className="label">Other Income (Rental + Gains + Interest) (₹)</label>
                  <input className="input-field" type="number"
                    value={toInputValue(engineInput.otherIncome.rental + engineInput.otherIncome.capitalGains + engineInput.otherIncome.interest)}
                    onChange={e => {
                      const v = toApiNumber(toInputNumber(e.target.value));
                      setEngineInput({
                        ...engineInput,
                        otherIncome: {
                          ...engineInput.otherIncome,
                          rental: Math.round(v * 0.45),
                          capitalGains: Math.round(v * 0.35),
                          interest: Math.round(v * 0.2),
                        },
                      });
                    }}
                  />
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <input
                    id="seniorParents"
                    type="checkbox"
                    checked={engineInput.family.seniorCitizenParents}
                    onChange={e => setEngineInput({
                      ...engineInput,
                      family: { ...engineInput.family, seniorCitizenParents: e.target.checked },
                    })}
                  />
                  <label htmlFor="seniorParents" className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Senior citizen parents (for higher 80D cap)
                  </label>
                </div>
                <div>
                  <label className="label">Donations Eligible u/s 80G (₹)</label>
                  <input className="input-field" type="number" value={toInputValue(engineInput.donationsEligible)}
                    onChange={e => setEngineInput({ ...engineInput, donationsEligible: toInputNumber(e.target.value) })} />
                </div>
              </div>
            )}

            {engineStep === 4 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">HRA Received (₹)</label>
                  <input className="input-field" type="number" value={toInputValue(engineInput.housing.hraReceived)}
                    onChange={e => setEngineInput({ ...engineInput, housing: { ...engineInput.housing, hraReceived: toInputNumber(e.target.value) } })} />
                </div>
                <div>
                  <label className="label">Annual Rent Paid (₹)</label>
                  <input className="input-field" type="number" value={toInputValue(engineInput.housing.annualRentPaid)}
                    onChange={e => setEngineInput({ ...engineInput, housing: { ...engineInput.housing, annualRentPaid: toInputNumber(e.target.value) } })} />
                </div>
                <div>
                  <label className="label">Basic Salary (₹)</label>
                  <input className="input-field" type="number" value={toInputValue(engineInput.housing.basicSalary)}
                    onChange={e => setEngineInput({ ...engineInput, housing: { ...engineInput.housing, basicSalary: toInputNumber(e.target.value) } })} />
                </div>
                <div>
                  <label className="label">Metro City</label>
                  <select className="input-field" value={engineInput.housing.isMetroCity ? 'yes' : 'no'}
                    onChange={e => setEngineInput({ ...engineInput, housing: { ...engineInput.housing, isMetroCity: e.target.value === 'yes' } })}>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 mt-5">
              {engineStep > 1 && (
                <button className="btn-secondary" onClick={() => setEngineStep(engineStep - 1)}>Previous</button>
              )}
              {engineStep < 4 && (
                <button className="btn-secondary" onClick={() => setEngineStep(engineStep + 1)}>Next</button>
              )}
              <button className="btn-primary" onClick={runEngine}>Run Full Optimization</button>
            </div>
          </div>

          {engineResult && (
            <>
              <div className="card glass-card neon-gradient-border">
                <div className="flex items-center justify-between gap-3 mb-3">
                  <div>
                    <p className="section-title">AI Tax Strategy</p>
                    <p className="text-sm accent-violet" style={{ marginTop: 4 }}>
                      Precision optimization across regime, deductions, and filing timelines
                    </p>
                  </div>
                  <span className="badge badge-green pulse-tax-badge">TAX EXEMPT</span>
                </div>
                <div className="space-y-1">
                  {engineResult.assumptions.slice(0, 3).map((line, i) => (
                    <p key={i} className={`text-xs ${i === 0 ? 'typing-cursor' : ''}`} style={{ color: 'var(--text-muted)' }}>
                      - {line}
                    </p>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="card">
                  <p className="section-title">Current Tax</p>
                  <p className="num" style={{ fontSize: 20, color: 'var(--red)' }}>₹{engineResult.currentEstimatedTaxLiability.toLocaleString('en-IN')}</p>
                </div>
                <div className="card">
                  <p className="section-title">Optimized Tax</p>
                  <p className="num" style={{ fontSize: 20, color: 'var(--green)' }}>₹{engineResult.optimizedTaxLiability.toLocaleString('en-IN')}</p>
                </div>
                <div className="card">
                  <p className="section-title">Potential Savings</p>
                  <p className="num" style={{ fontSize: 20, color: 'var(--accent)' }}>₹{engineResult.totalPotentialSavings.toLocaleString('en-IN')}</p>
                </div>
                <div className="card">
                  <p className="section-title">Recommended Regime</p>
                  <p className="num" style={{ fontSize: 20, color: 'var(--yellow)', textTransform: 'uppercase' }}>
                    {engineResult.computation.recommendedRegime}
                  </p>
                </div>
              </div>

              <div className="card">
                <p className="section-title mb-3">Old vs New Regime Comparison</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="card" style={{ background: 'var(--bg-elevated)', padding: '12px 14px' }}>
                    <p className="text-sm mb-2" style={{ color: 'var(--text-primary)' }}>Old Regime</p>
                    <p className="num text-sm" style={{ color: 'var(--text-muted)' }}>Taxable Income: ₹{Math.round(engineResult.computation.oldRegime.taxableIncome).toLocaleString('en-IN')}</p>
                    <p className="num text-sm" style={{ color: 'var(--text-muted)' }}>Total Tax: ₹{Math.round(engineResult.computation.oldRegime.totalTax).toLocaleString('en-IN')}</p>
                  </div>
                  <div className="card" style={{ background: 'var(--bg-elevated)', padding: '12px 14px' }}>
                    <p className="text-sm mb-2" style={{ color: 'var(--text-primary)' }}>New Regime</p>
                    <p className="num text-sm" style={{ color: 'var(--text-muted)' }}>Taxable Income: ₹{Math.round(engineResult.computation.newRegime.taxableIncome).toLocaleString('en-IN')}</p>
                    <p className="num text-sm" style={{ color: 'var(--text-muted)' }}>Total Tax: ₹{Math.round(engineResult.computation.newRegime.totalTax).toLocaleString('en-IN')}</p>
                  </div>
                </div>
              </div>

              <div className="card">
                <p className="section-title mb-3">Top Actionable Strategies</p>
                <div className="space-y-2">
                  {engineResult.strategies.slice(0, 10).map((s, idx) => (
                    <div key={`${s.strategy_name}-${idx}`} className="card" style={{ background: 'var(--bg-elevated)', padding: '12px 14px' }}>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 600 }}>
                            {s.strategy_name} ({s.section})
                          </p>
                          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{s.action_required}</p>
                          <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
                            Deadline: {s.deadline} · Risk: {s.risk_level} · Priority: {s.priority_score}
                          </p>
                          <p style={{ fontSize: 11, color: 'var(--accent)', marginTop: 2 }}>
                            Did you know? {s.did_you_know_tip}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="num" style={{ color: 'var(--green)', fontSize: 14, fontWeight: 700 }}>
                            ₹{s.estimated_tax_saving_inr.toLocaleString('en-IN')}
                          </p>
                          {s.quick_win && <span className="badge badge-green" style={{ marginTop: 4 }}>Quick Win</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="card">
                  <p className="section-title mb-2">FY-End Checklist</p>
                  {engineResult.checklist.map((c, i) => (
                    <p key={i} className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>- {c}</p>
                  ))}
                </div>
                <div className="card">
                  <p className="section-title mb-2">Advance Tax Calendar</p>
                  {engineResult.advanceTaxChecklist.map((c, i) => (
                    <p key={i} className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>- {c}</p>
                  ))}
                </div>
              </div>

              <div className="card card-yellow">
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  This is for informational purposes only. Please consult a Chartered Accountant (CA) for personalized tax advice.
                </p>
              </div>
            </>
          )}
        </div>
      )}

      {/* Capital Gains Tab */}
      {activeTab === 'capital_gains' && (
        <div className="space-y-4 animate-fade-in">
          <div className="card">
            <div className="flex items-center gap-2 mb-5">
              <TrendingDown size={14} style={{ color: 'var(--red)' }} />
              <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>
                Capital Gains Calculator
              </span>
              <span className="badge badge-blue" style={{ fontSize: 10 }}>Budget 2024</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Asset Type</label>
                <select className="input-field" value={cgForm.asset_type}
                  onChange={e => setCgForm({ ...cgForm, asset_type: e.target.value })}>
                  <option value="equity">Equity</option>
                  <option value="debt">Debt</option>
                  <option value="gold">Gold</option>
                </select>
              </div>
              <div>
                <label className="label">Tax Regime</label>
                <select className="input-field" value={cgForm.tax_regime}
                  onChange={e => setCgForm({ ...cgForm, tax_regime: e.target.value })}>
                  <option value="new_regime">New Regime</option>
                  <option value="old_regime">Old Regime</option>
                </select>
              </div>
              <div>
                <label className="label">Purchase Price (₹)</label>
                <input type="number" className="input-field" value={toInputValue(cgForm.purchase_price)}
                  onChange={e => setCgForm({ ...cgForm, purchase_price: toInputNumber(e.target.value) })} />
              </div>
              <div>
                <label className="label">Sale Price (₹)</label>
                <input type="number" className="input-field" value={toInputValue(cgForm.sale_price)}
                  onChange={e => setCgForm({ ...cgForm, sale_price: toInputNumber(e.target.value) })} />
              </div>
              <div>
                <label className="label">Holding Days</label>
                <input type="number" className="input-field" value={toInputValue(cgForm.holding_days)}
                  onChange={e => setCgForm({ ...cgForm, holding_days: toInputNumber(e.target.value) })} />
              </div>
              <div>
                <label className="label">Annual Income (₹)</label>
                <input type="number" className="input-field" value={toInputValue(cgForm.annual_income)}
                  onChange={e => setCgForm({ ...cgForm, annual_income: toInputNumber(e.target.value) })} />
              </div>
            </div>
            <div className="mt-4 space-y-1">
              {buildRegimeHints(toApiNumber(cgForm.annual_income), cgForm.tax_regime).map((h, i) => (
                <p key={i} className="text-xs" style={{ color: 'var(--text-muted)' }}>- {h}</p>
              ))}
            </div>
            <button onClick={calcCG} disabled={loading} className="btn-primary mt-5">
              {loading ? 'Calculating...' : 'Calculate Tax'}
            </button>
          </div>

          {cgResult && (
            <div className="card animate-fade-up">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle size={14} style={{ color: 'var(--green)' }} />
                <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>Result</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                {[
                  { label: 'Capital Gain',  value: `₹${cgResult.gain?.toLocaleString('en-IN')}`, color: 'var(--green)' },
                  { label: 'Gain Type',     value: cgResult.gain_type,                            color: 'var(--text-primary)' },
                  { label: 'Tax Rate',      value: `${cgResult.tax_rate}%`,                       color: 'var(--yellow)' },
                  { label: 'Total Tax',     value: `₹${cgResult.total_tax?.toLocaleString('en-IN')}`, color: 'var(--red)' },
                ].map(m => (
                  <div key={m.label} className="card" style={{ padding: '12px 14px', background: 'var(--bg-elevated)' }}>
                    <p className="section-title mb-1">{m.label}</p>
                    <p className="num" style={{ fontSize: 17, fontWeight: 700, color: m.color }}>{m.value}</p>
                  </div>
                ))}
              </div>
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '14px 16px', background: 'var(--bg-elevated)', borderRadius: 12,
                border: '1px solid var(--border)',
              }}>
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Net Proceeds After Tax</span>
                <span className="num" style={{ fontSize: 20, fontWeight: 700, color: 'var(--green)' }}>
                  ₹{cgResult.net_proceeds?.toLocaleString('en-IN')}
                </span>
              </div>
              <div className="mt-4 p-3 rounded-xl" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                <p className="section-title mb-2">Strategy Insights</p>
                <div className="space-y-1">
                  {buildCapitalGainHints(cgForm, cgResult).map((h, i) => (
                    <p key={i} className="text-xs" style={{ color: 'var(--text-muted)' }}>- {h}</p>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 80C Tab */}
      {activeTab === '80c' && (
        <div className="space-y-4 animate-fade-in">
          <div className="card">
            <div className="flex items-center gap-2 mb-5">
              <Receipt size={14} style={{ color: 'var(--purple)' }} />
              <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>
                Section 80C Optimizer
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Annual Income (₹)</label>
                <input type="number" className="input-field" value={toInputValue(s80cForm.annual_income)}
                  onChange={e => setS80cForm({ ...s80cForm, annual_income: toInputNumber(e.target.value) })} />
              </div>
              <div>
                <label className="label">Tax Regime</label>
                <select className="input-field" value={s80cForm.tax_regime}
                  onChange={e => setS80cForm({ ...s80cForm, tax_regime: e.target.value })}>
                  <option value="old_regime">Old Regime</option>
                  <option value="new_regime">New Regime</option>
                </select>
              </div>
              <div>
                <label className="label">ELSS Investment (₹)</label>
                <input type="number" className="input-field"
                  value={toInputValue(s80cForm.current_investments.elss)}
                  onChange={e => setS80cForm({ ...s80cForm, current_investments: { ...s80cForm.current_investments, elss: toInputNumber(e.target.value) } })} />
              </div>
              <div>
                <label className="label">PPF Investment (₹)</label>
                <input type="number" className="input-field"
                  value={toInputValue(s80cForm.current_investments.ppf)}
                  onChange={e => setS80cForm({ ...s80cForm, current_investments: { ...s80cForm.current_investments, ppf: toInputNumber(e.target.value) } })} />
              </div>
            </div>
            <div className="mt-4 space-y-1">
              {buildRegimeHints(toApiNumber(s80cForm.annual_income), s80cForm.tax_regime).map((h, i) => (
                <p key={i} className="text-xs" style={{ color: 'var(--text-muted)' }}>- {h}</p>
              ))}
            </div>
            <button onClick={calc80C} disabled={loading} className="btn-primary mt-5">
              {loading ? 'Optimizing...' : 'Optimize 80C'}
            </button>
          </div>

          {s80cResult && (
            <div className="card animate-fade-up">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle size={14} style={{ color: 'var(--green)' }} />
                <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>80C Result</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
                {[
                  { label: 'Tax Before 80C',   value: `₹${s80cResult.tax_before_80c?.toLocaleString('en-IN')}`,   color: 'var(--red)'    },
                  { label: 'Tax After 80C',    value: `₹${s80cResult.tax_after_80c?.toLocaleString('en-IN')}`,    color: 'var(--green)'  },
                  { label: 'Tax Saved',        value: `₹${s80cResult.tax_saved?.toLocaleString('en-IN')}`,        color: 'var(--accent)' },
                  { label: 'Remaining Limit',  value: `₹${s80cResult.remaining_80c_limit?.toLocaleString('en-IN')}`, color: 'var(--yellow)' },
                ].map(m => (
                  <div key={m.label} className="card" style={{ padding: '12px 14px', background: 'var(--bg-elevated)' }}>
                    <p className="section-title mb-1">{m.label}</p>
                    <p className="num" style={{ fontSize: 17, fontWeight: 700, color: m.color }}>{m.value}</p>
                  </div>
                ))}
              </div>

              {s80cResult.recommendations?.length > 0 && (
                <>
                  <p className="section-title mb-3">Recommendations</p>
                  <div className="space-y-2">
                    {s80cResult.recommendations.map((r: any, i: number) => (
                      <div key={i} style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        padding: '12px 14px',
                        background: 'var(--bg-elevated)',
                        borderRadius: 10, border: '1px solid var(--border)',
                      }}>
                        <div>
                          <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{r.instrument}</p>
                          <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
                            {r.benefit} · Lock-in: {r.lock_in}
                          </p>
                        </div>
                        <span className="num" style={{ fontSize: 14, fontWeight: 700, color: 'var(--green)' }}>
                          ₹{r.amount?.toLocaleString('en-IN')}
                        </span>
                      </div>
                    ))}
                  </div>
                </>
              )}

              <div className="mt-4 p-3 rounded-xl" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
                <p className="section-title mb-2">Strategy Insights</p>
                <div className="space-y-1">
                  {build80cHints(s80cForm, s80cResult).map((h, i) => (
                    <p key={i} className="text-xs" style={{ color: 'var(--text-muted)' }}>- {h}</p>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
