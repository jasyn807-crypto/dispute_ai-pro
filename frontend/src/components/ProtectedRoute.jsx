import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children, requiredRole }) {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

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
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    const redirect = user?.role === 'client' ? '/portal' : '/dashboard';
    return <Navigate to={redirect} replace />;
  }

  return children;
}
