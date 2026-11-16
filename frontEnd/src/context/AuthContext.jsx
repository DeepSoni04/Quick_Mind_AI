import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  authLogin,
  authRegister,
  authMe,
  authLogout,
  updateProfile,
  changePassword as apiChangePassword,
  toggleTwoFactor as apiToggleTwoFactor,
  regenerateApiToken as apiRegenerateToken,
} from './api';

const AuthContext = createContext(null);

/** Returns a 2-character avatar string from a full name */
function makeAvatar(name = '') {
  const parts = (name || '').trim().split(/\s+/);
  return ((parts[0]?.[0] || '?').toUpperCase() + (parts[1]?.[0] || '').toUpperCase());
}

/** Enrich a raw user object returned by the API with all profile fields */
function enrichUser(u) {
  if (!u) return null;
  const role = u.role || 'viewer';
  return {
    ...u,
    avatar: u.avatar || makeAvatar(u.name),
    title: u.title || (role === 'admin' ? 'Lead Data Architect & AI Admin' : 'Database Analyst'),
    department: u.department || (role === 'admin' ? 'Data Platform & AI Infrastructure' : 'Analytics & Data Platforms'),
    bio: u.bio !== undefined ? u.bio : (
      role === 'admin'
        ? 'QueryMind Lead Data Architect & AI Administrator focusing on automated NL query synthesis, vector embeddings, and real-time operational database infrastructure.'
        : 'QueryMind database engineer exploring automated NL query models.'
    ),
    phone: u.phone || '+91 98765 43210',
    location: u.location || 'Ahmedabad, India',
    joinedDate: u.joined_date || u.joinedDate || 'January 2026',
    apiToken: u.api_token || u.apiToken || 'qm_live_a89f3c01e742b89d5543c2e109ab7d34',
    twoFactorEnabled: u.two_factor_enabled !== undefined ? !!u.two_factor_enabled : (u.twoFactorEnabled !== undefined ? !!u.twoFactorEnabled : true),
    stats: {
      queriesRun: u.stats?.queries_run ?? u.stats?.queriesRun ?? 342,
      savedQueries: u.stats?.saved_queries ?? u.stats?.savedQueries ?? 28,
      connectedClusters: u.stats?.connected_clusters ?? u.stats?.connectedClusters ?? 3,
      successRate: u.stats?.success_rate ?? u.stats?.successRate ?? '99.6%',
    },
  };
}

export function AuthProvider({ children }) {
  const [user, setUser]                   = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading]             = useState(true);

  // On mount: try to restore session from stored JWT
  useEffect(() => {
    const token = localStorage.getItem('qm_token');
    if (!token) {
      setLoading(false);
      return;
    }
    authMe()
      .then((u) => {
        if (u) {
          setUser(enrichUser(u));
          setIsAuthenticated(true);
        }
      })
      .catch(() => {
        // Token invalid or expired — clear it
        authLogout();
      })
      .finally(() => setLoading(false));
  }, []);

  /** Login — calls POST /api/auth/login */
  const login = useCallback(async (email, password) => {
    try {
      const data = await authLogin(email, password);
      const enriched = enrichUser(data.user);
      setUser(enriched);
      setIsAuthenticated(true);
      return { success: true, user: enriched };
    } catch (err) {
      return { success: false, error: err.message || 'Login failed.' };
    }
  }, []);

  /** Sign Up — calls POST /api/auth/register */
  const signup = useCallback(async (name, email, password) => {
    try {
      const data = await authRegister(name, email, password);
      const enriched = enrichUser(data.user);
      setUser(enriched);
      setIsAuthenticated(true);
      return { success: true, user: enriched };
    } catch (err) {
      return { success: false, error: err.message || 'Registration failed.' };
    }
  }, []);

  const logout = useCallback(() => {
    authLogout();
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  /**
   * updateProfile — calls PUT /api/auth/me and updates stored user in context.
   */
  const updateProfileHandler = useCallback(async (profileData) => {
    try {
      const updated = await updateProfile(profileData);
      const enriched = enrichUser(updated);
      setUser(enriched);
      return { success: true, user: enriched };
    } catch (err) {
      return { success: false, error: err.message || 'Failed to update profile.' };
    }
  }, []);

  /**
   * changePassword — calls POST /api/auth/change-password.
   */
  const changePasswordHandler = useCallback(async (currentPassword, newPassword) => {
    try {
      const res = await apiChangePassword(currentPassword, newPassword);
      return { success: true, message: res?.message || 'Password updated successfully.' };
    } catch (err) {
      return { success: false, error: err.message || 'Failed to update password.' };
    }
  }, []);

  /**
   * toggleTwoFactor — calls POST /api/auth/toggle-2fa.
   */
  const toggleTwoFactorHandler = useCallback(async () => {
    try {
      const res = await apiToggleTwoFactor();
      const newEnabled = !!res?.two_factor_enabled;
      setUser((prev) => prev ? { ...prev, twoFactorEnabled: newEnabled, two_factor_enabled: newEnabled } : null);
      return newEnabled;
    } catch (err) {
      return false;
    }
  }, []);

  /**
   * regenerateApiToken — calls POST /api/auth/regenerate-token.
   */
  const regenerateApiTokenHandler = useCallback(async () => {
    try {
      const res = await apiRegenerateToken();
      const newToken = res?.api_token;
      if (newToken) {
        setUser((prev) => prev ? { ...prev, apiToken: newToken, api_token: newToken } : null);
      }
      return newToken;
    } catch (err) {
      return null;
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        loading,
        login,
        signup,
        logout,
        updateUser: updateProfileHandler,
        updateProfile: updateProfileHandler,
        changePassword: changePasswordHandler,
        toggleTwoFactor: toggleTwoFactorHandler,
        regenerateApiToken: regenerateApiTokenHandler,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

// Legacy exports
export function getMockUsers()        { return []; }
export function setMockUsers()        {}
