import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Register.css';

export default function Register() {
  const [mode, setMode] = useState('agency');
  const [formData, setFormData] = useState({
    agency_name: '',
    owner_name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    agency_code: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    setLoading(true);
    try {
      const payload = mode === 'agency'
        ? {
            role: 'agency',
            agency_name: formData.agency_name,
            name: formData.owner_name,
            email: formData.email,
            phone: formData.phone,
            password: formData.password,
          }
        : {
            role: 'client',
            first_name: formData.first_name,
            last_name: formData.last_name,
            email: formData.email,
            password: formData.password,
            agency_code: formData.agency_code,
          };

      const user = await register(payload);
      navigate(user.role === 'client' ? '/portal' : '/dashboard');
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-page">
      <div className="login-bg">
        <div className="login-bg-orb login-bg-orb-1"></div>
        <div className="login-bg-orb login-bg-orb-2"></div>
        <div className="login-bg-grid"></div>
      </div>

      <div className="register-container animate-scale-in">
        <div className="login-header">
          <div className="login-logo">
            <div className="login-logo-icon">⚡</div>
            <div>
              <h1 className="login-logo-name">CreditEngine</h1>
              <p className="login-logo-sub">Create Your Account</p>
            </div>
          </div>
        </div>

        <div className="login-mode-toggle">
          <button
            className={`login-mode-btn ${mode === 'agency' ? 'active' : ''}`}
            onClick={() => setMode('agency')}
          >
            🏢 Agency
          </button>
          <button
            className={`login-mode-btn ${mode === 'client' ? 'active' : ''}`}
            onClick={() => setMode('client')}
          >
            👤 Client
          </button>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="login-error animate-fade-in">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
              </svg>
              {error}
            </div>
          )}

          {mode === 'agency' ? (
            <>
              <div className="form-group">
                <label className="form-label">Agency Name</label>
                <input
                  type="text" name="agency_name" className="form-input"
                  placeholder="Your credit repair agency name"
                  value={formData.agency_name} onChange={handleChange} required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Owner Full Name</label>
                <input
                  type="text" name="owner_name" className="form-input"
                  placeholder="John Smith"
                  value={formData.owner_name} onChange={handleChange} required
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <input
                    type="email" name="email" className="form-input"
                    placeholder="agency@email.com"
                    value={formData.email} onChange={handleChange} required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Phone Number</label>
                  <input
                    type="tel" name="phone" className="form-input"
                    placeholder="(555) 123-4567"
                    value={formData.phone} onChange={handleChange}
                  />
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">First Name</label>
                  <input
                    type="text" name="first_name" className="form-input"
                    placeholder="John"
                    value={formData.first_name} onChange={handleChange} required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Last Name</label>
                  <input
                    type="text" name="last_name" className="form-input"
                    placeholder="Doe"
                    value={formData.last_name} onChange={handleChange} required
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  type="email" name="email" className="form-input"
                  placeholder="your@email.com"
                  value={formData.email} onChange={handleChange} required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Agency Code</label>
                <input
                  type="text" name="agency_code" className="form-input"
                  placeholder="Enter your agency's invite code"
                  value={formData.agency_code} onChange={handleChange} required
                />
              </div>
            </>
          )}

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password" name="password" className="form-input"
                placeholder="Min 8 characters"
                value={formData.password} onChange={handleChange} required minLength={8}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <input
                type="password" name="confirmPassword" className="form-input"
                placeholder="Confirm password"
                value={formData.confirmPassword} onChange={handleChange} required
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-lg w-full" disabled={loading}>
            {loading ? (
              <>
                <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }}></div>
                Creating Account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="login-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
