import { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

// Mock users for demo
const MOCK_USERS = [
  { id: 1, name: 'Deep Soni', email: 'deep@querymind.ai', role: 'admin', avatar: 'DS' },
  { id: 2, name: 'Heer Sachdev', email: 'heer@querymind.ai', role: 'analyst', avatar: 'HS' },
  { id: 3, name: 'Neel Shah', email: 'neel@querymind.ai', role: 'viewer', avatar: 'NS' },
];

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = (email, password) => {
    // Mock login — accepts any password
    const found = MOCK_USERS.find(u => u.email === email);
    if (found) {
      setUser(found);
      setIsAuthenticated(true);
      return { success: true };
    }
    // Auto-login as viewer for demo
    const demoUser = { id: 99, name: email.split('@')[0], email, role: 'viewer', avatar: email[0].toUpperCase() + (email[1] || '').toUpperCase() };
    setUser(demoUser);
    setIsAuthenticated(true);
    return { success: true };
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
