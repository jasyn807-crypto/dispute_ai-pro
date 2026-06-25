import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

// Pages
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import Dashboard from './pages/Dashboard/Dashboard';
import Clients from './pages/Clients/Clients';
import ClientOnboarding from './pages/Clients/ClientOnboarding';
import ClientDetail from './pages/Clients/ClientDetail';
import CreditReports from './pages/CreditReports/CreditReports';
import Disputes from './pages/Disputes/Disputes';
import DisputeDetail from './pages/Disputes/DisputeDetail';
import ClientPortal from './pages/ClientPortal/ClientPortal';

// Helper component to redirect root / based on role
function RootRedirect() {
  const { isAuthenticated, isAgency, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="page-loader">
        <div className="page-loader-inner">
          <div className="spinner spinner-lg"></div>
          <p style={{ color: 'var(--text-muted)', marginTop: 16 }}>Loading...</p>
        </div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <Navigate to={isAgency ? "/dashboard" : "/portal"} replace />;
}

// Helper component to guard public routes (login/register)
function PublicRoute({ children }) {
  const { isAuthenticated, isAgency, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="page-loader">
        <div className="page-loader-inner">
          <div className="spinner spinner-lg"></div>
          <p style={{ color: 'var(--text-muted)', marginTop: 16 }}>Loading...</p>
        </div>
      </div>
    );
  }
  
  if (isAuthenticated) {
    return <Navigate to={isAgency ? "/dashboard" : "/portal"} replace />;
  }
  
  return children;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            {/* Agency Routes */}
            <Route path="/dashboard" element={<ProtectedRoute requiredRole="agency"><Dashboard /></ProtectedRoute>} />
            <Route path="/clients" element={<ProtectedRoute requiredRole="agency"><Clients /></ProtectedRoute>} />
            <Route path="/clients/new" element={<ProtectedRoute requiredRole="agency"><ClientOnboarding /></ProtectedRoute>} />
            <Route path="/clients/:id" element={<ProtectedRoute requiredRole="agency"><ClientDetail /></ProtectedRoute>} />
            <Route path="/reports" element={<ProtectedRoute requiredRole="agency"><CreditReports /></ProtectedRoute>} />
            <Route path="/disputes" element={<ProtectedRoute requiredRole="agency"><Disputes /></ProtectedRoute>} />
            <Route path="/disputes/:id" element={<ProtectedRoute requiredRole="agency"><DisputeDetail /></ProtectedRoute>} />

            {/* Client Routes */}
            <Route path="/portal" element={<ProtectedRoute requiredRole="client"><ClientPortal /></ProtectedRoute>} />
            <Route path="/portal/reports" element={<ProtectedRoute requiredRole="client"><ClientPortal /></ProtectedRoute>} />
            <Route path="/portal/disputes" element={<ProtectedRoute requiredRole="client"><ClientPortal /></ProtectedRoute>} />
            <Route path="/portal/documents" element={<ProtectedRoute requiredRole="client"><ClientPortal /></ProtectedRoute>} />
            <Route path="/portal/billing" element={<ProtectedRoute requiredRole="client"><ClientPortal /></ProtectedRoute>} />
          </Route>

          {/* Root Redirect & Fallbacks */}
          <Route path="/" element={<RootRedirect />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
