import { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

// Mutable in-memory user store (let so signup can push new users)
let MOCK_USERS = [
  { id: 1, name: 'Deep Soni',      email: 'deep@querymind.ai',     password: 'admin123',   role: 'admin',   avatar: 'DS' },
  { id: 2, name: 'Heer Sachdev',   email: 'heer@querymind.ai',     password: 'analyst123', role: 'analyst', avatar: 'HS' },
  { id: 3, name: 'Neel Shah',      email: 'neel@querymind.ai',     password: 'viewer123',  role: 'viewer',  avatar: 'NS' },
];

/** Returns a 2-character avatar string from a full name */
function makeAvatar(name = '') {
  const parts = name.trim().split(/\s+/);
  return (parts[0]?.[0] || '?').toUpperCase() + (parts[1]?.[0] || '').toUpperCase();
}

export function AuthProvider({ children }) {
  const [user, setUser]                   = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  /** Login — matches against MOCK_USERS by email (any password accepted for demo) */
  const login = (email, _password) => {
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
      role: 'viewer',
      avatar: makeAvatar(email.split('@')[0]),
    };
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
      role: 'analyst', // default role for self-signup
      avatar: makeAvatar(name),
    };
    MOCK_USERS = [...MOCK_USERS, newUser];
    setUser(newUser);
    setIsAuthenticated(true);
    return { success: true, user: newUser };
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, signup, logout }}>
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
export function getMockUsers()          { return [...MOCK_USERS]; }
export function setMockUsers(updated)   { MOCK_USERS = updated; }
