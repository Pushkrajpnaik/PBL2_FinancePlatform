import { TaxBreakdown, TaxComputationResult, TaxEngineInput } from './types';

const CESS_RATE = 0.04;

const NEW_SLABS = [
  { upTo: 400000, rate: 0 },
  { upTo: 800000, rate: 0.05 },
  { upTo: 1200000, rate: 0.1 },
  { upTo: 1600000, rate: 0.15 },
  { upTo: 2000000, rate: 0.2 },
  { upTo: 2400000, rate: 0.25 },
  { upTo: Number.POSITIVE_INFINITY, rate: 0.3 },
];

const OLD_SLABS = [
  { upTo: 250000, rate: 0 },
  { upTo: 500000, rate: 0.05 },
  { upTo: 1000000, rate: 0.2 },
  { upTo: Number.POSITIVE_INFINITY, rate: 0.3 },
];

const surchargeRate = (taxableIncome: number, regime: 'old' | 'new') => {
  if (taxableIncome <= 5000000) return 0;
  if (taxableIncome <= 10000000) return 0.1;
  if (taxableIncome <= 20000000) return 0.15;
  if (taxableIncome <= 50000000) return 0.25;
  return regime === 'new' ? 0.25 : 0.37;
};

const computeSlabTax = (taxableIncome: number, slabs: { upTo: number; rate: number }[]) => {
  let tax = 0;
  let prev = 0;
  for (const slab of slabs) {
    if (taxableIncome <= prev) break;
    const amountInSlab = Math.min(taxableIncome, slab.upTo) - prev;
    tax += amountInSlab * slab.rate;
    prev = slab.upTo;
  }
  return Math.max(0, tax);
};

const safe = (n: number) => (Number.isFinite(n) ? Math.max(0, n) : 0);

const getBaseIncome = (input: TaxEngineInput) => {
  const salary = safe(input.salaryIncome);
  const business = safe(input.businessProfit);
  const other =
    safe(input.otherIncome.rental) +
    safe(input.otherIncome.capitalGains) +
    safe(input.otherIncome.interest) +
    safe(input.otherIncome.freelance);
  return salary + business + other;
};

const getBusinessDeduction = (input: TaxEngineInput) => {
  if (input.employmentType === 'salaried') return 0;
  const e = input.businessExpenses;
  return (
    safe(e.officeRent) +
    safe(e.salaries) +
    safe(e.utilities) +
    safe(e.depreciation) +
    safe(e.travel) +
    safe(e.marketing) +
    safe(e.software) +
    safe(e.professionalFees) +
    safe(e.homeOffice) +
    safe(e.vehicleFuelMaintenance) +
    safe(e.epfEmployerContribution)
  );
};

const getOldRegimeDeductions = (input: TaxEngineInput) => {
  const i = input.existingInvestments;
  const eightyCEligible =
    safe(i.epf) +
    safe(i.ppf) +
    safe(i.elss) +
    safe(i.lic) +
    safe(i.nsc) +
    safe(i.taxSaverFd) +
    safe(i.tuitionFees) +
    safe(i.homeLoanPrincipal) +
    safe(i.ulip);
  const sec80C = Math.min(150000, eightyCEligible);
  const sec80CCD1B = Math.min(50000, safe(i.npsSelf));
  const sec80DParentsCap = input.family.seniorCitizenParents ? 50000 : 25000;
  const sec80D =
    Math.min(25000, safe(input.healthInsuranceSelfFamily)) +
    Math.min(sec80DParentsCap, safe(input.healthInsuranceParents));
  const sec24B = Math.min(200000, safe(input.existingDeductionsClaimed.section24BUsed));
  const sec80E = safe(input.educationLoanInterest);
  const sec80G = Math.min(safe(input.donationsEligible), 1000000);
  const hra = computeHraExemption(input);
  const lta = safe(input.ltaClaim);
  const standard = input.employmentType === 'business' ? 0 : 50000;
  return sec80C + sec80CCD1B + sec80D + sec24B + sec80E + sec80G + hra + lta + standard;
};

const getNewRegimeDeductions = (input: TaxEngineInput) => {
  const standard = input.employmentType === 'business' ? 0 : 75000;
  const npsEmployer = Math.min(
    safe(input.existingInvestments.npsEmployer),
    Math.max(0, safe(input.housing.basicSalary) * 0.14),
  );
  return standard + npsEmployer;
};

export const computeHraExemption = (input: TaxEngineInput) => {
  const hraReceived = safe(input.housing.hraReceived);
  const annualRent = safe(input.housing.annualRentPaid);
  const basicSalary = safe(input.housing.basicSalary);
  if (hraReceived <= 0 || annualRent <= 0 || basicSalary <= 0) return 0;
  const rentMinusTenPercentBasic = Math.max(0, annualRent - basicSalary * 0.1);
  const cityCap = input.housing.isMetroCity ? basicSalary * 0.5 : basicSalary * 0.4;
  return Math.max(0, Math.min(hraReceived, rentMinusTenPercentBasic, cityCap));
};

const buildBreakdown = (
  grossIncome: number,
  taxableIncome: number,
  regime: 'old' | 'new',
  slabs: { upTo: number; rate: number }[],
): TaxBreakdown => {
  const taxBeforeRebate = computeSlabTax(taxableIncome, slabs);
  const rebate = regime === 'new' && taxableIncome <= 700000 ? Math.min(25000, taxBeforeRebate) : 0;
  const incomeTax = Math.max(0, taxBeforeRebate - rebate);
  const surcharge = incomeTax * surchargeRate(taxableIncome, regime);
  const cess = (incomeTax + surcharge) * CESS_RATE;
  const totalTax = incomeTax + surcharge + cess;
  return { grossIncome, taxableIncome, incomeTax, surcharge, cess, rebate, totalTax };
};

export const computeTaxComparison = (input: TaxEngineInput): TaxComputationResult => {
  const grossIncome = getBaseIncome(input);
  const businessDeduction = getBusinessDeduction(input);
  const oldTaxableIncome = Math.max(0, grossIncome - businessDeduction - getOldRegimeDeductions(input));
  const newTaxableIncome = Math.max(0, grossIncome - businessDeduction - getNewRegimeDeductions(input));

  const oldRegime = buildBreakdown(grossIncome, oldTaxableIncome, 'old', OLD_SLABS);
  const newRegime = buildBreakdown(grossIncome, newTaxableIncome, 'new', NEW_SLABS);

  const recommendedRegime = oldRegime.totalTax <= newRegime.totalTax ? 'old' : 'new';
  return {
    oldRegime,
    newRegime,
    recommendedRegime,
    regimeDeltaSavings: Math.abs(oldRegime.totalTax - newRegime.totalTax),
  };
};

export const marginalRate = (taxableIncome: number, regime: 'old' | 'new') => {
  const slabs = regime === 'old' ? OLD_SLABS : NEW_SLABS;
  for (const slab of slabs) {
    if (taxableIncome <= slab.upTo) return slab.rate;
  }
  return 0.3;
};
