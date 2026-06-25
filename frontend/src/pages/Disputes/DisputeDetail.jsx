import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { disputes, mailing } from '../../services/api';
import './DisputeDetail.css';

export default function DisputeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Actions states
  const [generating, setGenerating] = useState(false);
  const [complianceChecking, setComplianceChecking] = useState(false);
  const [complianceResult, setComplianceResult] = useState(null);
  const [mailingStatus, setMailingStatus] = useState(false);
  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' });

  // USPS / Lob tracking logs
  const [mailLogs, setMailLogs] = useState([]);

  useEffect(() => {
    fetchDetail();
    fetchMailingLogs();
  }, [id]);

  const fetchDetail = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await disputes.get(id);
      setDetail(data);
    } catch (err) {
      setError(err.message || 'Failed to load dispute letter details');
    } finally {
      setLoading(false);
    }
  };

  const fetchMailingLogs = async () => {
    try {
      const logs = await mailing.getLogs();
      const filtered = logs.filter(log => log.dispute_letter_id === parseInt(id, 10));
      setMailLogs(filtered);
    } catch (err) {
      // ignore
    }
  };

  const showStatus = (type, text) => {
    setStatusMsg({ type, text });
    setTimeout(() => setStatusMsg({ type: '', text: '' }), 5000);
  };

  const handleGenerateAI = async () => {
    setGenerating(true);
    showStatus('blue', 'Generating custom dispute letter using AI agent...');
    try {
      const res = await disputes.generateLetter(id);
      setDetail(prev => ({
        ...prev,
        letter: res
      }));
      setComplianceResult(null); // Reset compliance result as content changed
      showStatus('emerald', 'AI dispute letter generated successfully!');
    } catch (err) {
      showStatus('danger', 'Letter generation failed: ' + err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleCheckCompliance = async () => {
    setComplianceChecking(true);
    showStatus('blue', 'Analyzing compliance rules (FCRA / CROA)...');
    try {
      const res = await disputes.checkCompliance(id);
      setComplianceResult(res);
      if (res.passed) {
        showStatus('emerald', 'Compliance analysis passed! Letter is safe to mail.');
      } else {
        showStatus('amber', 'Compliance warnings detected. Check suggestions.');
      }
    } catch (err) {
      showStatus('danger', 'Compliance check failed: ' + err.message);
    } finally {
      setComplianceChecking(false);
    }
  };

  const handleSendMail = async () => {
    setMailingStatus(true);
    showStatus('blue', 'Dispatching via Lob Certified Mail API...');
    try {
      const res = await mailing.dispatch({
        dispute_letter_id: parseInt(id, 10)
      });
      showStatus('emerald', 'Dispute letter dispatched! USPS Tracking active.');
      // Refresh details and logs
      fetchDetail();
      fetchMailingLogs();
    } catch (err) {
      showStatus('danger', 'Mailing dispatch failed: ' + err.message);
    } finally {
      setMailingStatus(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center p-4">
        <div className="spinner spinner-lg" style={{ margin: '0 auto' }}></div>
        <p className="mt-2 text-muted">Loading dispute details...</p>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="glass-card-static p-4 text-center">
        <div className="empty-state">
          <div className="empty-state-icon">⚠️</div>
          <h3>Dispute Letter Not Found</h3>
          <p>{error || 'The requested dispute letter details could not be found.'}</p>
          <button className="btn btn-ghost mt-2" onClick={() => navigate('/disputes')}>
            ← Back to Disputes
          </button>
        </div>
      </div>
    );
  }

  const { letter, items } = detail;

  return (
    <div className="dispute-detail-page">
      <div className="page-header">
        <div>
          <button className="btn btn-ghost btn-sm mb-1" onClick={() => navigate('/disputes')}>
            ← Back to Disputes
          </button>
          <h2>Dispute Letter Detail</h2>
          <p className="page-subtitle">Letter #{letter.id} for {letter.bureau} Bureau</p>
        </div>
        <div className="flex gap-1">
          <span className={`badge badge-lg ${
            letter.status === 'draft' ? 'badge-gray' :
            letter.status === 'mailed' ? 'badge-blue' :
            'badge-emerald'
          }`}>
            Status: {letter.status}
          </span>
        </div>
      </div>

      {statusMsg.text && (
        <div className={`badge badge-${statusMsg.type} animate-fade-in mb-3`} style={{ padding: '12px 20px', width: '100%', borderRadius: '8px' }}>
          {statusMsg.text}
        </div>
      )}

      <div className="detail-layout">
        {/* Left Side: Letter Content and Editor */}
        <div className="letter-content-section flex-col gap-2">
          <div className="glass-card-static p-3 relative">
            <div className="flex justify-between items-center mb-2">
              <h3>Letter Body</h3>
              <div className="flex gap-1">
                <button 
                  className="btn btn-ghost btn-sm"
                  onClick={handleGenerateAI}
                  disabled={generating || letter.status === 'mailed' || letter.status === 'resolved'}
                >
                  {generating ? 'Regenerating...' : '🤖 AI Letter Draft'}
                </button>
              </div>
            </div>

            <textarea 
              className="form-input letter-textarea"
              style={{ minHeight: '400px', fontFamily: 'monospace', fontSize: '0.9rem' }}
              value={letter.letter_content || ''}
              readOnly={true}
              placeholder="Click 'AI Letter Draft' to generate dispute letter content using AI."
            />
          </div>

          {/* Compliance Checklist Panel */}
          {complianceResult && (
            <div className="glass-card-static p-3 compliance-results-panel">
              <h3 className="mb-2">Compliance Scan Results</h3>
              <div className="flex items-center gap-1 mb-2">
                <span className={`compliance-status-indicator ${complianceResult.passed ? 'passed' : 'failed'}`}>
                  {complianceResult.passed ? 'PASS' : 'WARNINGS'}
                </span>
                <span className="info-value">
                  {complianceResult.passed ? 'Letter meets FCRA/CROA requirements.' : 'Compliance rules violated.'}
                </span>
              </div>
              
              {!complianceResult.passed && complianceResult.flags && complianceResult.flags.length > 0 && (
                <div className="compliance-flags mt-1">
                  <strong>Violations Detected:</strong>
                  <ul>
                    {complianceResult.flags.map((flag, idx) => (
                      <li key={idx} className="text-glow-red">• {flag}</li>
                    ))}
                  </ul>
                </div>
              )}

              {complianceResult.suggestions && (
                <div className="compliance-suggestions mt-2">
                  <strong>Recommendations:</strong>
                  <p className="text-secondary mt-1">{complianceResult.suggestions}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Side: Linked Items and Shipping/Lob status */}
        <div className="metadata-section flex-col gap-2">
          {/* Action buttons */}
          <div className="glass-card-static p-3 flex-col gap-1">
            <h3>Dispute Manager</h3>
            <p className="page-subtitle mb-2">Generate letter, check legal compliance, and send via USPS</p>
            
            <button 
              className="btn btn-outline w-full mb-1" 
              onClick={handleCheckCompliance}
              disabled={complianceChecking || !letter.letter_content}
            >
              {complianceChecking ? 'Checking Compliance...' : '🔍 Check Compliance'}
            </button>
            
            <button 
              className="btn btn-success w-full"
              onClick={handleSendMail}
              disabled={mailingStatus || !letter.letter_content || letter.status === 'mailed' || letter.status === 'resolved'}
            >
              {mailingStatus ? 'Dispatching Certified...' : '📬 Send Certified Mail'}
            </button>
          </div>

          {/* Linked Dispute Items */}
          <div className="glass-card-static p-3">
            <h3 className="mb-2">Disputed Items ({items?.length || 0})</h3>
            <div className="disputed-items-list flex-col gap-2">
              {items && items.map(item => (
                <div key={item.id} className="disputed-item-item">
                  <div className="flex justify-between">
                    <strong>{item.creditor_name}</strong>
                    <span className="text-glow">${item.balance}</span>
                  </div>
                  <div className="item-detail-row mt-1 text-muted flex justify-between" style={{ fontSize: '0.75rem' }}>
                    <span>Account: {item.account_number || 'N/A'}</span>
                    <span>Type: {item.negative_type}</span>
                  </div>
                  <div className="item-reason-row mt-1 text-secondary" style={{ fontSize: '0.8rem', fontStyle: 'italic' }}>
                    Reason: {item.dispute_reason}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Lob/USPS Dispatch Log */}
          <div className="glass-card-static p-3">
            <h3 className="mb-2">Certified Mail Log</h3>
            {mailLogs.length === 0 ? (
              <div className="empty-state" style={{ padding: '12px' }}>
                <p>Not mailed yet.</p>
              </div>
            ) : (
              <div className="mail-logs flex-col gap-2">
                {mailLogs.map(log => (
                  <div key={log.id} className="mail-log-item">
                    <div className="flex justify-between items-center">
                      <span className="badge badge-blue">{log.status}</span>
                      <span className="log-date">{new Date(log.dispatched_at).toLocaleDateString()}</span>
                    </div>
                    <div className="mt-1" style={{ fontSize: '0.8rem' }}>
                      <strong>USPS tracking:</strong> <code className="tracking-code">{log.tracking_number}</code>
                    </div>
                    <div className="mt-1 text-muted" style={{ fontSize: '0.75rem' }}>
                      <div>Recipient: {log.recipient_name}</div>
                      <div>Address: {log.recipient_address}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
