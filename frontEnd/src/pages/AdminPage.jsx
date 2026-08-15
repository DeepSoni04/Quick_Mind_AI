import { useState } from 'react';
import {
  Shield, Users, Database, Activity, Settings, Search,
  UserPlus, Edit3, Trash2, Eye, EyeOff, Key, BarChart3, AlertTriangle
} from 'lucide-react';
import './AdminPage.css';

const MOCK_USERS = [
  { id: 1, name: 'Deep Soni', email: 'deep@querymind.ai', role: 'admin', status: 'active', queries: 342, lastActive: '2 min ago' },
  { id: 2, name: 'Ishpreet Kaur', email: 'ishpreet@querymind.ai', role: 'analyst', status: 'active', queries: 218, lastActive: '10 min ago' },
  { id: 3, name: 'Neel Shah', email: 'neel@querymind.ai', role: 'analyst', status: 'active', queries: 195, lastActive: '25 min ago' },
  { id: 4, name: 'Harsh Rathod', email: 'harsh@querymind.ai', role: 'analyst', status: 'active', queries: 167, lastActive: '1 hour ago' },
  { id: 5, name: 'Nishit Gal', email: 'nishit@querymind.ai', role: 'viewer', status: 'active', queries: 89, lastActive: '2 hours ago' },
  { id: 6, name: 'Parshwa Jain', email: 'parshwa@querymind.ai', role: 'analyst', status: 'inactive', queries: 134, lastActive: '3 days ago' },
  { id: 7, name: 'Heer Sachdev', email: 'heer@querymind.ai', role: 'analyst', status: 'active', queries: 201, lastActive: '5 min ago' },
  { id: 8, name: 'Bansari Akhani', email: 'bansari@querymind.ai', role: 'viewer', status: 'active', queries: 76, lastActive: '45 min ago' },
];

const SECURITY_LOGS = [
  { time: '19:22', event: 'Blocked destructive query: DROP TABLE', user: 'Neel Shah', severity: 'high' },
  { time: '18:45', event: 'SQL injection pattern detected', user: 'Unknown', severity: 'critical' },
  { time: '17:30', event: 'Role escalation attempt blocked', user: 'Guest User', severity: 'high' },
  { time: '16:10', event: 'Query timeout enforced (30s limit)', user: 'Parshwa Jain', severity: 'medium' },
  { time: '15:45', event: 'Unauthorized table access blocked', user: 'Nishit Gal', severity: 'medium' },
];

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('users');
  const [search, setSearch] = useState('');

  const filteredUsers = MOCK_USERS.filter(u =>
    u.name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  const tabs = [
    { id: 'users', label: 'Users', icon: Users },
    { id: 'security', label: 'Security Logs', icon: Shield },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  ];

  return (
    <div className="admin-page">
      <header className="admin-page__header">
        <div>
          <h1><Shield size={24} /> Admin Panel</h1>
          <p>Manage users, security, and system settings</p>
        </div>
        <button className="btn btn-primary"><UserPlus size={16} /> Add User</button>
      </header>

      {/* Tabs */}
      <div className="admin-page__tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`admin-page__tab ${activeTab === tab.id ? 'admin-page__tab--active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="admin-page__content animate-fade-in">
          <div className="admin-page__toolbar">
            <div className="admin-page__search">
              <Search size={16} />
              <input
                className="input-field"
                placeholder="Search users..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>

          <div className="admin-page__table-wrap">
            <table className="admin-page__table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Queries</th>
                  <th>Last Active</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map(user => (
                  <tr key={user.id}>
                    <td>
                      <div className="admin-page__user-cell">
                        <div className="admin-page__user-avatar">
                          {user.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div>
                          <div className="admin-page__user-name">{user.name}</div>
                          <div className="admin-page__user-email">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${user.role === 'admin' ? 'badge-primary' : user.role === 'analyst' ? 'badge-success' : 'badge-warning'}`}>
                        {user.role}
                      </span>
                    </td>
                    <td>
                      <span className={`admin-page__status ${user.status === 'active' ? 'admin-page__status--active' : 'admin-page__status--inactive'}`}>
                        <span className="admin-page__status-dot" />
                        {user.status}
                      </span>
                    </td>
                    <td>{user.queries}</td>
                    <td><span className="admin-page__last-active">{user.lastActive}</span></td>
                    <td>
                      <div className="admin-page__actions">
                        <button className="btn btn-ghost btn-sm" title="Edit"><Edit3 size={14} /></button>
                        <button className="btn btn-ghost btn-sm" title="Reset password"><Key size={14} /></button>
                        <button className="btn btn-danger btn-sm" title="Delete"><Trash2 size={14} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="admin-page__content animate-fade-in">
          <div className="admin-page__security-list">
            {SECURITY_LOGS.map((log, i) => (
              <div key={i} className="admin-page__security-item card" style={{ animationDelay: `${i * 0.05}s` }}>
                <div className={`admin-page__severity admin-page__severity--${log.severity}`}>
                  <AlertTriangle size={16} />
                </div>
                <div className="admin-page__security-info">
                  <div className="admin-page__security-event">{log.event}</div>
                  <div className="admin-page__security-meta">
                    User: {log.user} · {log.time}
                  </div>
                </div>
                <span className={`badge ${log.severity === 'critical' ? 'badge-danger' : log.severity === 'high' ? 'badge-warning' : 'badge-primary'}`}>
                  {log.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <div className="admin-page__content animate-fade-in">
          <div className="admin-page__analytics-grid">
            <div className="card">
              <h3>Queries by Role</h3>
              <div className="admin-page__bar-chart">
                {[
                  { label: 'Admin', value: 342, max: 400, color: 'var(--primary-400)' },
                  { label: 'Analyst', value: 815, max: 900, color: 'var(--accent-400)' },
                  { label: 'Viewer', value: 165, max: 900, color: 'var(--cyan-400)' },
                ].map((bar, i) => (
                  <div key={i} className="admin-page__bar-row">
                    <span className="admin-page__bar-label">{bar.label}</span>
                    <div className="admin-page__bar-track">
                      <div
                        className="admin-page__bar-fill"
                        style={{ width: `${(bar.value / bar.max) * 100}%`, background: bar.color, animationDelay: `${i * 0.15}s` }}
                      />
                    </div>
                    <span className="admin-page__bar-value">{bar.value}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="card">
              <h3>Security Summary</h3>
              <div className="admin-page__security-stats">
                <div className="admin-page__sec-stat">
                  <span className="admin-page__sec-stat-value" style={{ color: 'var(--danger-400)' }}>12</span>
                  <span>Critical Events</span>
                </div>
                <div className="admin-page__sec-stat">
                  <span className="admin-page__sec-stat-value" style={{ color: 'var(--warning-400)' }}>34</span>
                  <span>High Severity</span>
                </div>
                <div className="admin-page__sec-stat">
                  <span className="admin-page__sec-stat-value" style={{ color: 'var(--primary-400)' }}>67</span>
                  <span>Medium</span>
                </div>
                <div className="admin-page__sec-stat">
                  <span className="admin-page__sec-stat-value" style={{ color: 'var(--accent-400)' }}>1,134</span>
                  <span>Queries Validated</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
