import { computeTaxComparison, marginalRate } from './calculator';
import { StrategyOutput, TaxEngineInput, TaxEngineResult } from './types';

const round = (n: number) => Math.max(0, Math.round(n));
const safe = (n: number) => (Number.isFinite(n) ? Math.max(0, n) : 0);

const createStrategy = (s: StrategyOutput): StrategyOutput => s;

const salariedStrategies = (input: TaxEngineInput, regime: 'old' | 'new'): StrategyOutput[] => {
  const gross = safe(input.salaryIncome);
  const taxRate = marginalRate(gross, regime);
  const inv = input.existingInvestments;
  const items: StrategyOutput[] = [];
  const eightyCUsed =
    safe(inv.epf) + safe(inv.ppf) + safe(inv.elss) + safe(inv.lic) + safe(inv.nsc) + safe(inv.taxSaverFd) +
    safe(inv.tuitionFees) + safe(inv.homeLoanPrincipal) + safe(inv.ulip);
  const eightyCGap = Math.max(0, 150000 - eightyCUsed);
  if (eightyCGap > 0 && regime === 'old') {
    items.push(createStrategy({
      strategy_name: 'Maximise Section 80C basket',
      section: '80C',
      profile_applicability: 'Salaried',
      estimated_tax_saving_inr: round(eightyCGap * taxRate),
      action_required: 'Add ELSS/PPF/EPF/NSC/5-year FD mix to fill remaining 80C limit.',
      deadline: 'Before March 31',
      risk_level: 'Low',
      priority_score: 80,
      quick_win: true,
      did_you_know_tip: 'ELSS has the shortest 80C lock-in (3 years).',
    }));
  }

  const npsSelfGap = Math.max(0, 50000 - safe(inv.npsSelf));
  if (npsSelfGap > 0 && regime === 'old') {
    items.push(createStrategy({
      strategy_name: 'Use extra NPS deduction',
      section: '80CCD(1B)',
      profile_applicability: 'Salaried',
      estimated_tax_saving_inr: round(npsSelfGap * taxRate),
      action_required: 'Invest up to additional ₹50,000 in NPS Tier-1 beyond 80C.',
      deadline: 'Before March 31',
      risk_level: 'Low',
      priority_score: 78,
      quick_win: true,
      did_you_know_tip: '80CCD(1B) is over and above 80C cap.',
    }));
  }

  const selfFamGap = Math.max(0, 25000 - safe(input.healthInsuranceSelfFamily));
  const parentCap = input.family.seniorCitizenParents ? 50000 : 25000;
  const parentGap = Math.max(0, parentCap - safe(input.healthInsuranceParents));
  const sec80dGap = selfFamGap + parentGap;
  if (sec80dGap > 0 && regime === 'old') {
    items.push(createStrategy({
      strategy_name: 'Optimise family health insurance deduction',
      section: '80D',
      profile_applicability: 'Salaried',
      estimated_tax_saving_inr: round(sec80dGap * taxRate),
      action_required: 'Top up mediclaim for self/family and parents within 80D caps.',
      deadline: 'Before policy year-end / March 31',
      risk_level: 'Low',
      priority_score: 74,
      quick_win: true,
      did_you_know_tip: 'Parents can unlock additional deduction, higher for senior citizens.',
    }));
  }

  items.push(createStrategy({
    strategy_name: 'Salary restructuring for tax efficiency',
    section: 'Salary Structuring',
    profile_applicability: 'Salaried',
    estimated_tax_saving_inr: round(Math.min(150000, gross * 0.03)),
    action_required: 'Discuss NPS employer contribution, meal cards, reimbursements with payroll team.',
    deadline: 'At start of payroll cycle',
    risk_level: 'Medium',
    priority_score: 68,
    quick_win: false,
    did_you_know_tip: 'Employer NPS under 80CCD(2) is available in both regimes.',
  }));

  return items;
};

const businessStrategies = (input: TaxEngineInput, regime: 'old' | 'new'): StrategyOutput[] => {
  const businessProfit = safe(input.businessProfit);
  const taxRate = marginalRate(businessProfit, regime);
  const e = input.businessExpenses;
  const undocumentedExpenseBucket = Math.max(0, safe(input.businessRevenue) * 0.08 - (
    safe(e.officeRent) + safe(e.utilities) + safe(e.software) + safe(e.professionalFees) + safe(e.marketing)
  ));

  const items: StrategyOutput[] = [
    createStrategy({
      strategy_name: 'Capture all legitimate business expenses',
      section: 'Business Deduction',
      profile_applicability: 'Business',
      estimated_tax_saving_inr: round(undocumentedExpenseBucket * taxRate),
      action_required: 'Record rent, utilities, software, travel, professional fees with invoices.',
      deadline: 'Ongoing monthly bookkeeping',
      risk_level: 'Low',
      priority_score: 85,
      quick_win: true,
      did_you_know_tip: 'Clean documentation is as important as the deduction itself.',
    }),
    createStrategy({
      strategy_name: 'Evaluate presumptive taxation route',
      section: '44AD / 44ADA',
      profile_applicability: 'Business',
      estimated_tax_saving_inr: round(Math.min(120000, businessProfit * 0.02)),
      action_required: 'Compare normal books vs presumptive method based on actual margins and compliance cost.',
      deadline: 'Before ITR filing and advance-tax estimation',
      risk_level: 'Medium',
      priority_score: 70,
      quick_win: false,
      did_you_know_tip: 'Presumptive route can simplify compliance significantly.',
    }),
    createStrategy({
      strategy_name: 'Entity structure review',
      section: 'Business Structuring',
      profile_applicability: 'Business',
      estimated_tax_saving_inr: round(Math.min(250000, Math.max(0, businessProfit - 2000000) * 0.03)),
      action_required: 'Review sole prop vs LLP vs Pvt Ltd with CA based on profit scale and expansion plans.',
      deadline: 'Before next FY begins',
      risk_level: 'High',
      priority_score: 62,
      quick_win: false,
      did_you_know_tip: 'Correct structure improves both taxes and funding readiness.',
    }),
    createStrategy({
      strategy_name: 'Advance tax planning calendar',
      section: '234B / 234C',
      profile_applicability: 'Business',
      estimated_tax_saving_inr: round(Math.min(50000, businessProfit * 0.01)),
      action_required: 'Pay advance tax in quarterly milestones to avoid interest outgo.',
      deadline: 'Jun 15, Sep 15, Dec 15, Mar 15',
      risk_level: 'Low',
      priority_score: 75,
      quick_win: true,
      did_you_know_tip: 'Even correct annual tax can attract interest if paid late.',
    }),
  ];

  return items;
};

const investmentStrategies = (input: TaxEngineInput, regime: 'old' | 'new'): StrategyOutput[] => {
  const baseIncome = safe(input.salaryIncome) + safe(input.businessProfit);
  const taxRate = marginalRate(baseIncome, regime);
  return [
    createStrategy({
      strategy_name: 'Tax-loss harvesting for gains offset',
      section: 'Capital Gains Set-off',
      profile_applicability: 'Both',
      estimated_tax_saving_inr: round(Math.min(100000, safe(input.otherIncome.capitalGains) * 0.125)),
      action_required: 'Harvest eligible losses before March 31 after cost-benefit check.',
      deadline: 'Before March 31',
      risk_level: 'Medium',
      priority_score: 72,
      quick_win: true,
      did_you_know_tip: 'Loss carry-forward requires timely ITR filing.',
    }),
    createStrategy({
      strategy_name: 'NPS + retirement bucket optimization',
      section: '80CCD / Retirement',
      profile_applicability: 'Both',
      estimated_tax_saving_inr: round(Math.min(50000, 50000 * taxRate)),
      action_required: 'Use NPS Tier-1 as part of long-term retirement allocation and tax planning.',
      deadline: 'Before March 31',
      risk_level: 'Low',
      priority_score: 66,
      quick_win: true,
      did_you_know_tip: 'NPS can improve both tax efficiency and discipline.',
    }),
    createStrategy({
      strategy_name: 'SGB and tax-efficient asset location',
      section: 'Capital Gains Planning',
      profile_applicability: 'Both',
      estimated_tax_saving_inr: round(Math.min(75000, safe(input.otherIncome.capitalGains) * 0.05)),
      action_required: 'Use tax-efficient instruments for long-horizon allocation and rebalance tax-aware.',
      deadline: 'During annual portfolio rebalance',
      risk_level: 'Medium',
      priority_score: 60,
      quick_win: false,
      did_you_know_tip: 'SGB maturity gains are exempt for individual investors.',
    }),
  ];
};

export const runTaxOptimizationEngine = (input: TaxEngineInput): TaxEngineResult => {
  const computation = computeTaxComparison(input);
  const selectedRegime =
    input.regimePreference === 'auto' ? computation.recommendedRegime : input.regimePreference;

  const strategies: StrategyOutput[] = [];
  if (input.employmentType !== 'business') strategies.push(...salariedStrategies(input, selectedRegime));
  if (input.employmentType !== 'salaried') strategies.push(...businessStrategies(input, selectedRegime));
  strategies.push(...investmentStrategies(input, selectedRegime));

  const deduped = strategies
    .sort((a, b) => b.estimated_tax_saving_inr - a.estimated_tax_saving_inr)
    .map(s => ({
      ...s,
      priority_score: Math.round(s.priority_score + Math.min(20, s.estimated_tax_saving_inr / 20000)),
    }))
    .sort((a, b) => b.priority_score - a.priority_score || b.estimated_tax_saving_inr - a.estimated_tax_saving_inr);

  const topSavings = deduped.reduce((sum, s) => sum + s.estimated_tax_saving_inr, 0);
  const currentEstimatedTaxLiability =
    input.regimePreference === 'old' ? computation.oldRegime.totalTax :
    input.regimePreference === 'new' ? computation.newRegime.totalTax :
    Math.max(computation.oldRegime.totalTax, computation.newRegime.totalTax);

  const optimizedTaxLiability = Math.max(
    0,
    (selectedRegime === 'old' ? computation.oldRegime.totalTax : computation.newRegime.totalTax) - topSavings,
  );

  return {
    computation,
    strategies: deduped,
    currentEstimatedTaxLiability: round(currentEstimatedTaxLiability),
    optimizedTaxLiability: round(optimizedTaxLiability),
    totalPotentialSavings: round(Math.max(0, currentEstimatedTaxLiability - optimizedTaxLiability)),
    checklist: [
      'Complete all deduction investments and proofs before March 31.',
      'Re-evaluate Old vs New regime with full-year actuals before ITR filing.',
      'Reconcile AIS/26AS entries with broker and bank statements.',
      'Capture all eligible business and rental documentation.',
    ],
    advanceTaxChecklist: [
      '15 June - 15% of estimated tax',
      '15 September - 45% cumulative',
      '15 December - 75% cumulative',
      '15 March - 100% cumulative',
    ],
    assumptions: [
      'Computation uses simplified slab model and declared inputs.',
      'Exemptions with special conditions are estimated conservatively.',
      'Surcharge is approximated by taxable income threshold.',
    ],
    confidence: 'Medium',
  };
};
