import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  MessageSquare, History, LayoutDashboard, Database,
  Settings, LogOut, ChevronLeft, ChevronRight, Brain, Shield
} from 'lucide-react';
import './Sidebar.css';
import { useState } from 'react';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/chat', icon: MessageSquare, label: 'Query Chat' },
    { to: '/history', icon: History, label: 'Query History' },
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/databases', icon: Database, label: 'Databases' },
  ];

  const adminItems = [
    { to: '/admin', icon: Shield, label: 'Admin Panel' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
      {/* Brand */}
      <div className="sidebar__brand">
        <div className="sidebar__logo">
          <Brain size={28} />
        </div>
        {!collapsed && (
          <div className="sidebar__brand-text">
            <span className="sidebar__title">QueryMind</span>
            <span className="sidebar__subtitle">AI Assistant</span>
          </div>
        )}
        <button className="sidebar__toggle" onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar__nav">
        <div className="sidebar__section">
          {!collapsed && <span className="sidebar__section-label">Main</span>}
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
              title={item.label}
            >
              <item.icon size={20} />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </div>

        {user?.role === 'admin' && (
          <div className="sidebar__section">
            {!collapsed && <span className="sidebar__section-label">Administration</span>}
            {adminItems.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
                title={item.label}
              >
                <item.icon size={20} />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            ))}
          </div>
        )}
      </nav>

      {/* User section */}
      <div className="sidebar__footer">
        <div className="sidebar__user">
          <div className="sidebar__avatar">{user?.avatar}</div>
          {!collapsed && (
            <div className="sidebar__user-info">
              <span className="sidebar__user-name">{user?.name}</span>
              <span className="sidebar__user-role">{user?.role}</span>
            </div>
          )}
        </div>
        <button className="sidebar__logout" onClick={handleLogout} title="Logout">
          <LogOut size={18} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
