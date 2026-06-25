import { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { client as clientApi, documents as docsApi, disputes as disputesApi, creditReports, billing } from '../../services/api';
import './ClientPortal.css';

export default function ClientPortal() {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  
  // Determine current tab based on path
  const currentTab = location.pathname.endsWith('/reports') ? 'reports' :
                     location.pathname.endsWith('/disputes') ? 'disputes' :
                     location.pathname.endsWith('/documents') ? 'documents' :
                     location.pathname.endsWith('/billing') ? 'billing' : 'overview';

  const clientId = user?.client_profile?.id || user?.client?.id;

  // Overview states
  const [clientStatus, setClientStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(true);

  // Documents tab states
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [docType, setDocType] = useState('id_proof');
  const [docStatusMsg, setDocStatusMsg] = useState({ type: '', text: '' });
  const [uploadedDocsList, setUploadedDocsList] = useState([]);

  // Billing tab states
  const [billingList, setBillingList] = useState([]);
  const [loadingBilling, setLoadingBilling] = useState(false);

  // Disputes tab states
  const [myDisputesList, setMyDisputesList] = useState([]);
  const [loadingDisputes, setLoadingDisputes] = useState(false);

  // Reports tab states
  const [reportsList, setReportsList] = useState([]);
  const [selectedReportId, setSelectedReportId] = useState('');
  const [negativeItems, setNegativeItems] = useState([]);
  const [loadingItems, setLoadingItems] = useState(false);

  // Fetch client status (overview data + documents)
  useEffect(() => {
    if (clientId) {
      fetchStatus();
    }
  }, [clientId]);

  // Load specific tab data when tab changes
  useEffect(() => {
    if (!clientId) return;
    if (currentTab === 'documents') {
      loadDocuments();
    } else if (currentTab === 'disputes') {
      loadDisputes();
    } else if (currentTab === 'reports') {
      loadReports();
    } else if (currentTab === 'billing') {
      loadBilling();
    }
  }, [currentTab, clientId]);

  const loadBilling = () => {
    setLoadingBilling(true);
    billing.getClientBilling()
      .then(data => setBillingList(data || []))
      .catch(() => {})
      .finally(() => setLoadingBilling(false));
  };

  // Load negative items when client selects a report
  useEffect(() => {
    if (selectedReportId) {
      setLoadingItems(true);
      creditReports.getItems(selectedReportId)
        .then(items => setNegativeItems(items || []))
        .catch(() => {})
        .finally(() => setLoadingItems(false));
    } else {
      setNegativeItems([]);
    }
  }, [selectedReportId]);

  const fetchStatus = () => {
    setLoadingStatus(true);
    clientApi.getStatus()
      .then(data => {
        setClientStatus(data);
        if (data.documents_uploaded) {
          setUploadedDocsList(data.documents_uploaded);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingStatus(false));
  };

  const loadDocuments = () => {
    docsApi.getByClient(clientId)
      .then(data => setUploadedDocsList(data || []))
      .catch(() => {});
  };

  const loadDisputes = () => {
    setLoadingDisputes(true);
    disputesApi.list()
      .then(data => setMyDisputesList(data || []))
      .catch(() => {})
      .finally(() => setLoadingDisputes(false));
  };

  const loadReports = () => {
    creditReports.getByClient(clientId)
      .then(data => setReportsList(data || []))
      .catch(() => {});
  };

  const handleDocUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !clientId) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', docType);
    formData.append('client_id', clientId);

    setUploadingDoc(true);
    setDocStatusMsg({ type: 'blue', text: 'Uploading document...' });

    try {
      await docsApi.upload(formData);
      setDocStatusMsg({ type: 'emerald', text: 'Document uploaded successfully!' });
      loadDocuments();
      fetchStatus();
    } catch (err) {
      setDocStatusMsg({ type: 'danger', text: 'Upload failed: ' + err.message });
    } finally {
      setUploadingDoc(false);
    }
  };

  // Compute mock credit scores dynamically based on client ID
  const equifaxScore = clientId ? 610 + (clientId * 13) % 120 : 650;
  const experianScore = clientId ? 625 + (clientId * 17) % 120 : 660;
  const transunionScore = clientId ? 615 + (clientId * 19) % 120 : 655;

  const scoreTimeline = [
    { month: 'Jan', Equifax: equifaxScore - 30, Experian: experianScore - 25, TransUnion: transunionScore - 20 },
    { month: 'Feb', Equifax: equifaxScore - 20, Experian: experianScore - 15, TransUnion: transunionScore - 10 },
    { month: 'Mar', Equifax: equifaxScore - 15, Experian: experianScore - 10, TransUnion: transunionScore - 5 },
    { month: 'Apr', Equifax: equifaxScore - 5, Experian: experianScore - 5, TransUnion: transunionScore - 2 },
    { month: 'May', Equifax: equifaxScore, Experian: experianScore, TransUnion: transunionScore },
  ];

  return (
    <div className="client-portal-page">
      {/* Welcome Banner */}
      <div className="portal-welcome-banner glass-card p-3 mb-3 relative overflow-hidden">
        <div className="welcome-glow"></div>
        <h2>Welcome back, {user?.name || user?.email}!</h2>
        <p className="page-subtitle">Track your credit repair status and dispute letter progress.</p>
      </div>

      {/* Tabs Menu */}
      <div className="portal-tabs-nav mb-3">
        <button 
          className={`portal-tab-btn ${currentTab === 'overview' ? 'active' : ''}`}
          onClick={() => navigate('/portal')}
        >
          🏠 Overview
        </button>
        <button 
          className={`portal-tab-btn ${currentTab === 'reports' ? 'active' : ''}`}
          onClick={() => navigate('/portal/reports')}
        >
          📋 My Reports
        </button>
        <button 
          className={`portal-tab-btn ${currentTab === 'disputes' ? 'active' : ''}`}
          onClick={() => navigate('/portal/disputes')}
        >
          ⚖️ My Disputes
        </button>
        <button 
          className={`portal-tab-btn ${currentTab === 'documents' ? 'active' : ''}`}
          onClick={() => navigate('/portal/documents')}
        >
          📁 Documents
        </button>
        <button 
          className={`portal-tab-btn ${currentTab === 'billing' ? 'active' : ''}`}
          onClick={() => navigate('/portal/billing')}
        >
          💳 Billing
        </button>
      </div>

      {/* Tab Contents */}
      <div className="portal-tab-content">
        
        {/* Tab 1: Overview */}
        {currentTab === 'overview' && (
          <div className="portal-overview-grid animate-fade-in">
            {/* Credit Scores */}
            <div className="glass-card-static p-3 flex-col gap-2">
              <h3>Current Credit Scores</h3>
              <div className="scores-row mt-1">
                <div className="score-card glass-card text-center" style={{ '--accent': 'var(--accent-blue)' }}>
                  <span className="score-bureau">EQUIFAX</span>
                  <span className="score-num text-glow">{equifaxScore}</span>
                  <span className="badge badge-blue">Good</span>
                </div>
                <div className="score-card glass-card text-center" style={{ '--accent': 'var(--accent-purple)' }}>
                  <span className="score-bureau">EXPERIAN</span>
                  <span className="score-num text-glow">{experianScore}</span>
                  <span className="badge badge-purple">Good</span>
                </div>
                <div className="score-card glass-card text-center" style={{ '--accent': 'var(--accent-emerald)' }}>
                  <span className="score-bureau">TRANSUNION</span>
                  <span className="score-num text-glow">{transunionScore}</span>
                  <span className="badge badge-emerald">Good</span>
                </div>
              </div>

              {/* Timeline chart */}
              <div className="score-chart-container mt-2">
                <h4>Credit Score Progression</h4>
                <div className="score-chart mt-2">
                  {scoreTimeline.map((pt, i) => (
                    <div key={i} className="chart-bar-group">
                      <div className="chart-bars">
                        <div className="chart-bar bar-eq" style={{ height: `${(pt.Equifax - 400) / 4}px` }}></div>
                        <div className="chart-bar bar-ex" style={{ height: `${(pt.Experian - 400) / 4}px` }}></div>
                        <div className="chart-bar bar-tu" style={{ height: `${(pt.TransUnion - 400) / 4}px` }}></div>
                      </div>
                      <span className="chart-label">{pt.month}</span>
                    </div>
                  ))}
                </div>
                <div className="chart-legend flex justify-center gap-2 mt-2">
                  <span className="legend-item"><span className="legend-dot bar-eq"></span> Equifax</span>
                  <span className="legend-item"><span className="legend-dot bar-ex"></span> Experian</span>
                  <span className="legend-item"><span className="legend-dot bar-tu"></span> TransUnion</span>
                </div>
              </div>
            </div>

            {/* Right side: Disputes summary and upload prompt */}
            <div className="flex-col gap-2">
              {/* Disputes Status */}
              <div className="glass-card-static p-3">
                <h3>Active Disputes Summary</h3>
                {loadingStatus ? (
                  <p className="text-muted mt-2">Calculating status...</p>
                ) : (
                  <div className="disputes-status-bars mt-2 flex-col gap-2">
                    <div className="status-progress-group">
                      <div className="flex justify-between mb-1" style={{ fontSize: '0.85rem' }}>
                        <span>Pending Bureau Verification</span>
                        <strong>{clientStatus?.disputes_summary?.pending || 0}</strong>
                      </div>
                      <div className="progress-bar-bg">
                        <div 
                          className="progress-bar-fill bar-eq" 
                          style={{ width: `${clientStatus?.disputes_summary?.total > 0 ? (clientStatus.disputes_summary.pending / clientStatus.disputes_summary.total) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="status-progress-group">
                      <div className="flex justify-between mb-1" style={{ fontSize: '0.85rem' }}>
                        <span>Items Removed (Success)</span>
                        <strong className="text-glow" style={{ color: 'var(--accent-emerald)' }}>
                          {clientStatus?.disputes_summary?.deleted || 0}
                        </strong>
                      </div>
                      <div className="progress-bar-bg">
                        <div 
                          className="progress-bar-fill bar-tu" 
                          style={{ width: `${clientStatus?.disputes_summary?.total > 0 ? (clientStatus.disputes_summary.deleted / clientStatus.disputes_summary.total) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="status-progress-group">
                      <div className="flex justify-between mb-1" style={{ fontSize: '0.85rem' }}>
                        <span>Items Verified (Rejected)</span>
                        <strong>{clientStatus?.disputes_summary?.verified || 0}</strong>
                      </div>
                      <div className="progress-bar-bg">
                        <div 
                          className="progress-bar-fill bar-ex" 
                          style={{ width: `${clientStatus?.disputes_summary?.total > 0 ? (clientStatus.disputes_summary.verified / clientStatus.disputes_summary.total) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Documents Upload Alert */}
              <div className="glass-card p-3 relative overflow-hidden flex-col gap-1">
                <h3>Verification Documents</h3>
                <p className="page-subtitle">Upload identity and address proofs to enable dispatch of dispute letters.</p>
                <div className="flex justify-between items-center mt-2 border-top-glass pt-2">
                  <span style={{ fontSize: '0.85rem' }}>
                    Status: <strong className={clientStatus?.status === 'active' ? 'text-glow' : ''} style={{ color: clientStatus?.status === 'active' ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>{clientStatus?.status || 'onboarding'}</strong>
                  </span>
                  <button className="btn btn-ghost btn-sm" onClick={() => navigate('/portal/documents')}>
                    Upload Files →
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Reports */}
        {currentTab === 'reports' && (
          <div className="portal-reports-tab animate-fade-in flex-col gap-2">
            <div className="glass-card-static p-3">
              <div className="flex justify-between items-center mb-2">
                <h3>My Credit Reports</h3>
                <span className="badge badge-gray">{reportsList.length} Reports</span>
              </div>

              {reportsList.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">📋</div>
                  <h3>No reports uploaded yet</h3>
                  <p>Contact your agency staff to upload and parse your credit bureau files.</p>
                </div>
              ) : (
                <div className="reports-selection-row flex gap-1 flex-wrap mb-3">
                  {reportsList.map(rep => (
                    <button 
                      key={rep.report_id} 
                      className={`report-pill-btn ${selectedReportId === rep.report_id ? 'active' : ''}`}
                      onClick={() => setSelectedReportId(rep.report_id)}
                    >
                      📄 {rep.filename}
                    </button>
                  ))}
                </div>
              )}

              {selectedReportId && (
                <div className="parsed-items-box mt-3 border-top-glass pt-3">
                  <h4>Negative Items Extracted from Selected Report</h4>
                  {loadingItems ? (
                    <div className="text-center p-3">
                      <div className="spinner" style={{ margin: '0 auto' }}></div>
                    </div>
                  ) : negativeItems.length === 0 ? (
                    <p className="text-muted mt-2">No negative items found in this report.</p>
                  ) : (
                    <div className="negative-items-mini-list mt-2 flex-col gap-1">
                      {negativeItems.map(item => (
                        <div key={item.id} className="mini-item-card glass-card">
                          <div className="flex justify-between">
                            <strong>{item.creditor}</strong>
                            <span>${item.amount}</span>
                          </div>
                          <div className="flex justify-between mt-1 text-muted" style={{ fontSize: '0.8rem' }}>
                            <span>Bureau: {item.bureau}</span>
                            <span>Status: {item.status}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Disputes */}
        {currentTab === 'disputes' && (
          <div className="portal-disputes-tab animate-fade-in">
            <div className="glass-card-static p-3">
              <h3>My Dispute Letters</h3>
              {loadingDisputes ? (
                <div className="text-center p-3">
                  <div className="spinner spinner-lg" style={{ margin: '0 auto' }}></div>
                </div>
              ) : myDisputesList.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">⚖️</div>
                  <h3>No disputes initiated</h3>
                  <p>When negative items are disputed on your reports, their progress letters will show up here.</p>
                </div>
              ) : (
                <div className="mini-disputes-grid mt-2">
                  {myDisputesList.map(disp => (
                    <div key={disp.id} className="glass-card mini-dispute-card flex-col justify-between">
                      <div>
                        <div className="flex justify-between">
                          <span className="disp-bureau">{disp.bureau}</span>
                          <span className="badge badge-gray">{disp.status}</span>
                        </div>
                        <p className="disp-preview truncate mt-1">
                          {disp.letter_content ? disp.letter_content.substring(0, 100) + '...' : 'No content.'}
                        </p>
                      </div>
                      <div className="flex justify-between items-center mt-2 border-top-glass pt-1" style={{ fontSize: '0.8rem' }}>
                        <span className="text-muted">{new Date(disp.created_at).toLocaleDateString()}</span>
                        {disp.mail_tracking_id && <code className="tracking-code">{disp.mail_tracking_id.substring(0, 15)}...</code>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 4: Documents */}
        {currentTab === 'documents' && (
          <div className="portal-documents-tab animate-fade-in flex-col gap-2">
            <div className="glass-card-static p-3">
              <h3>Upload Verification Documents</h3>
              <p className="page-subtitle mb-3">Upload your government ID (driver license, passport) and proof of address (utility bill, bank statement) to activate your account.</p>

              {docStatusMsg.text && (
                <div className={`badge badge-${docStatusMsg.type} mb-3`} style={{ padding: '10px 16px', width: '100%', borderRadius: '6px' }}>
                  {docStatusMsg.text}
                </div>
              )}

              <div className="upload-options-row flex gap-2 mb-3">
                <div className="form-group flex-1">
                  <label className="form-label">Document Type</label>
                  <select 
                    className="form-select"
                    value={docType}
                    onChange={(e) => setDocType(e.target.value)}
                  >
                    <option value="id_proof">Government Photo ID</option>
                    <option value="address_proof">Proof of Address</option>
                    <option value="ssn_card">SSN Card Copy</option>
                    <option value="other">Other Document</option>
                  </select>
                </div>

                <div className="form-group flex-col justify-end" style={{ flex: '2' }}>
                  <label className="form-label">Select File</label>
                  <label className="btn btn-primary w-full" style={{ cursor: 'pointer' }}>
                    {uploadingDoc ? 'Uploading...' : '📁 Choose & Upload File'}
                    <input 
                      type="file" 
                      onChange={handleDocUpload}
                      disabled={uploadingDoc}
                      style={{ display: 'none' }} 
                    />
                  </label>
                </div>
              </div>

              {/* Uploaded Documents List */}
              <div className="uploaded-documents mt-3 border-top-glass pt-3">
                <h4>Your Uploaded Files</h4>
                {uploadedDocsList.length === 0 ? (
                  <p className="text-muted mt-1">No documents uploaded yet.</p>
                ) : (
                  <div className="uploaded-docs-list flex-col gap-1 mt-2">
                    {uploadedDocsList.map(doc => (
                      <div key={doc.id} className="uploaded-doc-row flex justify-between items-center glass-card">
                        <span className="doc-name-cell">
                          📁 <strong>[{doc.document_type}]</strong> {doc.filename}
                        </span>
                        <span className="doc-date-cell text-muted" style={{ fontSize: '0.8rem' }}>
                          {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : 'Just now'}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tab 5: Billing */}
        {currentTab === 'billing' && (
          <div className="portal-billing-tab animate-fade-in flex-col gap-2">
            <div className="glass-card-static p-3">
              <h3>My Billing & Invoices</h3>
              <p className="page-subtitle mb-3">View your outstanding charges, payment history, and usage transactions.</p>
              
              {/* Summary Cards */}
              <div className="flex gap-2 mb-3">
                <div className="glass-card flex-1 p-3 text-center">
                  <span className="info-label" style={{ fontSize: '0.8rem' }}>OUTSTANDING BALANCE</span>
                  <div className="score-num text-glow mt-1" style={{ fontSize: '1.8rem', color: 'var(--accent-amber)' }}>
                    ${(billingList.filter(tx => tx.status === 'pending').reduce((sum, tx) => sum + tx.amount, 0)).toFixed(2)}
                  </div>
                </div>
                <div className="glass-card flex-1 p-3 text-center">
                  <span className="info-label" style={{ fontSize: '0.8rem' }}>TOTAL PAID</span>
                  <div className="score-num text-glow mt-1" style={{ fontSize: '1.8rem', color: 'var(--accent-emerald)' }}>
                    ${(billingList.filter(tx => tx.status === 'paid').reduce((sum, tx) => sum + tx.amount, 0)).toFixed(2)}
                  </div>
                </div>
              </div>

              {loadingBilling ? (
                <div className="text-center p-3">
                  <div className="spinner" style={{ margin: '0 auto' }}></div>
                </div>
              ) : billingList.length === 0 ? (
                <p className="text-muted mt-1">No billing transactions found.</p>
              ) : (
                <div className="uploaded-docs-list flex-col gap-1 mt-2">
                  {billingList.map(tx => (
                    <div key={tx.id} className="uploaded-doc-row flex justify-between items-center glass-card">
                      <span className="doc-name-cell">
                        💳 <strong>{tx.description}</strong>
                      </span>
                      <div className="flex gap-2 items-center">
                        <span className="text-glow" style={{ fontWeight: 'bold' }}>
                          ${tx.amount.toFixed(2)}
                        </span>
                        <span className={`badge ${tx.status === 'paid' ? 'badge-emerald' : tx.status === 'pending' ? 'badge-amber' : 'badge-red'}`}>
                          {tx.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
