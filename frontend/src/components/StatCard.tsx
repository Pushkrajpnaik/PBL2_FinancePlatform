import React from 'react';
interface StatCardProps { title: string; value: string; subtitle?: string; icon?: React.ReactNode; color?: 'blue'|'green'|'red'|'yellow'|'purple'; }
const colorMap: any = { blue:'bg-blue-500/20 text-blue-400', green:'bg-green-500/20 text-green-400', red:'bg-red-500/20 text-red-400', yellow:'bg-yellow-500/20 text-yellow-400', purple:'bg-purple-500/20 text-purple-400' };
export default function StatCard({ title, value, subtitle, icon, color='blue' }: StatCardProps) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {subtitle && <p className="text-slate-500 text-xs mt-1">{subtitle}</p>}
        </div>
        {icon && <div className={`p-3 rounded-lg ${colorMap[color]}`}>{icon}</div>}
      </div>
    </div>
  );
}
