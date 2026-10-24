import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * Requires authenticated session. Redirects to /login if not authenticated.
 * Shows nothing while auth is being restored from localStorage (JWT validation).
 */
export function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null; // Prevent flash of redirect while restoring session
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

/**
 * Requires role === 'admin'. Redirects to /workspace if authenticated but not admin.
 */
export function AdminRoute() {
  const { isAuthenticated, user, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.role !== 'admin') return <Navigate to="/workspace" replace />;
  return <Outlet />;
}
