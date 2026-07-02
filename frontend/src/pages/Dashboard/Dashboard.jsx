import { useState, useEffect } from 'react';
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
        <defs>
          <filter id="donut-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
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
              filter="url(#donut-glow)"
              style={{ transition: 'all 0.8s ease', opacity: 0.9 }}
            />
          );
        })}
        <circle cx={size / 2} cy={size / 2} r={radius - 16} fill="transparent" />
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

const getActivityIcon = (iconName) => {
  switch (iconName) {
    case '⚖️':
      return (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="6" cy="18" r="3" /><circle cx="18" cy="18" r="3" /><line x1="6" y1="15" x2="6" y2="9" /><line x1="18" y1="15" x2="18" y2="9" /><line x1="6" y1="9" x2="18" y2="9" /><line x1="12" y1="9" x2="12" y2="3" />
        </svg>
      );
    case '👤':
      return (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
        </svg>
      );
    case '📋':
      return (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      );
    case '✅':
      return (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      );
    case '📬':
      return (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" />
        </svg>
      );
    default:
      return null;
  }
};

const pipelineIcons = {
  lead: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  ),
  active: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  ),
  in_progress: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10" />
      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
  ),
  completed: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  ),
};

const pipelineConfig = [
  { key: 'lead', label: 'New Leads', color: '#8b5cf6' },
  { key: 'active', label: 'Active', color: '#3b82f6' },
  { key: 'in_progress', label: 'In Progress', color: '#f59e0b' },
  { key: 'completed', label: 'Completed', color: '#10b981' },
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
            { label: 'Resolved', value: (metrics?.by_status?.deleted || 0) + (metrics?.by_status?.verified || 0), color: '#10b981' },
            { label: 'Pending', value: metrics?.by_status?.pending || 0, color: '#f59e0b' },
            { label: 'Mailed', value: metrics?.by_status?.mailed || 0, color: '#3b82f6' },
            { label: 'Draft', value: metrics?.by_status?.draft || 0, color: '#8b5cf6' },
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
          <div className="stat-icon" aria-hidden="true" style={{ background: 'var(--accent-blue-subtle)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <div className="stat-content">
            <span className="stat-value">{totalClients}</span>
            <span className="stat-label">Total Clients</span>
          </div>
          <div className="stat-trend stat-trend-up" aria-label="12 percent increase">↗ +12%</div>
        </div>

        <div className="stat-card glass-card animate-fade-in-up" style={{ '--accent': 'var(--accent-purple)' }}>
          <div className="stat-icon" aria-hidden="true" style={{ background: 'var(--accent-purple-subtle)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent-purple)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="18" r="3" />
              <line x1="6" y1="15" x2="6" y2="9" />
              <line x1="18" y1="15" x2="18" y2="9" />
              <line x1="6" y1="9" x2="18" y2="9" />
              <line x1="12" y1="9" x2="12" y2="3" />
            </svg>
          </div>
          <div className="stat-content">
            <span className="stat-value">{activeDisputes}</span>
            <span className="stat-label">Active Disputes</span>
          </div>
          <div className="stat-trend stat-trend-up" aria-label="5 new disputes">↗ +5</div>
        </div>

        <div className="stat-card glass-card animate-fade-in-up" style={{ '--accent': 'var(--accent-emerald)' }}>
          <div className="stat-icon" aria-hidden="true" style={{ background: 'var(--accent-emerald-subtle)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent-emerald)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
              <polyline points="16 7 22 7 22 13" />
            </svg>
          </div>
          <div className="stat-content">
            <span className="stat-value">{successRate}%</span>
            <span className="stat-label">Success Rate</span>
          </div>
          <div className="stat-trend stat-trend-up" aria-label="3 percent increase">↗ +3%</div>
        </div>

        <div className="stat-card glass-card animate-fade-in-up" style={{ '--accent': 'var(--accent-amber)' }}>
          <div className="stat-icon" aria-hidden="true" style={{ background: 'var(--accent-amber-subtle)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--accent-amber)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="1" x2="12" y2="23" />
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
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
          <span aria-hidden="true" style={{ marginRight: '4px' }}>+</span> Add Client
        </Link>
        <Link to="/clients" className="btn btn-ghost" style={{ display: 'inline-flex', alignItems: 'center' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '8px' }}>
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          Upload Report
        </Link>
        <Link to="/disputes" className="btn btn-ghost" style={{ display: 'inline-flex', alignItems: 'center' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '8px' }}>
            <circle cx="6" cy="18" r="3" />
            <circle cx="18" cy="18" r="3" />
            <line x1="6" y1="15" x2="6" y2="9" />
            <line x1="18" y1="15" x2="18" y2="9" />
            <line x1="6" y1="9" x2="18" y2="9" />
            <line x1="12" y1="9" x2="12" y2="3" />
          </svg>
          New Dispute
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
                  <span className="pipeline-column-icon" aria-hidden="true" style={{ display: 'inline-flex', alignItems: 'center', color: col.color }}>{pipelineIcons[col.key]}</span>
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
                  <div className="activity-icon" aria-hidden="true" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
                    {getActivityIcon(item.icon)}
                  </div>
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
            <div className="transaction-table-wrapper">
              <table className="transaction-table">
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'right' }}>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {billingList.slice(0, 10).map((tx) => (
                    <tr key={tx.id} className="transaction-row">
                      <td>
                        <span className="transaction-desc">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--accent-blue)', display: 'inline-block', verticalAlign: 'middle', marginRight: '8px' }}>
                            <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
                            <line x1="1" y1="10" x2="23" y2="10" />
                          </svg>
                          {tx.description}
                        </span>
                      </td>
                      <td>
                        <span className="transaction-date">
                          {new Date(tx.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${tx.status === 'paid' ? 'badge-emerald' : tx.status === 'pending' ? 'badge-amber' : 'badge-red'}`}>
                          {tx.status}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <span className="transaction-amount">
                          ${(tx.amount || 0).toFixed(2)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
