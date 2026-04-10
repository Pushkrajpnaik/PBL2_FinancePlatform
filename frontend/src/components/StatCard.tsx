import React from 'react';

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple';
  trend?: 'up' | 'down' | 'neutral';
  mono?: boolean;
}

const colorTokens: Record<string, { text: string; bg: string; border: string; glow: string }> = {
  blue:   { text: 'var(--accent)',  bg: 'var(--accent-dim)',           border: 'rgba(59,158,255,0.2)',  glow: 'rgba(59,158,255,0.15)' },
  green:  { text: 'var(--green)',   bg: 'var(--green-dim)',            border: 'rgba(16,217,138,0.2)',  glow: 'rgba(16,217,138,0.12)' },
  red:    { text: 'var(--red)',     bg: 'var(--red-dim)',              border: 'rgba(255,82,82,0.2)',   glow: 'rgba(255,82,82,0.12)'  },
  yellow: { text: 'var(--yellow)',  bg: 'var(--yellow-dim)',           border: 'rgba(255,192,71,0.2)',  glow: 'rgba(255,192,71,0.12)' },
  purple: { text: 'var(--purple)',  bg: 'var(--purple-dim)',           border: 'rgba(167,139,250,0.2)', glow: 'rgba(167,139,250,0.12)'},
};

export default function StatCard({ title, value, subtitle, icon, color = 'blue', trend, mono = true }: StatCardProps) {
  const c = colorTokens[color];

  return (
    <div
      className="card"
      style={{ borderColor: c.border }}
    >
      {/* Subtle top glow line */}
      <div style={{
        position: 'absolute', top: 0, left: '15%', right: '15%', height: 1,
        background: `linear-gradient(90deg, transparent, ${c.text}, transparent)`,
        opacity: 0.4,
      }} />

      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="section-title mb-2">{title}</p>
          <p
            className={mono ? 'num' : ''}
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: 'var(--text-primary)',
              lineHeight: 1.1,
              letterSpacing: '-0.03em',
            }}
          >
            {value}
          </p>
          {subtitle && (
            <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
              {subtitle}
            </p>
          )}
        </div>

        {icon && (
          <div
            className="shrink-0 flex items-center justify-center rounded-xl"
            style={{
              width: 36, height: 36,
              background: c.bg,
              color: c.text,
              border: `1px solid ${c.border}`,
            }}
          >
            {icon}
          </div>
        )}
      </div>

      {/* Optional trend indicator */}
      {trend && (
        <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--border)' }}>
          <span style={{
            fontSize: 10,
            fontWeight: 600,
            color: trend === 'up' ? 'var(--green)' : trend === 'down' ? 'var(--red)' : 'var(--text-dim)',
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
          }}>
            {trend === 'up' ? '▲ Trending Up' : trend === 'down' ? '▼ Trending Down' : '→ Stable'}
          </span>
        </div>
      )}
    </div>
  );
}
