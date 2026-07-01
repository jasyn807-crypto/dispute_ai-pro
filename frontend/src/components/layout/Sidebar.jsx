import { NavLink } from 'react-router-dom';
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
    <aside className="sidebar" aria-label="Sidebar Navigation">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon" aria-hidden="true">⚡</div>
          <div className="sidebar-logo-text">
            <span className="sidebar-logo-name">CreditEngine</span>
            <span className="sidebar-logo-sub">AI Platform</span>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Main Menu">
        <div className="sidebar-nav-label" id="menu-label">MENU</div>
        <ul className="sidebar-nav-list" aria-labelledby="menu-label">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                end={item.path === '/dashboard' || item.path === '/portal'}
                className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
                aria-current={({ isActive }) => isActive ? 'page' : undefined}
              >
                <span className="sidebar-nav-icon" aria-hidden="true">{item.icon}</span>
                <span className="sidebar-nav-text">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-user-avatar" aria-hidden="true">
            {user?.name?.[0] || user?.email?.[0] || 'U'}
          </div>
          <div className="sidebar-user-info">
            <span className="sidebar-user-name">{user?.agency_profile?.name || user?.name || user?.email}</span>
            <span className="sidebar-user-role">{isClient ? 'Client' : 'Agency Staff'}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
