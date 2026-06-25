import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { clients as clientsApi } from '../../services/api';
import './ClientOnboarding.css';

const steps = ['Personal Info', 'Documents', 'Review'];

export default function ClientOnboarding() {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    zip: '',
    dob: '',
    ssn_last4: '',
  });

  const [documents, setDocuments] = useState([]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    setDocuments([...documents, ...Array.from(e.target.files)]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    const files = Array.from(e.dataTransfer.files);
    setDocuments([...documents, ...files]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
  };

  const handleDragLeave = (e) => {
    e.currentTarget.classList.remove('drag-over');
  };

  const removeDoc = (index) => {
    setDocuments(documents.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    setError('');
    setLoading(true);
    try {
      await clientsApi.create(formData);
      navigate('/clients');
    } catch (err) {
      setError(err.message || 'Failed to create client');
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (step === 0) {
      if (!formData.first_name || !formData.last_name || !formData.email) {
        setError('Please fill in required fields');
        return;
      }
    }
    setError('');
    setStep(step + 1);
  };

  return (
    <div className="onboarding-page">
      <h2>New Client Onboarding</h2>
      <p className="page-subtitle">Add a new client to your pipeline</p>

      {/* Progress */}
      <div className="progress-bar">
        {steps.map((s, i) => (
          <div key={s} className={`progress-step ${i <= step ? 'active' : ''} ${i < step ? 'completed' : ''}`}>
            <div className="progress-step-circle">
              {i < step ? '✓' : i + 1}
            </div>
            <span className="progress-step-label">{s}</span>
            {i < steps.length - 1 && <div className="progress-step-line"></div>}
          </div>
        ))}
      </div>

      {error && (
        <div className="login-error animate-fade-in" style={{ marginBottom: 20 }}>
          {error}
        </div>
      )}

      <div className="glass-card-static onboarding-content animate-fade-in" key={step}>
        {/* Step 1: Personal Info */}
        {step === 0 && (
          <div>
            <h3 className="mb-2">Personal Information</h3>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">First Name *</label>
                <input type="text" name="first_name" className="form-input" value={formData.first_name} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label className="form-label">Last Name *</label>
                <input type="text" name="last_name" className="form-input" value={formData.last_name} onChange={handleChange} required />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Email *</label>
                <input type="email" name="email" className="form-input" value={formData.email} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label className="form-label">Phone</label>
                <input type="tel" name="phone" className="form-input" value={formData.phone} onChange={handleChange} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Address</label>
              <input type="text" name="address" className="form-input" value={formData.address} onChange={handleChange} />
            </div>
            <div className="form-row" style={{ gridTemplateColumns: '2fr 1fr 1fr' }}>
              <div className="form-group">
                <label className="form-label">City</label>
                <input type="text" name="city" className="form-input" value={formData.city} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label className="form-label">State</label>
                <input type="text" name="state" className="form-input" value={formData.state} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label className="form-label">ZIP</label>
                <input type="text" name="zip" className="form-input" value={formData.zip} onChange={handleChange} />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Date of Birth</label>
                <input type="date" name="dob" className="form-input" value={formData.dob} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label className="form-label">SSN (Last 4)</label>
                <input type="text" name="ssn_last4" className="form-input" maxLength={4} placeholder="1234" value={formData.ssn_last4} onChange={handleChange} />
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Documents */}
        {step === 1 && (
          <div>
            <h3 className="mb-2">Upload Documents</h3>
            <p className="page-subtitle mb-3">Upload ID, proof of address, or other documents</p>
            <div
              className="upload-zone"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <div className="upload-zone-icon">📁</div>
              <p>Drag & drop files here or</p>
              <label className="btn btn-outline btn-sm" style={{ cursor: 'pointer' }}>
                Browse Files
                <input type="file" multiple onChange={handleFileChange} style={{ display: 'none' }} />
              </label>
              <span className="upload-zone-hint">PDF, JPG, PNG up to 10MB each</span>
            </div>

            {documents.length > 0 && (
              <div className="uploaded-files mt-2">
                {documents.map((file, i) => (
                  <div key={i} className="uploaded-file">
                    <span className="uploaded-file-icon">📄</span>
                    <span className="uploaded-file-name">{file.name}</span>
                    <span className="uploaded-file-size">{(file.size / 1024).toFixed(0)} KB</span>
                    <button className="uploaded-file-remove" onClick={() => removeDoc(i)}>✕</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 3: Review */}
        {step === 2 && (
          <div>
            <h3 className="mb-2">Review & Submit</h3>
            <p className="page-subtitle mb-3">Please review the information before submitting</p>
            <div className="review-section">
              <h4>Personal Information</h4>
              <div className="info-grid" style={{ marginTop: 12 }}>
                <div className="info-item">
                  <span className="info-label">Name</span>
                  <span className="info-value">{formData.first_name} {formData.last_name}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Email</span>
                  <span className="info-value">{formData.email}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Phone</span>
                  <span className="info-value">{formData.phone || '—'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Address</span>
                  <span className="info-value">{formData.address ? `${formData.address}, ${formData.city} ${formData.state} ${formData.zip}` : '—'}</span>
                </div>
              </div>
            </div>
            <div className="review-section">
              <h4>Documents</h4>
              <p className="page-subtitle">{documents.length} file(s) attached</p>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="onboarding-nav">
        {step > 0 && (
          <button className="btn btn-ghost" onClick={() => setStep(step - 1)}>
            ← Previous
          </button>
        )}
        <div style={{ flex: 1 }}></div>
        {step < steps.length - 1 ? (
          <button className="btn btn-primary" onClick={nextStep}>
            Next →
          </button>
        ) : (
          <button className="btn btn-success" onClick={handleSubmit} disabled={loading}>
            {loading ? 'Creating...' : '✓ Create Client'}
          </button>
        )}
      </div>
    </div>
  );
}
