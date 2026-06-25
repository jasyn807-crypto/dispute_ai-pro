import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { clients as clientsApi, creditReports, disputes as disputesApi } from '../../services/api';
import './ClientDetail.css';

const mockClient = {
  id: 1,
  first_name: 'Emily',
  last_name: 'Davis',
  email: 'emily@email.com',
  phone: '(555) 345-6789',
  address: '123 Main St, Springfield, IL 62701',
  ssn_last4: '4567',
  dob: '1990-05-15',
  status: 'in_progress',
  credit_score: 580,
  score_change: +35,
  created_at: '2026-06-15',
};

const mockReports = [
  { id: 1, bureau: 'Equifax', uploaded_at: '2026-06-15', items_count: 12, negative_count: 5, status: 'parsed' },
  { id: 2, bureau: 'TransUnion', uploaded_at: '2026-06-16', items_count: 10, negative_count: 3, status: 'parsed' },
  { id: 3, bureau: 'Experian', uploaded_at: '2026-06-17', items_count: 11, negative_count: 4, status: 'pending' },
];

const mockDisputes = [
  { id: 1, creditor: 'Capital One', type: 'Late Payment', bureau: 'Equifax', status: 'sent', created_at: '2026-06-18' },
  { id: 2, creditor: 'Chase Bank', type: 'Collection', bureau: 'TransUnion', status: 'pending', created_at: '2026-06-19' },
  { id: 3, creditor: 'Medical Collections LLC', type: 'Medical Debt', bureau: 'Equifax', status: 'resolved', created_at: '2026-06-10' },
];

const mockTimeline = [
  { id: 1, type: 'dispute', message: 'Dispute sent to Equifax for Capital One late payment', date: '2026-06-18', icon: '⚖️' },
  { id: 2, type: 'report', message: 'Credit report uploaded from Experian', date: '2026-06-17', icon: '📋' },
  { id: 3, type: 'report', message: 'Credit report uploaded from TransUnion', date: '2026-06-16', icon: '📋' },
  { id: 4, type: 'client', message: 'Client onboarded and profile created', date: '2026-06-15', icon: '👤' },
];

const statusBadges = {
  pending: 'badge-amber',
  sent: 'badge-blue',
  resolved: 'badge-emerald',
  rejected: 'badge-red',
  parsed: 'badge-emerald',
  in_progress: 'badge-amber',
  active: 'badge-blue',
  completed: 'badge-emerald',
  lead: 'badge-purple',
};

export default function ClientDetail() {
  const { id } = useParams();
  const [client, setClient] = useState(mockClient);
  const [reports, setReports] = useState(mockReports);
  const [clientDisputes, setClientDisputes] = useState(mockDisputes);
  const [timeline, setTimeline] = useState(mockTimeline);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    async function fetchData() {
      try {
        const [c, r, d, t] = await Promise.allSettled([
          clientsApi.get(id),
          creditReports.getByClient(id),
          disputesApi.list(`client_id=${id}`),
          clientsApi.getTimeline(id),
        ]);
        if (c.status === 'fulfilled') setClient(c.value);
        if (r.status === 'fulfilled') setReports(r.value);
        if (d.status === 'fulfilled') setClientDisputes(d.value);
        if (t.status === 'fulfilled') setTimeline(t.value);
      } catch (e) {}
    }
    fetchData();
  }, [id]);

  const getScoreColor = (score) => {
    if (score >= 700) return 'var(--accent-emerald)';
    if (score >= 600) return 'var(--accent-blue)';
    if (score >= 500) return 'var(--accent-amber)';
    return 'var(--accent-red)';
  };

  const tabs = [
    { key: 'overview', label: 'Overview', icon: '📋' },
    { key: 'reports', label: 'Credit Reports', icon: '📊' },
    { key: 'disputes', label: 'Disputes', icon: '⚖️' },
    { key: 'timeline', label: 'Timeline', icon: '🕐' },
  ];

  return (
    <div className="client-detail">
      {/* Back */}
      <Link to="/clients" className="back-link">← Back to Clients</Link>

      {/* Client Header */}
      <div className="client-header glass-card-static">
        <div className="client-header-left">
          <div className="client-header-avatar">
            {client.first_name[0]}{client.last_name[0]}
          </div>
          <div className="client-header-info">
            <h2>{client.first_name} {client.last_name}</h2>
            <p>{client.email} · {client.phone}</p>
            <span className={`badge ${statusBadges[client.status] || 'badge-gray'}`}>
              {client.status?.replace('_', ' ')}
            </span>
          </div>
        </div>
        <div className="client-header-score">
          <div className="client-score-number" style={{ color: getScoreColor(client.credit_score) }}>
            {client.credit_score}
          </div>
          <div className="client-score-label">Credit Score</div>
          {client.score_change > 0 && (
            <div className="client-score-change" style={{ color: 'var(--accent-emerald)' }}>
              ↗ +{client.score_change} pts
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="detail-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`detail-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            <span>{tab.icon}</span> {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="detail-content animate-fade-in" key={activeTab}>
        {activeTab === 'overview' && (
          <div className="overview-grid">
            <div className="glass-card-static p-3">
              <h4 className="mb-2">Personal Information</h4>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">Full Name</span>
                  <span className="info-value">{client.first_name} {client.last_name}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Email</span>
                  <span className="info-value">{client.email}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Phone</span>
                  <span className="info-value">{client.phone}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Address</span>
                  <span className="info-value">{client.address}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">SSN (Last 4)</span>
                  <span className="info-value">···· {client.ssn_last4}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Date of Birth</span>
                  <span className="info-value">{client.dob}</span>
                </div>
              </div>
            </div>
            <div className="glass-card-static p-3">
              <h4 className="mb-2">Quick Stats</h4>
              <div className="quick-stats">
                <div className="quick-stat">
                  <span className="quick-stat-value">{reports.length}</span>
                  <span className="quick-stat-label">Reports</span>
                </div>
                <div className="quick-stat">
                  <span className="quick-stat-value">{clientDisputes.length}</span>
                  <span className="quick-stat-label">Disputes</span>
                </div>
                <div className="quick-stat">
                  <span className="quick-stat-value" style={{ color: 'var(--accent-emerald)' }}>
                    {clientDisputes.filter(d => d.status === 'resolved').length}
                  </span>
                  <span className="quick-stat-label">Resolved</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'reports' && (
          <div>
            <div className="flex justify-between items-center mb-2">
              <h4>Credit Reports</h4>
              <Link to={`/clients/${id}/reports`} className="btn btn-primary btn-sm">Upload Report</Link>
            </div>
            <div className="reports-grid">
              {reports.map((report) => (
                <div key={report.id} className="glass-card report-card">
                  <div className="report-card-header">
                    <span className="report-bureau">{report.bureau}</span>
                    <span className={`badge ${statusBadges[report.status]}`}>{report.status}</span>
                  </div>
                  <div className="report-card-stats">
                    <div><strong>{report.items_count}</strong> <span>Items</span></div>
                    <div><strong style={{ color: 'var(--accent-red)' }}>{report.negative_count}</strong> <span>Negative</span></div>
                  </div>
                  <div className="report-card-date">Uploaded: {report.uploaded_at}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'disputes' && (
          <div style={{ overflow: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Creditor</th>
                  <th>Type</th>
                  <th>Bureau</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {clientDisputes.map((d) => (
                  <tr key={d.id}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{d.creditor}</td>
                    <td>{d.type}</td>
                    <td>{d.bureau}</td>
                    <td><span className={`badge ${statusBadges[d.status]}`}>{d.status}</span></td>
                    <td style={{ color: 'var(--text-muted)' }}>{d.created_at}</td>
                    <td><Link to={`/disputes/${d.id}`} className="btn btn-ghost btn-sm">View →</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="timeline">
            {timeline.map((item) => (
              <div key={item.id} className="timeline-item">
                <div className="timeline-dot">{item.icon}</div>
                <div className="timeline-content">
                  <span className="timeline-message">{item.message}</span>
                  <span className="timeline-date">{item.date}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
