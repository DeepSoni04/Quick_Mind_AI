import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * Requires authenticated session. Redirects to /login if not authenticated.
 */
export function ProtectedRoute() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

/**
 * Requires role === 'admin'. Redirects to /workspace if authenticated but not admin.
 */
export function AdminRoute() {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.role !== 'admin') return <Navigate to="/workspace" replace />;
  return <Outlet />;
}
