import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Login.css';

export default function Login() {
  const [mode, setMode] = useState('agency'); // 'agency' or 'client'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await login({ email, password, role: mode });
      if (user.role === 'client') {
        navigate('/portal');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.message || 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      {/* Animated background */}
      <div className="login-bg" aria-hidden="true">
        <div className="login-bg-orb login-bg-orb-1"></div>
        <div className="login-bg-orb login-bg-orb-2"></div>
        <div className="login-bg-orb login-bg-orb-3"></div>
        <div className="login-bg-grid"></div>
      </div>

      <main className="login-container animate-scale-in">
        {/* Logo */}
        <header className="login-header">
          <div className="login-logo">
            <div className="login-logo-icon" aria-hidden="true">⚡</div>
            <div>
              <h1 className="login-logo-name">CreditEngine</h1>
              <p className="login-logo-sub">AI-Powered Credit Repair</p>
            </div>
          </div>
        </header>

        {/* Mode Toggle */}
        <nav className="login-mode-toggle" aria-label="Login Mode Selection">
          <button
            type="button"
            className={`login-mode-btn ${mode === 'agency' ? 'active' : ''}`}
            onClick={() => setMode('agency')}
            aria-pressed={mode === 'agency'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
              <polyline points="9 22 9 12 15 12 15 22"></polyline>
            </svg>
            Agency Staff
          </button>
          <button
            type="button"
            className={`login-mode-btn ${mode === 'client' ? 'active' : ''}`}
            onClick={() => setMode('client')}
            aria-pressed={mode === 'client'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            Client Portal
          </button>
        </nav>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="login-form">
          <div role="alert" aria-live="polite">
            {error && (
              <div className="login-error animate-fade-in">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="15" y1="9" x2="9" y2="15"></line>
                  <line x1="9" y1="9" x2="15" y2="15"></line>
                </svg>
                {error}
              </div>
            )}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              className="form-input"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="btn btn-primary btn-lg w-full" disabled={loading}>
            {loading ? (
              <>
                <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} aria-hidden="true"></div>
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <span>Sign In</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
              </>
            )}
          </button>
        </form>

        {/* Footer Links */}
        <footer className="login-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/register">Create one</Link>
          </p>
        </footer>
      </main>

      {/* Feature badges */}
      <aside className="login-features" aria-label="Platform Features">
        <div className="login-feature-item">
          <span aria-hidden="true">🔒</span> Bank-Level Security
        </div>
        <div className="login-feature-item">
          <span aria-hidden="true">🤖</span> AI-Powered Analysis
        </div>
        <div className="login-feature-item">
          <span aria-hidden="true">📊</span> Real-Time Tracking
        </div>
      </aside>
    </div>
  );
}
