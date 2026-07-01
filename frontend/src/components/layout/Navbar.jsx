import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './Navbar.css';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="navbar" role="banner">
      <div className="navbar-left">
        <button 
          className="navbar-mobile-toggle" 
          onClick={() => {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
              const isOpen = sidebar.classList.contains('sidebar-mobile-open');
              sidebar.classList.toggle('sidebar-mobile-open');
              document.querySelector('.navbar-mobile-toggle')?.setAttribute('aria-expanded', (!isOpen).toString());
            }
          }}
          aria-label="Toggle Navigation Menu"
          aria-expanded="false"
        >
          <span></span><span></span><span></span>
        </button>
        <div className="navbar-breadcrumb">
          <span className="navbar-welcome">Welcome back,</span>
          <span className="navbar-user-name">
            {user?.agency_profile?.name || user?.name || user?.email || 'User'}
          </span>
        </div>
      </div>

      <div className="navbar-right">
        <button className="navbar-icon-btn" title="Notifications" aria-label="View Notifications">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
          <span className="navbar-notification-dot"></span>
        </button>

        <div className="navbar-divider" aria-hidden="true"></div>

        <button className="navbar-user-btn" onClick={handleLogout} title="Logout" aria-label="Logout">
          <div className="navbar-avatar" aria-hidden="true">
            {user?.name?.[0] || user?.email?.[0] || 'U'}
          </div>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
        </button>
      </div>
    </header>
  );
}
