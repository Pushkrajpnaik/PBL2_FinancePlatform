import axios from 'axios';
const API_BASE = 'http://localhost:8000/api/v1';
const api = axios.create({ baseURL: API_BASE, headers: { 'Content-Type': 'application/json' } });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) { localStorage.removeItem('token'); window.location.href = '/login'; }
    return Promise.reject(error);
  }
);
export const authAPI = {
  register: (data: any) => api.post('/auth/register', data),
  login:    (data: any) => api.post('/auth/login', data),
  me:       ()          => api.get('/users/me'),
};
export const riskAPI = {
  getQuestionnaire: ()          => api.get('/risk/questionnaire'),
  assess:           (data: any) => api.post('/risk/assess', data),
  getMyProfile:     ()          => api.get('/risk/me'),
};
export const simulationAPI = {
  run:   (data: any) => api.post('/simulation/run', data),
  quick: ()          => api.post('/simulation/quick'),
};
export const portfolioAPI = {
  optimize:    (data: any) => api.post('/portfolio/optimize', data),
  optimizeAll: (data: any) => api.post('/portfolio/optimize/all', data),
  myPortfolio: ()          => api.get('/portfolio/my-portfolio'),
};
export const goalsAPI = {
  getTemplates: ()          => api.get('/goals/templates'),
  analyze:      (data: any) => api.post('/goals/analyze', data),
  save:         (data: any) => api.post('/goals/save', data),
  myGoals:      ()          => api.get('/goals/my-goals'),
};
export const retirementAPI = {
  calculate: (data: any) => api.post('/retirement/calculate', data),
  save:      (data: any) => api.post('/retirement/save', data),
  myPlan:    ()          => api.get('/retirement/my-plan'),
};
export const taxAPI = {
  capitalGains:       (data: any) => api.post('/tax/capital-gains', data),
  optimize80c:        (data: any) => api.post('/tax/optimize-80c', data),
  afterTaxComparison: (data: any) => api.post('/tax/after-tax-comparison', data),
  getRules:           ()          => api.get('/tax/rules'),
};
export const newsAPI = {
  marketSentiment: ()               => api.get('/news/market-sentiment'),
  latest:          (cat: string)    => api.get(`/news/latest?category=${cat}`),
  analyzeText:     (text: string)   => api.post('/news/analyze-text', { text }),
  riskAlerts:      ()               => api.get('/news/risk-alerts'),
  sectorSentiment: (sector: string) => api.get(`/news/sector-sentiment/${sector}`),
};
export const predictionAPI = {
  marketRegime:            () => api.get('/prediction/market-regime'),
  regimeAdjustedPortfolio: () => api.get('/prediction/regime-adjusted-portfolio'),
};
export default api;
