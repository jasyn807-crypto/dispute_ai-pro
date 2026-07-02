import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
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
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

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

  // Drag and drop event handlers
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      triggerUpload(file);
    }
  };

  const triggerUpload = async (file) => {
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
      setSelectedFile(null);
      loadDocuments();
      fetchStatus();
    } catch (err) {
      setDocStatusMsg({ type: 'danger', text: 'Upload failed: ' + err.message });
    } finally {
      setUploadingDoc(false);
    }
  };

  // Onboarding agreement states
  const [signing, setSigning] = useState(false);
  const [sigName, setSigName] = useState('');
  const [agreeChecked, setAgreeChecked] = useState(false);
  const [sigError, setSigError] = useState('');

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

  const handleSignAgreement = async () => {
    if (!agreeChecked) {
      setSigError('You must check the box agreeing to the contract terms.');
      return;
    }
    if (!sigName.trim()) {
      setSigError('Please type your full name to sign.');
      return;
    }
    setSigning(true);
    setSigError('');
    try {
      await clientApi.signAgreement();
      fetchStatus();
    } catch (err) {
      setSigError(err.message || 'Failed to sign agreement');
    } finally {
      setSigning(false);
    }
  };

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

  const handleDocUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      triggerUpload(file);
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
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            <polyline points="9 22 9 12 15 12 15 22" />
          </svg>
          Overview
        </button>
        <button 
          className={`portal-tab-btn ${currentTab === 'reports' ? 'active' : ''}`}
          onClick={() => navigate('/portal/reports')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
          My Reports
        </button>
        <button 
          className={`portal-tab-btn ${currentTab === 'disputes' ? 'active' : ''}`}
          onClick={() => navigate('/portal/disputes')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="6" cy="18" r="3" />
            <circle cx="18" cy="18" r="3" />
            <line x1="6" y1="15" x2="6" y2="9" />
            <line x1="18" y1="15" x2="18" y2="9" />
            <line x1="6" y1="9" x2="18" y2="9" />
            <line x1="12" y1="9" x2="12" y2="3" />
          </svg>
          My Disputes
        </button>
        <button 
          className={`portal-tab-btn ${currentTab === 'documents' ? 'active' : ''}`}
          onClick={() => navigate('/portal/documents')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          </svg>
          Documents
        </button>
        <button 
          className={`portal-tab-btn ${currentTab === 'billing' ? 'active' : ''}`}
          onClick={() => navigate('/portal/billing')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
            <line x1="1" y1="10" x2="23" y2="10" />
          </svg>
          Billing
        </button>
      </div>

      {/* Tab Contents */}
      <div className="portal-tab-content">
        {clientStatus && !clientStatus.signed_agreement ? (
          <div className="glass-card-static p-4 animate-fade-in flex-col gap-2" style={{ maxWidth: '800px', margin: '0 auto' }}>
            <h2 className="text-center" style={{ color: 'var(--accent-blue)' }}>Consumer Agreement & Disclosures</h2>
            <p className="text-muted text-center mb-2">Please read and sign the legal disclosures below to activate your account.</p>
            
            <div className="border-top-glass pt-2 flex-col gap-2" style={{ maxHeight: '350px', overflowY: 'auto', paddingRight: '10px', fontSize: '0.9rem', lineHeight: '1.5' }}>
              <h4>1. Right to Cancel (3-Day Policy)</h4>
              <p>
                <strong>Right to Cancel:</strong> You may cancel this contract without any penalty or obligation at any time before midnight of the 3rd business day after the date on which the contract was signed. To cancel this agreement, submit a written cancellation request to the agency.
              </p>
              
              <h4>2. No Advance Fee Prohibitions (CROA)</h4>
              <p>
                <strong>Advance Fee Restriction:</strong> No fee, deposit, or money can be charged or accepted by the Credit Repair Organization before services are fully performed. You will only be billed after dispute items are fully generated, processed, and dispatched.
              </p>
              
              <h4>3. Consumer Credit File Rights (State & Federal Law)</h4>
              <p>
                You have the right to dispute inaccurate information in your credit report by contacting the credit bureau directly. You are not required to use a credit repair organization to do so. No one can legally remove accurate and timely negative information from a credit report.
              </p>
              <p>
                Under the Fair Credit Reporting Act (FCRA), you have the right to obtain a free copy of your credit report from each bureau annually, and dispute any errors found directly.
              </p>
            </div>

            {sigError && <div className="login-error mt-2">{sigError}</div>}

            <div className="border-top-glass pt-3 mt-2 flex-col gap-1">
              <label className="flex items-center gap-1" style={{ cursor: 'pointer', fontSize: '0.95rem' }}>
                <input 
                  type="checkbox" 
                  checked={agreeChecked} 
                  onChange={(e) => setAgreeChecked(e.target.checked)} 
                />
                I read and agree to the Credit Service Contract, Disclosure Statement, and 3-day cancellation rights.
              </label>

              <div className="form-group mt-2">
                <label className="form-label">Type your Full Name to Sign *</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. John Doe"
                  value={sigName} 
                  onChange={(e) => setSigName(e.target.value)} 
                />
                {sigName && (
                  <div className="signature-preview mt-2" style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'flex-start', padding: '12px 20px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: 'var(--border-radius-md)', border: '1px dashed var(--glass-border)', marginTop: '12px' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '4px' }}>Digital Signature Preview</span>
                    <span style={{ fontFamily: "'Dancing Script', cursive", fontSize: '2rem', color: 'var(--accent-blue)', textShadow: '0 0 10px var(--accent-blue-glow)' }}>{sigName}</span>
                  </div>
                )}
              </div>

              <button 
                className="btn btn-success mt-2" 
                onClick={handleSignAgreement}
                disabled={signing}
              >
                {signing ? 'Signing...' : '✓ Sign & Activate Account'}
              </button>
            </div>
          </div>
        ) : (
          <>

        
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
                          <div 
                            className="chart-bar bar-eq" 
                            style={{ height: `${Math.max(5, Math.min(100, ((pt.Equifax - 300) / 550) * 100))}%` }}
                            title={`Equifax: ${pt.Equifax}`}
                          >
                            <span className="chart-bar-tooltip">Equifax: {pt.Equifax}</span>
                          </div>
                          <div 
                            className="chart-bar bar-ex" 
                            style={{ height: `${Math.max(5, Math.min(100, ((pt.Experian - 300) / 550) * 100))}%` }}
                            title={`Experian: ${pt.Experian}`}
                          >
                            <span className="chart-bar-tooltip">Experian: {pt.Experian}</span>
                          </div>
                          <div 
                            className="chart-bar bar-tu" 
                            style={{ height: `${Math.max(5, Math.min(100, ((pt.TransUnion - 300) / 550) * 100))}%` }}
                            title={`TransUnion: ${pt.TransUnion}`}
                          >
                            <span className="chart-bar-tooltip">TransUnion: {pt.TransUnion}</span>
                          </div>
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
                          style={{ width: `${Math.max(0, Math.min(100, clientStatus?.disputes_summary?.total > 0 ? (clientStatus.disputes_summary.pending / clientStatus.disputes_summary.total) * 100 : 0))}%` }}
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
                          style={{ width: `${Math.max(0, Math.min(100, clientStatus?.disputes_summary?.total > 0 ? (clientStatus.disputes_summary.deleted / clientStatus.disputes_summary.total) * 100 : 0))}%` }}
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
                          style={{ width: `${Math.max(0, Math.min(100, clientStatus?.disputes_summary?.total > 0 ? (clientStatus.disputes_summary.verified / clientStatus.disputes_summary.total) * 100 : 0))}%` }}
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
                <div className="empty-state" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 20px', textAlign: 'center' }}>
                  <div className="empty-state-icon" style={{ fontSize: '3rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                    </svg>
                  </div>
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
                <div className="empty-state" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 20px', textAlign: 'center' }}>
                  <div className="empty-state-icon" style={{ fontSize: '3rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="6" cy="18" r="3" />
                      <circle cx="18" cy="18" r="3" />
                      <line x1="6" y1="15" x2="6" y2="9" />
                      <line x1="18" y1="15" x2="18" y2="9" />
                      <line x1="6" y1="9" x2="18" y2="9" />
                      <line x1="12" y1="9" x2="12" y2="3" />
                    </svg>
                  </div>
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
                <div className="form-group flex-1" style={{ marginBottom: '0' }}>
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
              </div>

              {/* Drag and Drop Zone */}
              <div 
                className={`upload-dropzone ${dragActive ? 'drag-active' : ''}`}
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('file-upload-input').click()}
              >
                <input 
                  id="file-upload-input"
                  type="file" 
                  onChange={handleDocUpload}
                  disabled={uploadingDoc}
                  style={{ display: 'none' }} 
                />
                
                <svg className="upload-dropzone-icon" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                </svg>

                <p className="upload-dropzone-text">
                  {uploadingDoc ? 'Uploading...' : 'Drag & drop your file here, or click to browse'}
                </p>
                <p className="upload-dropzone-subtext">
                  Supports PDF, PNG, JPG up to 10MB
                </p>

                {selectedFile && (
                  <div className="upload-file-info" onClick={(e) => e.stopPropagation()}>
                    <div className="upload-file-info-icon">
                      <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                    </div>
                    <div className="upload-file-info-details">
                      <span className="upload-file-name">{selectedFile.name}</span>
                      <span className="upload-file-size">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Uploaded Documents List */}
              <div className="uploaded-documents mt-3 border-top-glass pt-3">
                <h4>Your Uploaded Files</h4>
                {uploadedDocsList.length === 0 ? (
                  <p className="text-muted mt-1">No documents uploaded yet.</p>
                ) : (
                  <div className="uploaded-docs-list flex-col gap-1 mt-2">
                    {uploadedDocsList.map(doc => (
                      <div key={doc.id} className="uploaded-doc-row flex justify-between items-center glass-card" style={{ padding: '12px 16px', marginBottom: '8px' }}>
                        <span className="doc-name-cell" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--accent-blue)' }}>
                            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                          </svg>
                          <strong>[{doc.document_type}]</strong> {doc.filename}
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
                      {billingList.map((tx) => (
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
            </div>
          </div>
        )}

          </>
        )}
      </div>
    </div>
  );
}

