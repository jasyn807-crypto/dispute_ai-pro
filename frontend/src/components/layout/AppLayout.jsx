import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import './AppLayout.css';

export default function AppLayout() {
  return (
    <div className="app-layout">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <Sidebar />
      <div className="app-main-wrapper">
        <Navbar />
        <main className="app-content" id="main-content" role="main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
