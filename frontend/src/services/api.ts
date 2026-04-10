import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Auto attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto logout on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  register: (data: any) => api.post('/auth/register', data),
  login:    (data: any) => api.post('/auth/login', data),
  me:       ()          => api.get('/users/me'),
};

// Risk Profile
export const riskAPI = {
  getQuestionnaire: ()          => api.get('/risk/questionnaire'),
  assess:           (data: any) => api.post('/risk/assess', data),
  getMyProfile:     ()          => api.get('/risk/me'),
};

// Simulation
export const simulationAPI = {
  run:   (data: any) => api.post('/simulation/run', data),
  quick: ()          => api.post('/simulation/quick'),
};

// Portfolio
export const portfolioAPI = {
  optimize:    (data: any) => api.post('/portfolio/optimize', data),
  optimizeAll: (data: any) => api.post('/portfolio/optimize/all', data),
  myPortfolio: ()          => api.get('/portfolio/my-portfolio'),
};

// Goals
export const goalsAPI = {
  getTemplates: ()          => api.get('/goals/templates'),
  analyze:      (data: any) => api.post('/goals/analyze', data),
  save:         (data: any) => api.post('/goals/save', data),
  myGoals:      ()          => api.get('/goals/my-goals'),
};

// Retirement
export const retirementAPI = {
  calculate: (data: any) => api.post('/retirement/calculate', data),
  save:      (data: any) => api.post('/retirement/save', data),
  myPlan:    ()          => api.get('/retirement/my-plan'),
};

// Tax
export const taxAPI = {
  capitalGains:       (data: any) => api.post('/tax/capital-gains', data),
  optimize80c:        (data: any) => api.post('/tax/optimize-80c', data),
  afterTaxComparison: (data: any) => api.post('/tax/after-tax-comparison', data),
  getRules:           ()          => api.get('/tax/rules'),
};

// News
export const newsAPI = {
  marketSentiment: ()               => api.get('/news/market-sentiment'),
  latest:          (cat: string)    => api.get(`/news/latest?category=${cat}`),
  analyzeText:     (text: string)   => api.post('/news/analyze-text', { text }),
  riskAlerts:      ()               => api.get('/news/risk-alerts'),
  sectorSentiment: (sector: string) => api.get(`/news/sector-sentiment/${sector}`),
};

// Market Data (live endpoints)
export const marketAPI = {
  summary:         (refresh = false) => api.get(`/market/summary`),
  nifty50:         (period: string)  => api.get(`/market/nifty50?period=${period}`),
  stock:           (symbol: string)  => api.get(`/market/stock/${symbol}`),
  allStocks:       ()                => api.get('/market/stocks/all'),
  macro:           ()                => api.get('/market/macro'),
  gold:            ()                => api.get('/market/gold'),
  liveNews:        (refresh = false) => api.get(`/market/news/live?force_refresh=${refresh}`),
  portfolioSignal: ()                => api.get('/market/portfolio-signal'),
  realRegime:      ()                => api.get('/market/regime/real'),
  popularFunds:    ()                => api.get('/market/mutual-funds/popular'),
  searchFunds:     (q: string)       => api.get(`/market/mutual-funds/search?query=${encodeURIComponent(q)}`),
  fundDetails:     (code: string)    => api.get(`/market/mutual-funds/${code}`),
};

// Prediction (all endpoints including new live ones)
export const predictionAPI = {
  marketRegime:            () => api.get('/prediction/market-regime'),
  regimeAdjustedPortfolio: () => api.get('/prediction/regime-adjusted-portfolio'),
  regimeHistory:           () => api.get('/prediction/market-regime/history'),
  investmentSignal:        () => api.get('/prediction/investment-signal'),
  arimaPredict:            () => api.get('/prediction/nifty50/arima'),
  xgboostPredict:          () => api.get('/prediction/nifty50/xgboost'),
  combinedPredict:         () => api.get('/prediction/nifty50/combined'),
  newsAdjustedArima:       () => api.get('/prediction/nifty50/news-adjusted-arima'),
  backtestFull:            () => api.get('/prediction/backtest/full?period=3y'),
  backtestCompare:         () => api.get('/prediction/backtest/compare-all?period=3y'),
  equityCurve:             () => api.get('/prediction/backtest/equity-curve?period=2y'),
};

export default api;