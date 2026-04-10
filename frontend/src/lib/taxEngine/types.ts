export type EmploymentType = 'salaried' | 'business' | 'both';
export type RegimePreference = 'old' | 'new' | 'auto';
export type RiskLevel = 'Low' | 'Medium' | 'High';
export type ProfileApplicability = 'Salaried' | 'Business' | 'Both';

export interface ExistingInvestments {
  epf: number;
  ppf: number;
  elss: number;
  npsSelf: number;
  npsEmployer: number;
  lic: number;
  nsc: number;
  taxSaverFd: number;
  tuitionFees: number;
  homeLoanPrincipal: number;
  ulip: number;
}

export interface BusinessExpenses {
  officeRent: number;
  salaries: number;
  utilities: number;
  depreciation: number;
  travel: number;
  marketing: number;
  software: number;
  professionalFees: number;
  homeOffice: number;
  vehicleFuelMaintenance: number;
  epfEmployerContribution: number;
}

export interface OtherIncome {
  rental: number;
  capitalGains: number;
  interest: number;
  freelance: number;
}

export interface FamilyDetails {
  dependents: number;
  seniorCitizenParents: boolean;
  spouseIncome: number;
}

export interface ExistingDeductionsClaimed {
  section80CUsed: number;
  section80DUsed: number;
  section80CCD1BUsed: number;
  section24BUsed: number;
  section80EUsed: number;
  section80GUsed: number;
}

export interface HousingDetails {
  hraReceived: number;
  annualRentPaid: number;
  isMetroCity: boolean;
  basicSalary: number;
}

export interface TaxEngineInput {
  employmentType: EmploymentType;
  salaryIncome: number;
  businessRevenue: number;
  businessProfit: number;
  regimePreference: RegimePreference;
  existingInvestments: ExistingInvestments;
  businessExpenses: BusinessExpenses;
  otherIncome: OtherIncome;
  family: FamilyDetails;
  existingDeductionsClaimed: ExistingDeductionsClaimed;
  healthInsuranceSelfFamily: number;
  healthInsuranceParents: number;
  educationLoanInterest: number;
  donationsEligible: number;
  ltaClaim: number;
  housing: HousingDetails;
}

export interface StrategyOutput {
  strategy_name: string;
  section: string;
  profile_applicability: ProfileApplicability;
  estimated_tax_saving_inr: number;
  action_required: string;
  deadline: string;
  risk_level: RiskLevel;
  priority_score: number;
  quick_win: boolean;
  did_you_know_tip: string;
}

export interface TaxBreakdown {
  grossIncome: number;
  taxableIncome: number;
  incomeTax: number;
  surcharge: number;
  cess: number;
  rebate: number;
  totalTax: number;
}

export interface TaxComputationResult {
  oldRegime: TaxBreakdown;
  newRegime: TaxBreakdown;
  recommendedRegime: 'old' | 'new';
  regimeDeltaSavings: number;
}

export interface TaxEngineResult {
  computation: TaxComputationResult;
  strategies: StrategyOutput[];
  currentEstimatedTaxLiability: number;
  optimizedTaxLiability: number;
  totalPotentialSavings: number;
  checklist: string[];
  advanceTaxChecklist: string[];
  assumptions: string[];
  confidence: 'High' | 'Medium' | 'Low';
}
