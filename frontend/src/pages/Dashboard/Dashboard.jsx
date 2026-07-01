import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { dashboard, billing } from '../../services/api';
import './Dashboard.css';

// Animated counter hook
function useCountUp(target, duration = 1200) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (target === null || target === undefined) return;
    let start = 0;
    const end = parseInt(target, 10);
    if (isNaN(end)) { setCount(target); return; }
    if (end === 0) { setCount(0); return; }
    
    const step = Math.max(1, Math.ceil(end / (duration / 16)));
    const timer = setInterval(() => {
      start += step;
      if (start >= end) {
        start = end;
        clearInterval(timer);
      }
      setCount(start);
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration]);

  return count;
}

// Donut chart component
function DonutChart({ data, size = 160 }) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  let cumulative = 0;
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className="donut-chart-container" role="img" aria-label={`Dispute distribution chart. Total items: ${total}`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="donut-chart">
        {data.map((item, i) => {
          const percentage = total > 0 ? item.value / total : 0;
          const strokeDasharray = `${percentage * circumference} ${circumference}`;
          const strokeDashoffset = -cumulative * circumference;
          cumulative += percentage;
          return (
            <circle
              key={i}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={item.color}
              strokeWidth="16"
              strokeDasharray={strokeDasharray}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
              style={{ transition: 'all 0.8s ease', opacity: 0.9 }}
            />
          );
        })}
        <circle cx={size / 2} cy={size / 2} r={radius - 16} fill="var(--bg-secondary)" />
        <text x={size / 2} y={size / 2 - 8} textAnchor="middle" fill="var(--text-primary)" fontSize="22" fontWeight="700">
          {total}
        </text>
        <text x={size / 2} y={size / 2 + 14} textAnchor="middle" fill="var(--text-muted)" fontSize="11">
          Total Items
        </text>
      </svg>
    </div>
  );
}

// Mock data for demo fallbacks
const mockStats = {
  total_clients: 147,
  active_disputes: 38,
  success_rate: 73,
  monthly_revenue: 24850,
};

const mockPipeline = {
  lead: [
    { id: 1, name: 'Sarah Johnson', email: 'sarah@email.com', score: 520, date: '2026-06-20' },
    { id: 2, name: 'Mike Chen', email: 'mike@email.com', score: 490, date: '2026-06-21' },
  ],
  active: [
    { id: 3, name: 'Emily Davis', email: 'emily@email.com', score: 580, date: '2026-06-15' },
    { id: 4, name: 'James Wilson', email: 'james@email.com', score: 545, date: '2026-06-18' },
    { id: 5, name: 'Lisa Anderson', email: 'lisa@email.com', score: 510, date: '2026-06-19' },
  ],
  in_progress: [
    { id: 6, name: 'Robert Brown', email: 'robert@email.com', score: 610, date: '2026-06-10' },
    { id: 7, name: 'Amanda Taylor', email: 'amanda@email.com', score: 595, date: '2026-06-12' },
  ],
  completed: [
    { id: 8, name: 'David Martinez', email: 'david@email.com', score: 720, date: '2026-05-20' },
  ],
};

const mockDisputeMetrics = [
  { label: 'Resolved', value: 45, color: '#10b981' },
  { label: 'Pending', value: 28, color: '#f59e0b' },
  { label: 'Sent', value: 18, color: '#3b82f6' },
  { label: 'Rejected', value: 9, color: '#ef4444' },
];

const mockActivity = [
  { id: 1, type: 'dispute', message: 'Dispute letter sent for Emily Davis', time: '2 hours ago', icon: '⚖️' },
  { id: 2, type: 'client', message: 'New client Sarah Johnson added', time: '4 hours ago', icon: '👤' },
  { id: 3, type: 'report', message: 'Credit report uploaded for James Wilson', time: '6 hours ago', icon: '📋' },
  { id: 4, type: 'success', message: 'Dispute resolved for David Martinez — item removed!', time: '1 day ago', icon: '✅' },
  { id: 5, type: 'mail', message: 'Certified mail dispatched to Equifax', time: '1 day ago', icon: '📬' },
];

const pipelineConfig = [
  { key: 'lead', label: 'New Leads', color: '#8b5cf6', icon: '🔮' },
  { key: 'active', label: 'Active', color: '#3b82f6', icon: '⚡' },
  { key: 'in_progress', label: 'In Progress', color: '#f59e0b', icon: '🔄' },
  { key: 'completed', label: 'Completed', color: '#10b981', icon: '✅' },
];

export default function Dashboard() {
  const [stats, setStats] = useState(mockStats);
  const [pipeline, setPipeline] = useState(mockPipeline);
  const [disputeMetrics, setDisputeMetrics] = useState(mockDisputeMetrics);
  const [activity, setActivity] = useState(mockActivity);
  const [billingList, setBillingList] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const [s, p, d, a, b] = await Promise.allSettled([
          dashboard.getStats(),
          dashboard.getPipeline(),
          dashboard.getDisputeMetrics(),
          dashboard.getRecentActivity(),
          billing.getAgencyBilling(),
        ]);
        
        if (s.status === 'fulfilled') {
          setStats({
            total_clients: s.value.total_clients,
            active_disputes: s.value.active_disputes,
            success_rate: Math.round(s.value.success_rate * 100),
            monthly_revenue: s.value.estimated_monthly_revenue,
          });
        }
        
        if (p.status === 'fulfilled') {
          // In a real app, we'd fetch the actual clients. 
          // For now, let's keep the mock cards but update counts if needed.
          setPipeline(mockPipeline);
        }

        if (d.status === 'fulfilled') {
          const metrics = d.value;
          const transformed = [
            { label: 'Resolved', value: (metrics.by_status?.deleted || 0) + (metrics.by_status?.verified || 0), color: '#10b981' },
            { label: 'Pending', value: metrics.by_status?.pending || 0, color: '#f59e0b' },
            { label: 'Mailed', value: metrics.by_status?.mailed || 0, color: '#3b82f6' },
            { label: 'Draft', value: metrics.by_status?.draft || 0, color: '#8b5cf6' },
          ].filter(m => m.value > 0);
          setDisputeMetrics(transformed.length > 0 ? transformed : mockDisputeMetrics);
        }

        if (a.status === 'fulfilled' && a.value) setActivity(a.value);
        if (b.status === 'fulfilled' && b.value) setBillingList(b.value || []);
      } catch (e) {
        console.error('Dashboard data fetch error', e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const totalClients = useCountUp(stats.total_clients);
  const activeDisputes = useCountUp(stats.active_disputes);
  const successRate = useCountUp(stats.success_rate);
  const revenue = useCountUp(stats.monthly_revenue);

  return (
    <div className="dashboard">
      <h1 className="sr-only">Agency Dashboard Overview</h1>
      {/* Stats Cards */}
      <section className="stats-grid stagger-children" aria-label="Quick Stats">
        <div className="stat-card glass-card animate-fade-in-up" style={{ '--accent': 'var(--accent-blue)' }}>
          <div className="stat-icon" aria-hidden="true" style={{ background: 'var(--accent-blue-subtle)' }}>👥</div>
          <div className="stat-content">
            <span className="stat-value">{totalClients}</span>
            <span className="stat-label">Total Clients</span>
          </div>
          <div className="stat-trend stat-trend-up" aria-label="12 percent increase">↗ +12%</div>
        </div>

        <div className="stat-card glass-card animate-fade-in-up" style={{ '--accent': 'var(--accent-purple)' }}>
          <div className="stat-icon" aria-hidden="true" style={{ background: 'var(--accent-purple-subtle)' }}>⚖️</div>
          <div className="stat-content">
            <span className="stat-value">{activeDisputes}</span>
            <span className="stat-label">Active Disputes</span>
          </div>
          <div className="stat-trend stat-trend-up" aria-label="5 new disputes">↗ +5</div>
        </div>

        <div className="stat-card glass-card animate-fade-in-up" style={{ '--accent': 'var(--accent-emerald)' }}>
          <div className="stat-icon" aria-hidden="true" style={{ background: 'var(--accent-emerald-subtle)' }}>📈</div>
          <div className="stat-content">
            <span className="stat-value">{successRate}%</span>
            <span className="stat-label">Success Rate</span>
          </div>
          <div className="stat-trend stat-trend-up" aria-label="3 percent increase">↗ +3%</div>
        </div>

        <div className="stat-card glass-card animate-fade-in-up" style={{ '--accent': 'var(--accent-amber)' }}>
          <div className="stat-icon" aria-hidden="true" style={{ background: 'var(--accent-amber-subtle)' }}>💰</div>
          <div className="stat-content">
            <span className="stat-value">${revenue.toLocaleString()}</span>
            <span className="stat-label">Monthly Revenue</span>
          </div>
          <div className="stat-trend stat-trend-up" aria-label="18 percent increase">↗ +18%</div>
        </div>
      </section>

      {/* Quick Actions */}
      <nav className="quick-actions" aria-label="Quick Actions">
        <Link to="/clients/new" className="btn btn-primary">
          <span aria-hidden="true">+</span> Add Client
        </Link>
        <Link to="/clients" className="btn btn-ghost">
          📋 Upload Report
        </Link>
        <Link to="/disputes" className="btn btn-ghost">
          ⚖️ New Dispute
        </Link>
      </nav>

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Pipeline */}
        <section className="dashboard-section pipeline-section" aria-labelledby="pipeline-title">
          <h2 id="pipeline-title" className="section-title">Client Pipeline</h2>
          <div className="pipeline-columns">
            {pipelineConfig.map((col) => (
              <div key={col.key} className="pipeline-column">
                <div className="pipeline-column-header">
                  <span className="pipeline-column-icon" aria-hidden="true">{col.icon}</span>
                  <span className="pipeline-column-label">{col.label}</span>
                  <span className="pipeline-column-count" style={{ background: col.color + '22', color: col.color }}>
                    {pipeline[col.key]?.length || 0}
                  </span>
                </div>
                <div className="pipeline-cards">
                  {(pipeline[col.key] || []).map((client) => (
                    <Link to={`/clients/${client.id}`} key={client.id} className="pipeline-card glass-card">
                      <div className="pipeline-card-avatar" aria-hidden="true" style={{ background: col.color + '33', color: col.color }}>
                        {client.name?.[0] || '?'}
                      </div>
                      <div className="pipeline-card-info">
                        <span className="pipeline-card-name">{client.name}</span>
                        <span className="pipeline-card-score">Score: {client.score}</span>
                      </div>
                    </Link>
                  ))}
                  {(!pipeline[col.key] || pipeline[col.key].length === 0) && (
                    <div className="pipeline-empty">No clients</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Bottom Row */}
        <div className="dashboard-bottom-grid">
          {/* Dispute Metrics */}
          <section className="glass-card-static dashboard-metrics" aria-labelledby="metrics-title">
            <h2 id="metrics-title" className="section-title">Dispute Metrics</h2>
            <div className="metrics-content">
              <DonutChart data={disputeMetrics} />
              <div className="metrics-legend" role="list">
                {disputeMetrics.map((item, i) => (
                  <div key={i} className="metrics-legend-item" role="listitem">
                    <span className="metrics-legend-dot" aria-hidden="true" style={{ background: item.color }}></span>
                    <span className="metrics-legend-label">{item.label}</span>
                    <span className="metrics-legend-value">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Recent Activity */}
          <section className="glass-card-static dashboard-activity" aria-labelledby="activity-title">
            <h2 id="activity-title" className="section-title">Recent Activity</h2>
            <div className="activity-list" role="log" aria-live="polite">
              {activity.map((item) => (
                <div key={item.id} className="activity-item">
                  <div className="activity-icon" aria-hidden="true">{item.icon}</div>
                  <div className="activity-content">
                    <span className="activity-message">{item.message}</span>
                    <span className="activity-time">{item.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Billing Transactions */}
        <section className="glass-card-static mt-3 p-3 w-full" aria-labelledby="billing-title" style={{ marginTop: '24px' }}>
          <h2 id="billing-title" className="section-title mb-2">Agency Billing & Transaction Logs</h2>
          <p className="page-subtitle mb-3 text-muted">Certified mail dispatch and AI dispute letter generation fees ($5.00/event).</p>
          {billingList.length === 0 ? (
            <p className="text-muted">No billing transactions recorded yet.</p>
          ) : (
            <div className="flex-col gap-1">
              {billingList.slice(0, 10).map((tx) => (
                <div key={tx.id} className="uploaded-doc-row flex justify-between items-center glass-card p-2" style={{ marginBottom: '8px', padding: '12px' }}>
                  <span>
                    💳 <strong>{tx.description}</strong>
                  </span>
                  <div className="flex gap-2 items-center">
                    <span className="text-glow" style={{ fontWeight: 'bold' }}>
                      ${tx.amount.toFixed(2)}
                    </span>
                    <span className={`badge ${tx.status === 'paid' ? 'badge-emerald' : tx.status === 'pending' ? 'badge-amber' : 'badge-red'}`}>
                      {tx.status}
                    </span>
                    <span className="text-muted" style={{ fontSize: '0.8rem' }}>
                      {new Date(tx.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
