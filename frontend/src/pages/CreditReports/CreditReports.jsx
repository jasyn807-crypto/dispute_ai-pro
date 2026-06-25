import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { clients as clientsApi, creditReports, disputes } from '../../services/api';
import './CreditReports.css';

export default function CreditReports() {
  const { user, isAgency } = useAuth();
  const [clientList, setClientList] = useState([]);
  const [selectedClientId, setSelectedClientId] = useState('');
  const [reportsList, setReportsList] = useState([]);
  const [selectedReportId, setSelectedReportId] = useState('');
  const [negativeItems, setNegativeItems] = useState([]);
  
  // States for actions
  const [uploading, setUploading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [creatingDispute, setCreatingDispute] = useState(null); // stores item ID being disputed
  const [disputeReason, setDisputeReason] = useState('Not mine. Please verify.');
  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' });

  // Load clients if user is agency
  useEffect(() => {
    if (isAgency) {
      clientsApi.list()
        .then(data => {
          setClientList(data || []);
          if (data && data.length > 0) {
            setSelectedClientId(data[0].id);
          }
        })
        .catch(err => showStatus('danger', 'Failed to load clients: ' + err.message));
    } else {
      // If client, we need to get their client profile ID.
      // From AuthContext, we have user.client_profile or user.client
      const cId = user?.client_profile?.id || user?.client?.id;
      if (cId) {
        setSelectedClientId(cId);
      }
    }
  }, [isAgency, user]);

  // Load reports when client is selected
  useEffect(() => {
    if (selectedClientId) {
      loadReports(selectedClientId);
      setSelectedReportId('');
      setNegativeItems([]);
    }
  }, [selectedClientId]);

  // Load negative items when report is selected
  useEffect(() => {
    if (selectedReportId) {
      setParsing(true);
      creditReports.getItems(selectedReportId)
        .then(items => {
          setNegativeItems(items || []);
        })
        .catch(err => showStatus('danger', 'Failed to load negative items: ' + err.message))
        .finally(() => setParsing(false));
    } else {
      setNegativeItems([]);
    }
  }, [selectedReportId]);

  const loadReports = (cId) => {
    creditReports.getByClient(cId)
      .then(data => setReportsList(data || []))
      .catch(err => showStatus('danger', 'Failed to load reports: ' + err.message));
  };

  const showStatus = (type, text) => {
    setStatusMsg({ type, text });
    setTimeout(() => setStatusMsg({ type: '', text: '' }), 5000);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !selectedClientId) return;

    const formData = new FormData();
    formData.append('report', file);
    formData.append('client_id', selectedClientId);

    setUploading(true);
    showStatus('blue', 'Uploading and parsing credit report...');
    
    try {
      const res = await creditReports.upload(formData);
      showStatus('emerald', 'Report uploaded successfully!');
      loadReports(selectedClientId);
      if (res && res.report_id) {
        setSelectedReportId(res.report_id);
      }
    } catch (err) {
      showStatus('danger', 'Upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleCreateDispute = async (itemId) => {
    try {
      setCreatingDispute(itemId);
      const res = await disputes.create({
        client_id: parseInt(selectedClientId, 10),
        dispute_item_id: parseInt(itemId, 10),
        dispute_reason: disputeReason
      });
      showStatus('emerald', 'Dispute created successfully! Letter ID: ' + res.id);
      
      // Update item status in local list
      setNegativeItems(prev => prev.map(item => 
        item.id === itemId ? { ...item, status: 'disputed' } : item
      ));
      setCreatingDispute(null);
    } catch (err) {
      showStatus('danger', 'Failed to create dispute: ' + err.message);
      setCreatingDispute(null);
    }
  };

  // Group items by category helper
  const getCategoryLabel = (statusStr) => {
    const s = (statusStr || '').toLowerCase();
    if (s.includes('late') || s.includes('payment')) return 'Late Payments';
    if (s.includes('collect') || s.includes('collection')) return 'Collections';
    if (s.includes('bankrupt') || s.includes('bankruptcy')) return 'Bankruptcies';
    if (s.includes('inquir') || s.includes('inquiry')) return 'Inquiries';
    if (s.includes('charge') || s.includes('off')) return 'Charge-offs';
    return 'Other Negatives';
  };

  const getCategoryClass = (statusStr) => {
    const s = (statusStr || '').toLowerCase();
    if (s.includes('late') || s.includes('payment')) return 'cat-amber';
    if (s.includes('collect') || s.includes('collection')) return 'cat-purple';
    if (s.includes('bankrupt') || s.includes('bankruptcy')) return 'cat-red';
    if (s.includes('inquir') || s.includes('inquiry')) return 'cat-blue';
    if (s.includes('charge') || s.includes('off')) return 'cat-emerald';
    return 'cat-gray';
  };

  return (
    <div className="credit-reports-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h2>Credit Reports & Parser</h2>
          <p className="page-subtitle">Upload and extract negative items from credit bureau reports</p>
        </div>
      </div>

      {statusMsg.text && (
        <div className={`badge badge-${statusMsg.type} animate-fade-in mb-3`} style={{ padding: '12px 20px', width: '100%', borderRadius: '8px' }}>
          {statusMsg.text}
        </div>
      )}

      {/* Select Client (Agency only) */}
      {isAgency && (
        <div className="glass-card-static p-3 mb-3">
          <label className="form-label">Select Client for Report Management</label>
          <select 
            className="form-select"
            value={selectedClientId} 
            onChange={(e) => setSelectedClientId(e.target.value)}
          >
            <option value="" disabled>-- Select a Client --</option>
            {clientList.map(c => (
              <option key={c.id} value={c.id}>{c.first_name} {c.last_name} ({c.email})</option>
            ))}
          </select>
        </div>
      )}

      <div className="credit-reports-grid">
        {/* Left Side: Upload & Report list */}
        <div className="reports-sidebar-section flex-col gap-2">
          {/* Upload Zone */}
          <div className="glass-card p-3 text-center relative overflow-hidden">
            <div className="upload-glow"></div>
            <div className="upload-zone-icon">📥</div>
            <h3 className="mt-1">Upload New Report</h3>
            <p className="page-subtitle mb-2">Drag & drop or select PDF/Text credit reports</p>
            <label className="btn btn-primary btn-sm w-full" style={{ cursor: 'pointer' }}>
              {uploading ? 'Processing...' : 'Browse Files'}
              <input 
                type="file" 
                onChange={handleFileUpload} 
                disabled={uploading || !selectedClientId} 
                style={{ display: 'none' }} 
              />
            </label>
          </div>

          {/* Reports list */}
          <div className="glass-card-static p-3">
            <h3 className="mb-2">Parsed Reports</h3>
            {reportsList.length === 0 ? (
              <div className="empty-state" style={{ padding: '20px' }}>
                <p>No reports uploaded yet.</p>
              </div>
            ) : (
              <div className="reports-list">
                {reportsList.map(rep => (
                  <button 
                    key={rep.report_id} 
                    className={`report-item-btn ${selectedReportId === rep.report_id ? 'active' : ''}`}
                    onClick={() => setSelectedReportId(rep.report_id)}
                  >
                    <span className="report-item-icon">📋</span>
                    <div className="text-left truncate">
                      <div className="report-item-name">{rep.filename}</div>
                      <div className="report-item-date">{new Date(rep.uploaded_at).toLocaleDateString()}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Parsed Negative Items */}
        <div className="parsed-items-section">
          {selectedReportId ? (
            <div className="glass-card-static p-3">
              <div className="flex justify-between items-center mb-3">
                <h3>Extracted Negative Items</h3>
                <span className="badge badge-gray">{negativeItems.length} Items Found</span>
              </div>

              {parsing ? (
                <div className="text-center p-4">
                  <div className="spinner spinner-lg" style={{ margin: '0 auto' }}></div>
                  <p className="mt-2 text-muted">Parsing credit report details...</p>
                </div>
              ) : negativeItems.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">✅</div>
                  <h3>No negative items found!</h3>
                  <p>This report appears to be clean, or parser could not extract any items.</p>
                </div>
              ) : (
                <div className="negative-items-list flex-col gap-2">
                  {negativeItems.map(item => (
                    <div 
                      key={item.id} 
                      className={`glass-card negative-item-card ${getCategoryClass(item.status)}`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className={`badge category-badge ${getCategoryClass(item.status)}`}>
                            {getCategoryLabel(item.status)}
                          </span>
                          <h4 className="mt-1">{item.creditor}</h4>
                          <div className="item-detail mt-1">
                            <span>Amount: <strong className="text-glow">${item.amount}</strong></span>
                            <span className="mx-2">|</span>
                            <span>Bureau: <strong>{item.bureau}</strong></span>
                            {item.status && (
                              <>
                                <span className="mx-2">|</span>
                                <span>Reported: <strong>{item.status}</strong></span>
                              </>
                            )}
                          </div>
                        </div>

                        <div className="dispute-action-zone">
                          {creatingDispute === item.id ? (
                            <div className="flex-col gap-1 items-end">
                              <input 
                                type="text"
                                className="form-input form-input-sm" 
                                style={{ width: '200px', fontSize: '0.8rem', padding: '6px' }}
                                value={disputeReason} 
                                onChange={(e) => setDisputeReason(e.target.value)} 
                              />
                              <div className="flex gap-1 mt-1">
                                <button 
                                  className="btn btn-success btn-sm"
                                  onClick={() => handleCreateDispute(item.id)}
                                >
                                  Submit
                                </button>
                                <button 
                                  className="btn btn-ghost btn-sm"
                                  onClick={() => setCreatingDispute(null)}
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <button 
                              className="btn btn-primary btn-sm scale-hover"
                              onClick={() => {
                                setCreatingDispute(item.id);
                                setDisputeReason('This account belongs to another person with a similar name.');
                              }}
                            >
                              Create Dispute
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="glass-card-static p-4 text-center">
              <div className="empty-state">
                <div className="empty-state-icon">📋</div>
                <h3>Select a Credit Report</h3>
                <p>Choose an uploaded credit report from the left panel to inspect parsed negative entries and initiate dispute letters.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
