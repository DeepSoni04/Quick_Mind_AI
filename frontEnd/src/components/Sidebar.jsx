import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

export default function Sidebar() {
  const location  = useLocation();
  const navigate  = useNavigate();
  const { user, logout }  = useAuth();
  const path      = location.pathname;
  const role      = user?.role || 'viewer';

  const isQueryActive    = ['/', '/workspace', '/processing', '/result', '/update-preview', '/delete-confirm'].includes(path);
  const isDashActive     = path.startsWith('/dashboard');
  const isHistoryActive  = path.startsWith('/history');
  const isSavedActive    = path.startsWith('/saved');
  const isConnectActive  = path.startsWith('/connections') || path.startsWith('/add-connection');
  const isAdminActive    = path.startsWith('/admin');
  const isSettingsActive = path.startsWith('/settings');
  const isProfileActive  = path.startsWith('/profile');

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const topNavItems = [
    {
      id: 'query', label: 'Query', to: '/workspace', active: isQueryActive,
      icon: (
        <svg viewBox="0 0 17 17" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="7" cy="7" r="4.5" />
          <line x1="10.5" y1="10.5" x2="14.5" y2="14.5" />
          <line x1="5" y1="7" x2="9" y2="7" strokeWidth="1.1" />
          <line x1="7" y1="5" x2="7" y2="9" strokeWidth="1.1" />
        </svg>
      ),
    },
    {
      id: 'dashboard', label: 'Dashboard', to: '/dashboard', active: isDashActive,
      icon: (
        <svg viewBox="0 0 17 17" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="2" width="5.5" height="5.5" rx="1.2" />
          <rect x="9.5" y="2" width="5.5" height="5.5" rx="1.2" />
          <rect x="2" y="9.5" width="5.5" height="5.5" rx="1.2" />
          <rect x="9.5" y="9.5" width="5.5" height="5.5" rx="1.2" />
        </svg>
      ),
    },
    {
      id: 'history', label: 'History', to: '/history', active: isHistoryActive,
      icon: (
        <svg viewBox="0 0 17 17" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="8.5" cy="8.5" r="5.5" />
          <polyline points="8.5 5.5 8.5 8.5 11 8.5" />
          <path d="M4.5 4.5 L3 3 M3 6 L3 3 L6 3" />
        </svg>
      ),
    },
    {
      id: 'saved', label: 'Saved', to: '/saved', active: isSavedActive,
      icon: (
        <svg viewBox="0 0 17 17" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 2.5 h6.5 l3 3 V14.5 a1 1 0 0 1 -1 1 H4 a1 1 0 0 1 -1 -1 V3.5 a1 1 0 0 1 1 -1 Z" />
          <line x1="5.5" y1="7" x2="11.5" y2="7" />
          <line x1="5.5" y1="9.5" x2="11.5" y2="9.5" />
          <line x1="5.5" y1="12" x2="9.5" y2="12" />
        </svg>
      ),
    },
    {
      id: 'connect', label: 'Connect', to: '/connections', active: isConnectActive,
      icon: (
        <svg viewBox="0 0 17 17" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <ellipse cx="8.5" cy="4" rx="5.5" ry="2" />
          <path d="M3 4 v4.5 c0 1.1 2.5 2 5.5 2 s5.5 -0.9 5.5 -2 V4" />
          <path d="M3 8.5 v4 c0 1.1 2.5 2 5.5 2 s5.5 -0.9 5.5 -2 v-4" />
        </svg>
      ),
    },
    // Admin Panel — only visible to admins
    ...(role === 'admin' ? [{
      id: 'admin', label: 'Admin', to: '/admin', active: isAdminActive,
      icon: (
        <svg viewBox="0 0 17 17" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M8.5 1.5 L14 4.5 v4 c0 3.5-5.5 6.5-5.5 6.5S3 12 3 8.5 v-4 z" />
          <polyline points="6 8.5 8 10.5 11.5 7" />
        </svg>
      ),
    }] : []),
  ];

  const bottomNavItems = [
    {
      id: 'settings', label: 'Settings', to: '/settings', active: isSettingsActive,
      icon: (
        <svg viewBox="0 0 17 17" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="8.5" cy="8.5" r="2.2" />
          <path d="M8.5 1.5 v1.5 M8.5 14 v1.5 M1.5 8.5 h1.5 M14 8.5 h1.5 M3.5 3.5 l1.1 1.1 M12.4 12.4 l1.1 1.1 M3.5 13.5 l1.1 -1.1 M12.4 4.6 l1.1 -1.1" />
        </svg>
      ),
    },
  ];

  const renderItem = (item) => (
    <div key={item.id} className="sidebar__item-wrapper">
      <button
        type="button"
        className={`sidebar__item ${item.active ? 'sidebar__item--active' : ''}`}
        onClick={() => navigate(item.to)}
        title={item.label}
      >
        {item.active && <div className="sidebar__indicator" />}
        <span className="sidebar__item-icon">{item.icon}</span>
        <span className="sidebar__item-label">{item.label}</span>
      </button>
    </div>
  );

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar__brand">
        <button
          className="sidebar__logo-link"
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
          onClick={() => navigate('/workspace')}
          title="QueryMind Home"
        >
          <svg className="sidebar__logo-svg" viewBox="0 0 28 28" width="24" height="24">
            <circle cx="14" cy="14" r="12" stroke="rgba(254,239,184,0.35)" strokeWidth="1" fill="none" />
            <circle cx="14" cy="14" r="7" stroke="rgba(254,239,184,0.55)" strokeWidth="1" fill="none" />
            <circle cx="14" cy="14" r="2.5" fill="rgba(254,239,184,0.90)" />
          </svg>
        </button>
      </div>

      {/* Top navigation */}
      <nav className="sidebar__nav">
        {topNavItems.map(renderItem)}

        {/* Bottom-pinned settings */}
        {bottomNavItems.map((item) => (
          <div key={item.id} className="sidebar__item-wrapper sidebar__item-wrapper--bottom">
            <button
              type="button"
              className={`sidebar__item ${item.active ? 'sidebar__item--active' : ''}`}
              onClick={() => navigate(item.to)}
              title={item.label}
            >
              {item.active && <div className="sidebar__indicator" />}
              <span className="sidebar__item-icon">{item.icon}</span>
              <span className="sidebar__item-label">{item.label}</span>
            </button>
          </div>
        ))}

        {/* User profile + Logout */}
        <div className="sidebar__user-section">
          <button
            type="button"
            className={`sidebar__user-btn ${isProfileActive ? 'sidebar__user-btn--active' : ''}`}
            onClick={() => navigate('/profile')}
            title={`${user?.name || 'Account'} — Open Profile`}
          >
            {isProfileActive && <div className="sidebar__indicator" />}
            <span className="sidebar__user-avatar">{user?.avatar || '?'}</span>
            <span className="sidebar__user-label">Account</span>
          </button>
          <button
            type="button"
            className="sidebar__logout-btn"
            onClick={handleLogout}
            title="Sign out"
          >
            <svg className="sidebar__logout-icon" viewBox="0 0 17 17" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 12v2.5H3V2.5h8V5" />
              <polyline points="9 8.5 14 8.5" />
              <polyline points="12 6.5 14 8.5 12 10.5" />
            </svg>
            Logout
          </button>
        </div>
      </nav>
    </aside>
  );
}
