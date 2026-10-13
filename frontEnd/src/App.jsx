import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute, AdminRoute } from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';
import LoginPage from './pages/LoginPage';
import SignUpPage from './pages/SignUpPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ChatPage from './pages/ChatPage';
import HistoryPage from './pages/HistoryPage';
import SavedQueriesPage from './pages/SavedQueriesPage';
import DashboardPage from './pages/DashboardPage';
import DatabasesPage from './pages/DatabasesPage';
import SettingsPage from './pages/SettingsPage';
import AdminPage from './pages/AdminPage';
import ProfilePage from './pages/ProfilePage';

function AppLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes (no auth required) */}
          <Route path="/login"           element={<LoginPage />} />
          <Route path="/signup"          element={<SignUpPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />

          {/* Root redirect: go to login by default */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Protected app shell — requires authentication */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              {/* Query Group (Screens 2–6) */}
              <Route path="/workspace"      element={<ChatPage view="workspace" />} />
              <Route path="/processing"     element={<ChatPage view="processing" />} />
              <Route path="/result"         element={<ChatPage view="result" />} />
              <Route path="/update-preview" element={<ChatPage view="update-preview" />} />
              <Route path="/delete-confirm" element={<ChatPage view="delete-confirm" />} />

              {/* Dashboard */}
              <Route path="/dashboard"      element={<DashboardPage />} />

              {/* History & Saved */}
              <Route path="/history"        element={<HistoryPage />} />
              <Route path="/saved"          element={<SavedQueriesPage />} />

              {/* Connections */}
              <Route path="/connections"    element={<DatabasesPage view="list" />} />
              <Route path="/add-connection" element={<DatabasesPage view="add" />} />

              {/* Settings */}
              <Route path="/settings"       element={<SettingsPage />} />

              {/* Profile */}
              <Route path="/profile"        element={<ProfilePage />} />
            </Route>

            {/* Admin Panel — admin role only */}
            <Route element={<AdminRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/admin" element={<AdminPage />} />
              </Route>
            </Route>
          </Route>

          {/* Catch-all → login */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
