import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { dashboard, billing } from '../../services/api';
import './Dashboard.css';

// Animated counter hook
function useCountUp(target, duration = 1200) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);

  useEffect(() => {
    if (target === null || target === undefined) return;
    let start = 0;
    const end = parseInt(target, 10);
    if (isNaN(end)) { setCount(target); return; }
    const step = Math.max(1, Math.floor(end / (duration / 16)));
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
        Total
      </text>
    </svg>
  );
}

// Mock data for demo
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
        if (s.status === 'fulfilled') setStats(s.value);
        if (p.status === 'fulfilled') setPipeline(p.value);
        if (d.status === 'fulfilled') setDisputeMetrics(d.value);
        if (a.status === 'fulfilled') setActivity(a.value);
        if (b.status === 'fulfilled') setBillingList(b.value || []);
      } catch (e) {
        // Fall back to mock data
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
      {/* Stats Cards */}
      <div className="stats-grid stagger-children">
        <div className="stat-card glass-card animate-fade-in-up" style={{ '--accent': 'var(--accent-blue)' }}>
          <div className="stat-icon" style={{ background: 'var(--accent-blue-subtle)' }}>👥</div>
          <div className="stat-content">
            <span className="stat-value">{totalClients}</span>
            <span className="stat-label">Total Clients</span>
          </div>
          <div className="stat-trend stat-trend-up">↗ +12%</div>
        </div>

        <div className="stat-card glass-card animate-fade-in-up" style={{ '--accent': 'var(--accent-purple)' }}>
          <div className="stat-icon" style={{ background: 'var(--accent-purple-subtle)' }}>⚖️</div>
          <div className="stat-content">
            <span className="stat-value">{activeDisputes}</span>
            <span className="stat-label">Active Disputes</span>
          </div>
          <div className="stat-trend stat-trend-up">↗ +5</div>
        </div>

        <div className="stat-card glass-card animate-fade-in-up" style={{ '--accent': 'var(--accent-emerald)' }}>
          <div className="stat-icon" style={{ background: 'var(--accent-emerald-subtle)' }}>📈</div>
          <div className="stat-content">
            <span className="stat-value">{successRate}%</span>
            <span className="stat-label">Success Rate</span>
          </div>
          <div className="stat-trend stat-trend-up">↗ +3%</div>
        </div>

        <div className="stat-card glass-card animate-fade-in-up" style={{ '--accent': 'var(--accent-amber)' }}>
          <div className="stat-icon" style={{ background: 'var(--accent-amber-subtle)' }}>💰</div>
          <div className="stat-content">
            <span className="stat-value">${revenue.toLocaleString()}</span>
            <span className="stat-label">Monthly Revenue</span>
          </div>
          <div className="stat-trend stat-trend-up">↗ +18%</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <Link to="/clients/new" className="btn btn-primary">
          <span>+</span> Add Client
        </Link>
        <Link to="/clients" className="btn btn-ghost">
          📋 Upload Report
        </Link>
        <Link to="/disputes" className="btn btn-ghost">
          ⚖️ New Dispute
        </Link>
      </div>

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Pipeline */}
        <div className="dashboard-section pipeline-section">
          <h3 className="section-title">Client Pipeline</h3>
          <div className="pipeline-columns">
            {pipelineConfig.map((col) => (
              <div key={col.key} className="pipeline-column">
                <div className="pipeline-column-header">
                  <span className="pipeline-column-icon">{col.icon}</span>
                  <span className="pipeline-column-label">{col.label}</span>
                  <span className="pipeline-column-count" style={{ background: col.color + '22', color: col.color }}>
                    {pipeline[col.key]?.length || 0}
                  </span>
                </div>
                <div className="pipeline-cards">
                  {(pipeline[col.key] || []).map((client) => (
                    <Link to={`/clients/${client.id}`} key={client.id} className="pipeline-card glass-card">
                      <div className="pipeline-card-avatar" style={{ background: col.color + '33', color: col.color }}>
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
        </div>

        {/* Bottom Row */}
        <div className="dashboard-bottom-grid">
          {/* Dispute Metrics */}
          <div className="glass-card-static dashboard-metrics">
            <h3 className="section-title">Dispute Metrics</h3>
            <div className="metrics-content">
              <DonutChart data={disputeMetrics} />
              <div className="metrics-legend">
                {disputeMetrics.map((item, i) => (
                  <div key={i} className="metrics-legend-item">
                    <span className="metrics-legend-dot" style={{ background: item.color }}></span>
                    <span className="metrics-legend-label">{item.label}</span>
                    <span className="metrics-legend-value">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="glass-card-static dashboard-activity">
            <h3 className="section-title">Recent Activity</h3>
            <div className="activity-list">
              {activity.map((item) => (
                <div key={item.id} className="activity-item">
                  <div className="activity-icon">{item.icon}</div>
                  <div className="activity-content">
                    <span className="activity-message">{item.message}</span>
                    <span className="activity-time">{item.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Billing Transactions */}
        <div className="glass-card-static mt-3 p-3 w-full" style={{ marginTop: '24px' }}>
          <h3 className="section-title mb-2">Agency Billing & Transaction Logs</h3>
          <p className="page-subtitle mb-3">Certified mail dispatch and AI dispute letter generation fees ($5.00/event).</p>
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
        </div>

      </div>
    </div>
  );
}
