import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import RiskProfile from './pages/RiskProfile';
import Portfolio from './pages/Portfolio';
import Goals from './pages/Goals';
import Retirement from './pages/Retirement';
import Tax from './pages/Tax';
import News from './pages/News';
import Layout from './components/Layout';
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  return token ? <>{children}</> : <Navigate to="/login" />;
};
function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{style:{background:'#1e293b',color:'#e2e8f0',border:'1px solid #334155'}}}/>
      <Routes>
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<PrivateRoute><Layout><Dashboard/></Layout></PrivateRoute>}/>
        <Route path="/risk" element={<PrivateRoute><Layout><RiskProfile/></Layout></PrivateRoute>}/>
        <Route path="/portfolio" element={<PrivateRoute><Layout><Portfolio/></Layout></PrivateRoute>}/>
        <Route path="/goals" element={<PrivateRoute><Layout><Goals/></Layout></PrivateRoute>}/>
        <Route path="/retirement" element={<PrivateRoute><Layout><Retirement/></Layout></PrivateRoute>}/>
        <Route path="/tax" element={<PrivateRoute><Layout><Tax/></Layout></PrivateRoute>}/>
        <Route path="/news" element={<PrivateRoute><Layout><News/></Layout></PrivateRoute>}/>
        <Route path="*" element={<Navigate to="/" />}/>
      </Routes>
    </BrowserRouter>
  );
}
export default App;
