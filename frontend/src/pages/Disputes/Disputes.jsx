import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { disputes } from '../../services/api';
import './Disputes.css';

const statusConfig = {
  draft: { label: 'Draft', badge: 'badge-gray' },
  mailed: { label: 'Mailed', badge: 'badge-blue' },
  resolved: { label: 'Resolved', badge: 'badge-emerald' },
  accepted: { label: 'Accepted', badge: 'badge-emerald' },
  rejected: { label: 'Rejected', badge: 'badge-red' },
  pending: { label: 'Pending', badge: 'badge-amber' },
};

export default function Disputes() {
  const [disputesList, setDisputesList] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDisputes();
  }, [statusFilter]);

  const fetchDisputes = async () => {
    setLoading(true);
    setError('');
    try {
      const params = statusFilter !== 'all' ? `dispute_status=${statusFilter}` : '';
      const data = await disputes.list(params);
      setDisputesList(data || []);
    } catch (err) {
      setError(err.message || 'Failed to load disputes');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="disputes-page">
      <div className="page-header">
        <div>
          <h2>Dispute Letters</h2>
          <p className="page-subtitle">Manage AI-generated letters sent to credit bureaus</p>
        </div>
        <Link to="/reports" className="btn btn-primary">
          <span>+</span> Create Dispute
        </Link>
      </div>

      {error && (
        <div className="badge badge-red mb-3" style={{ padding: '12px', width: '100%' }}>
          {error}
        </div>
      )}

      {/* Filter pills */}
      <div className="disputes-filters glass-card-static mb-3">
        <span className="filter-label">Filter Status:</span>
        <div className="filter-pills">
          {['all', 'draft', 'mailed', 'accepted', 'rejected'].map(status => (
            <button
              key={status}
              className={`filter-pill ${statusFilter === status ? 'active' : ''}`}
              onClick={() => setStatusFilter(status)}
            >
              {status === 'all' ? 'All' : statusConfig[status]?.label || status}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center p-4">
          <div className="spinner spinner-lg" style={{ margin: '0 auto' }}></div>
          <p className="mt-2 text-muted">Loading disputes...</p>
        </div>
      ) : disputesList.length === 0 ? (
        <div className="glass-card-static p-4 text-center">
          <div className="empty-state">
            <div className="empty-state-icon">⚖️</div>
            <h3>No disputes found</h3>
            <p>Initiate a dispute from a credit report to generate and mail letters.</p>
          </div>
        </div>
      ) : (
        <div className="disputes-grid stagger-children">
          {disputesList.map(disp => (
            <div key={disp.id} className="glass-card dispute-card flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="dispute-letter-id">Letter #{disp.id}</span>
                  <span className={`badge ${statusConfig[disp.status]?.badge || 'badge-gray'}`}>
                    {statusConfig[disp.status]?.label || disp.status}
                  </span>
                </div>
                <h3 className="dispute-bureau text-glow mb-1">{disp.bureau}</h3>
                <p className="dispute-preview truncate">
                  {disp.letter_content ? disp.letter_content.substring(0, 120) + '...' : 'No content generated yet.'}
                </p>
                {disp.mail_tracking_id && (
                  <div className="dispute-tracking mt-2">
                    <span className="info-label">USPS Tracking:</span>
                    <code className="tracking-code">{disp.mail_tracking_id}</code>
                  </div>
                )}
              </div>

              <div className="flex justify-between items-center mt-3 border-top-glass pt-2">
                <span className="dispute-date">
                  Created: {new Date(disp.created_at).toLocaleDateString()}
                </span>
                <Link to={`/disputes/${disp.id}`} className="btn btn-ghost btn-sm">
                  View Detail →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
