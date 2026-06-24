import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Sidebar.css';

const agencyNavItems = [
  { path: '/dashboard', icon: '📊', label: 'Dashboard' },
  { path: '/clients', icon: '👥', label: 'Clients' },
  { path: '/disputes', icon: '⚖️', label: 'Disputes' },
  { path: '/mailing', icon: '📬', label: 'Mailing' },
  { path: '/settings', icon: '⚙️', label: 'Settings' },
];

const clientNavItems = [
  { path: '/portal', icon: '🏠', label: 'Overview' },
  { path: '/portal/reports', icon: '📋', label: 'My Reports' },
  { path: '/portal/disputes', icon: '⚖️', label: 'My Disputes' },
  { path: '/portal/documents', icon: '📁', label: 'Documents' },
];

export default function Sidebar() {
  const { user, isClient } = useAuth();
  const navItems = isClient ? clientNavItems : agencyNavItems;

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">⚡</div>
          <div className="sidebar-logo-text">
            <span className="sidebar-logo-name">CreditEngine</span>
            <span className="sidebar-logo-sub">AI Platform</span>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-nav-label">MENU</div>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/dashboard' || item.path === '/portal'}
            className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="sidebar-nav-icon">{item.icon}</span>
            <span className="sidebar-nav-text">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-user-avatar">
            {user?.name?.[0] || user?.email?.[0] || 'U'}
          </div>
          <div className="sidebar-user-info">
            <span className="sidebar-user-name">{user?.name || user?.email}</span>
            <span className="sidebar-user-role">{isClient ? 'Client' : 'Agency Staff'}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
