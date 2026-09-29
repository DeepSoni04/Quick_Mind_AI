import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

/** Returns a 2-character avatar string from a full name */
export function makeAvatar(name = '') {
  const parts = name.trim().split(/\s+/);
  return (parts[0]?.[0] || '?').toUpperCase() + (parts[1]?.[0] || '').toUpperCase();
}

// Initial mock user store with complete profile data
let MOCK_USERS = [
  {
    id: 1,
    name: 'Deep Soni',
    email: 'deep@querymind.ai',
    password: 'admin123',
    role: 'admin',
    avatar: 'DS',
    title: 'Lead Data Architect & AI Admin',
    department: 'Data Platform & AI Infrastructure',
    bio: 'Overseeing MongoDB and vector pipeline schemas with automated NL query generation and enterprise security.',
    phone: '+91 98765 43210',
    location: 'Ahmedabad, India',
    joinedDate: 'January 2026',
    twoFactorEnabled: true,
    apiToken: 'qm_live_7e8b9401ad2c35f992a',
    stats: {
      queriesRun: 342,
      savedQueries: 28,
      connectedClusters: 3,
      successRate: '99.6%',
    },
  },
  {
    id: 2,
    name: 'Heer Sachdev',
    email: 'heer@querymind.ai',
    password: 'analyst123',
    role: 'analyst',
    avatar: 'HS',
    title: 'Senior Database Analyst',
    department: 'Business Intelligence & Student Analytics',
    bio: 'Specializing in student metrics, cohort retention, and SQL/MQL optimization workflows.',
    phone: '+91 98250 12345',
    location: 'Surat, India',
    joinedDate: 'February 2026',
    twoFactorEnabled: true,
    apiToken: 'qm_live_3c2d1840ef9a81b742e',
    stats: {
      queriesRun: 184,
      savedQueries: 19,
      connectedClusters: 2,
      successRate: '98.9%',
    },
  },
  {
    id: 3,
    name: 'Neel Shah',
    email: 'neel@querymind.ai',
    password: 'viewer123',
    role: 'viewer',
    avatar: 'NS',
    title: 'Data Auditor & Reviewer',
    department: 'Operations & Compliance',
    bio: 'Auditing query performance, rate limits, and dashboard compliance standards.',
    phone: '+91 97120 67890',
    location: 'Vadodara, India',
    joinedDate: 'March 2026',
    twoFactorEnabled: false,
    apiToken: 'qm_live_9b1f4820ca3e65d881c',
    stats: {
      queriesRun: 67,
      savedQueries: 6,
      connectedClusters: 1,
      successRate: '97.4%',
    },
  },
];

export function AuthProvider({ children }) {
  // Initialize from localStorage if available, or default to Deep Soni for seamless dev experience
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('qm_user');
      if (stored) {
        return JSON.parse(stored);
      }
    } catch {
      // ignore
    }
    // Default logged in user in dev mode
    return MOCK_USERS[0];
  });

  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    try {
      const storedAuth = localStorage.getItem('qm_auth');
      if (storedAuth !== null) {
        return storedAuth === 'true';
      }
    } catch {
      // ignore
    }
    return true; // default true for frictionless development
  });

  // Sync state changes to localStorage
  useEffect(() => {
    try {
      if (user) {
        localStorage.setItem('qm_user', JSON.stringify(user));
        localStorage.setItem('qm_auth', 'true');
      } else {
        localStorage.removeItem('qm_user');
        localStorage.setItem('qm_auth', 'false');
      }
    } catch {
      // ignore
    }
  }, [user]);

  /** Login — matches against MOCK_USERS by email */
  const login = (email, password) => {
    const found = MOCK_USERS.find((u) => u.email.toLowerCase() === (email || '').toLowerCase());
    if (found) {
      setUser(found);
      setIsAuthenticated(true);
      return { success: true, user: found };
    }
    // Unknown email → auto-login as viewer so demo always works
    const demoUser = {
      id: Date.now(),
      name: email.split('@')[0],
      email,
      password: password || 'demo123',
      role: 'viewer',
      avatar: makeAvatar(email.split('@')[0]),
      title: 'Database User',
      department: 'General Access',
      bio: 'QuickMind AI workspace explorer.',
      phone: '+91 98000 00000',
      location: 'India',
      joinedDate: 'September 2026',
      twoFactorEnabled: false,
      apiToken: 'qm_live_' + Math.random().toString(36).slice(2, 10),
      stats: {
        queriesRun: 0,
        savedQueries: 0,
        connectedClusters: 1,
        successRate: '100%',
      },
    };
    MOCK_USERS = [...MOCK_USERS, demoUser];
    setUser(demoUser);
    setIsAuthenticated(true);
    return { success: true, user: demoUser };
  };

  /** Sign Up — creates a new mock user and logs them in as analyst */
  const signup = (name, email, password) => {
    const existing = MOCK_USERS.find((u) => u.email.toLowerCase() === email.toLowerCase());
    if (existing) {
      return { success: false, error: 'An account with that email already exists.' };
    }
    const newUser = {
      id: Date.now(),
      name,
      email,
      password,
      role: 'analyst',
      avatar: makeAvatar(name),
      title: 'Data Analyst',
      department: 'Analytics Department',
      bio: 'QueryMind user exploring natural language database queries.',
      phone: '+91 98000 00000',
      location: 'India',
      joinedDate: 'September 2026',
      twoFactorEnabled: false,
      apiToken: 'qm_live_' + Math.random().toString(36).slice(2, 10),
      stats: {
        queriesRun: 0,
        savedQueries: 0,
        connectedClusters: 1,
        successRate: '100%',
      },
    };
    MOCK_USERS = [...MOCK_USERS, newUser];
    setUser(newUser);
    setIsAuthenticated(true);
    return { success: true, user: newUser };
  };

  /** Update profile fields and persist */
  const updateProfile = (updates = {}) => {
    if (!user) return { success: false, error: 'No authenticated user' };

    const updatedUser = {
      ...user,
      ...updates,
      avatar: updates.name ? makeAvatar(updates.name) : user.avatar,
    };

    // Keep MOCK_USERS in sync
    MOCK_USERS = MOCK_USERS.map((u) => (u.id === user.id ? { ...u, ...updatedUser } : u));
    setUser(updatedUser);
    return { success: true, user: updatedUser };
  };

  /** Change Password */
  const changePassword = (currentPassword, newPassword) => {
    if (!user) return { success: false, error: 'No authenticated user' };
    if (user.password && currentPassword && user.password !== currentPassword) {
      return { success: false, error: 'Current password does not match.' };
    }
    const updatedUser = { ...user, password: newPassword };
    MOCK_USERS = MOCK_USERS.map((u) => (u.id === user.id ? { ...u, ...updatedUser } : u));
    setUser(updatedUser);
    return { success: true };
  };

  /** Toggle 2FA */
  const toggleTwoFactor = () => {
    if (!user) return false;
    const newState = !user.twoFactorEnabled;
    const updatedUser = { ...user, twoFactorEnabled: newState };
    MOCK_USERS = MOCK_USERS.map((u) => (u.id === user.id ? { ...u, ...updatedUser } : u));
    setUser(updatedUser);
    return newState;
  };

  /** Regenerate API Token */
  const regenerateApiToken = () => {
    if (!user) return null;
    const newToken = 'qm_live_' + Math.random().toString(36).slice(2, 10) + Math.random().toString(36).slice(2, 10);
    const updatedUser = { ...user, apiToken: newToken };
    MOCK_USERS = MOCK_USERS.map((u) => (u.id === user.id ? { ...u, ...updatedUser } : u));
    setUser(updatedUser);
    return newToken;
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    try {
      localStorage.removeItem('qm_user');
      localStorage.setItem('qm_auth', 'false');
    } catch {
      // ignore
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        login,
        signup,
        logout,
        updateProfile,
        changePassword,
        toggleTwoFactor,
        regenerateApiToken,
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

/** Exported so AdminPage can read/write mock users directly */
export function getMockUsers()        { return [...MOCK_USERS]; }
export function setMockUsers(updated) { MOCK_USERS = updated; }

