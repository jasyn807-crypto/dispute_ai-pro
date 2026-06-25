import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { clients as clientsApi } from '../../services/api';
import './Clients.css';

const mockClients = [
  { id: 1, first_name: 'Sarah', last_name: 'Johnson', email: 'sarah@email.com', phone: '(555) 123-4567', status: 'active', credit_score: 520, disputes_count: 3, created_at: '2026-06-20' },
  { id: 2, first_name: 'Mike', last_name: 'Chen', email: 'mike@email.com', phone: '(555) 234-5678', status: 'lead', credit_score: 490, disputes_count: 0, created_at: '2026-06-21' },
  { id: 3, first_name: 'Emily', last_name: 'Davis', email: 'emily@email.com', phone: '(555) 345-6789', status: 'in_progress', credit_score: 580, disputes_count: 5, created_at: '2026-06-15' },
  { id: 4, first_name: 'James', last_name: 'Wilson', email: 'james@email.com', phone: '(555) 456-7890', status: 'active', credit_score: 545, disputes_count: 2, created_at: '2026-06-18' },
  { id: 5, first_name: 'Lisa', last_name: 'Anderson', email: 'lisa@email.com', phone: '(555) 567-8901', status: 'in_progress', credit_score: 510, disputes_count: 4, created_at: '2026-06-19' },
  { id: 6, first_name: 'Robert', last_name: 'Brown', email: 'robert@email.com', phone: '(555) 678-9012', status: 'completed', credit_score: 720, disputes_count: 6, created_at: '2026-05-10' },
  { id: 7, first_name: 'Amanda', last_name: 'Taylor', email: 'amanda@email.com', phone: '(555) 789-0123', status: 'active', credit_score: 595, disputes_count: 1, created_at: '2026-06-12' },
  { id: 8, first_name: 'David', last_name: 'Martinez', email: 'david@email.com', phone: '(555) 890-1234', status: 'completed', credit_score: 705, disputes_count: 8, created_at: '2026-05-20' },
];

const statusConfig = {
  lead: { label: 'Lead', badge: 'badge-purple' },
  active: { label: 'Active', badge: 'badge-blue' },
  in_progress: { label: 'In Progress', badge: 'badge-amber' },
  completed: { label: 'Completed', badge: 'badge-emerald' },
};

export default function Clients() {
  const [clientList, setClientList] = useState(mockClients);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function fetchClients() {
      setLoading(true);
      try {
        const data = await clientsApi.list();
        if (data && data.length > 0) setClientList(data);
      } catch (e) {
        // fallback to mock
      } finally {
        setLoading(false);
      }
    }
    fetchClients();
  }, []);

  const filtered = clientList.filter((c) => {
    const matchesSearch =
      `${c.first_name} ${c.last_name} ${c.email}`.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getScoreColor = (score) => {
    if (score >= 700) return 'var(--accent-emerald)';
    if (score >= 600) return 'var(--accent-blue)';
    if (score >= 500) return 'var(--accent-amber)';
    return 'var(--accent-red)';
  };

  return (
    <div className="clients-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h2>Client Management</h2>
          <p className="page-subtitle">{filtered.length} clients total</p>
        </div>
        <Link to="/clients/new" className="btn btn-primary">
          <span>+</span> Add Client
        </Link>
      </div>

      {/* Filters */}
      <div className="clients-filters glass-card-static">
        <div className="search-input-wrap">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            className="form-input search-input"
            placeholder="Search clients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="filter-pills">
          {['all', 'lead', 'active', 'in_progress', 'completed'].map((s) => (
            <button
              key={s}
              className={`filter-pill ${statusFilter === s ? 'active' : ''}`}
              onClick={() => setStatusFilter(s)}
            >
              {s === 'all' ? 'All' : statusConfig[s]?.label || s}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="glass-card-static" style={{ overflow: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Client</th>
              <th>Status</th>
              <th>Credit Score</th>
              <th>Disputes</th>
              <th>Phone</th>
              <th>Date Added</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((client) => (
              <tr key={client.id}>
                <td>
                  <div className="client-cell">
                    <div className="client-cell-avatar">
                      {client.first_name[0]}{client.last_name[0]}
                    </div>
                    <div>
                      <div className="client-cell-name">
                        {client.first_name} {client.last_name}
                      </div>
                      <div className="client-cell-email">{client.email}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span className={`badge ${statusConfig[client.status]?.badge || 'badge-gray'}`}>
                    {statusConfig[client.status]?.label || client.status}
                  </span>
                </td>
                <td>
                  <span className="score-display" style={{ color: getScoreColor(client.credit_score) }}>
                    {client.credit_score}
                  </span>
                </td>
                <td>{client.disputes_count}</td>
                <td style={{ color: 'var(--text-muted)' }}>{client.phone}</td>
                <td style={{ color: 'var(--text-muted)' }}>{client.created_at}</td>
                <td>
                  <Link to={`/clients/${client.id}`} className="btn btn-ghost btn-sm">
                    View →
                  </Link>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7}>
                  <div className="empty-state" style={{ padding: '40px' }}>
                    <div className="empty-state-icon">🔍</div>
                    <h3>No clients found</h3>
                    <p>Try adjusting your search or filter</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
