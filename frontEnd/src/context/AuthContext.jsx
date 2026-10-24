import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authLogin, authRegister, authMe, authLogout, updateProfile } from './api';

const AuthContext = createContext(null);

/** Returns a 2-character avatar string from a full name */
function makeAvatar(name = '') {
  const parts = (name || '').trim().split(/\s+/);
  return ((parts[0]?.[0] || '?').toUpperCase() + (parts[1]?.[0] || '').toUpperCase());
}

/** Enrich a raw user object returned by the API with a computed avatar */
function enrichUser(u) {
  if (!u) return null;
  return { ...u, avatar: u.avatar || makeAvatar(u.name) };
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
   * updateUser — calls PUT /api/auth/me and updates stored user in context.
   * Returns { success, user } or { success: false, error }.
   */
  const updateUser = useCallback(async (name) => {
    try {
      const updated = await updateProfile(name);
      const enriched = enrichUser(updated);
      setUser(enriched);
      return { success: true, user: enriched };
    } catch (err) {
      return { success: false, error: err.message || 'Failed to update profile.' };
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, login, signup, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

// Legacy exports — kept for any component that imported them from the mock
export function getMockUsers()        { return []; }
export function setMockUsers()        {}
