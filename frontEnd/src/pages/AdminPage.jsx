import { useState } from 'react';
import { getMockUsers, setMockUsers } from '../context/AuthContext';
import './AdminPage.css';

// Icons as inline SVGs to avoid any dependency issues
const IconShield  = () => <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M9 1.5L15 4.5v4c0 4-6 7.5-6 7.5S3 12.5 3 8.5v-4z"/><polyline points="6.5 9 8.5 11 12 7.5"/></svg>;
const IconUsers   = () => <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="5.5" cy="5" r="2.5"/><path d="M1 14c0-2.5 2-4 4.5-4s4.5 1.5 4.5 4"/><circle cx="11.5" cy="5" r="2"/><path d="M14 13.5c0-2-1.5-3.5-3-3.5"/></svg>;
const IconLogs    = () => <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M2 2h12v12H2z"/><line x1="5" y1="6" x2="11" y2="6"/><line x1="5" y1="9" x2="9" y2="9"/></svg>;
const IconSearch  = () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><circle cx="6" cy="6" r="4"/><line x1="9" y1="9" x2="12.5" y2="12.5"/></svg>;
const IconEdit    = () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M9.5 1.5l2 2-7 7H2.5V9l7-7.5z"/></svg>;
const IconKey     = () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="5" cy="5" r="3"/><line x1="7" y1="7" x2="11" y2="11"/><line x1="9" y1="9" x2="11" y2="7"/></svg>;
const IconTrash   = () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="2 3.5 11 3.5"/><path d="M4.5 3.5V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5v1M10 3.5l-.8 7.5a.5.5 0 0 1-.5.5H4.3a.5.5 0 0 1-.5-.5L3 3.5"/></svg>;
const IconAlert   = () => <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M7.5 1L14 13H1z"/><line x1="7.5" y1="6" x2="7.5" y2="9"/><circle cx="7.5" cy="11" r="0.6" fill="currentColor" stroke="none"/></svg>;
const IconPlus    = () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"><line x1="7" y1="2" x2="7" y2="12"/><line x1="2" y1="7" x2="12" y2="7"/></svg>;
const IconCheck   = () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 7l4 4 5-6"/></svg>;

const INITIAL_SECURITY_LOGS = [
  { id: 1, time: '19:22', event: 'Blocked destructive query: DROP TABLE',    user: 'Neel Shah',     severity: 'high' },
  { id: 2, time: '18:45', event: 'SQL injection pattern detected',            user: 'Unknown',       severity: 'critical' },
  { id: 3, time: '17:30', event: 'Role escalation attempt blocked',           user: 'Guest User',    severity: 'high' },
  { id: 4, time: '16:10', event: 'Query timeout enforced (30s limit)',         user: 'Parshwa Jain',  severity: 'medium' },
  { id: 5, time: '15:45', event: 'Unauthorized table access blocked',          user: 'Nishit Gal',    severity: 'medium' },
  { id: 6, time: '14:20', event: 'Failed login attempt (3rd try)',             user: 'Unknown',       severity: 'high' },
  { id: 7, time: '13:05', event: 'Password reset triggered',                  user: 'Heer Sachdev',  severity: 'low' },
];

const ROLES = ['admin', 'analyst', 'viewer'];

function makeAvatar(name = '') {
  const parts = name.trim().split(/\s+/);
  return (parts[0]?.[0] || '?').toUpperCase() + (parts[1]?.[0] || '').toUpperCase();
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers]         = useState(() => getMockUsers().map((u) => ({ ...u, status: u.status || 'active' })));
  const [search, setSearch]       = useState('');
  const [securityLogs, setSecurityLogs] = useState(INITIAL_SECURITY_LOGS);

  // Edit state
  const [editingId, setEditingId] = useState(null);
  const [editRole, setEditRole]   = useState('');

  // Add User form state
  const [showAddUser, setShowAddUser] = useState(false);
  const [addForm, setAddForm]         = useState({ name: '', email: '', role: 'analyst' });
  const [addError, setAddError]       = useState('');

  // Reset password feedback
  const [resetDone, setResetDone] = useState({});

  const filtered = users.filter(
    (u) => u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase())
  );

  /* ── User actions ── */
  const startEdit = (u) => { setEditingId(u.id); setEditRole(u.role); };

  const saveEdit = (id) => {
    const updated = users.map((u) => u.id === id ? { ...u, role: editRole } : u);
    setUsers(updated);
    setMockUsers(updated);
    setEditingId(null);
    // Log event
    const u = users.find((x) => x.id === id);
    setSecurityLogs((prev) => [{ id: Date.now(), time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }), event: `Role changed to ${editRole}`, user: u?.name || 'Unknown', severity: 'low' }, ...prev]);
  };

  const handleResetPassword = (u) => {
    setResetDone((prev) => ({ ...prev, [u.id]: true }));
    setSecurityLogs((prev) => [{ id: Date.now(), time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }), event: 'Password reset triggered', user: u.name, severity: 'low' }, ...prev]);
    setTimeout(() => setResetDone((prev) => ({ ...prev, [u.id]: false })), 2500);
  };

  const handleDelete = (id) => {
    if (!window.confirm('Delete this user? This cannot be undone.')) return;
    const deleted = users.find((u) => u.id === id);
    const updated = users.filter((u) => u.id !== id);
    setUsers(updated);
    setMockUsers(updated);
    setSecurityLogs((prev) => [{ id: Date.now(), time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }), event: 'User deleted', user: deleted?.name || 'Unknown', severity: 'high' }, ...prev]);
  };

  const handleAddUser = (e) => {
    e.preventDefault();
    if (!addForm.name.trim() || !addForm.email.trim()) { setAddError('Name and email are required.'); return; }
    if (users.find((u) => u.email.toLowerCase() === addForm.email.toLowerCase())) { setAddError('A user with that email already exists.'); return; }
    const newUser = { id: Date.now(), name: addForm.name.trim(), email: addForm.email.trim(), role: addForm.role, status: 'active', queries: 0, lastActive: 'Just now' };
    const updated = [...users, newUser];
    setUsers(updated);
    setMockUsers(updated);
    setShowAddUser(false);
    setAddForm({ name: '', email: '', role: 'analyst' });
    setAddError('');
  };

  const TABS = [
    { id: 'users',    label: 'Users',         Icon: IconUsers },
    { id: 'security', label: 'Security Logs',  Icon: IconLogs  },
  ];

  const severityColor = { critical: 'var(--text-red)', high: 'rgba(243,156,18,0.85)', medium: 'rgba(74,158,186,0.75)', low: 'rgba(42,157,92,0.75)' };

  return (
    <div className="admin-page">
      {/* ── Header ── */}
      <header className="admin-page__header">
        <div>
          <h1><IconShield /> Admin Panel</h1>
          <p>Manage users, security, and system settings</p>
        </div>
        <button className="admin-page__add-btn" onClick={() => setShowAddUser(true)}>
          <IconPlus /> Add User
        </button>
      </header>

      {/* ── Add User inline form ── */}
      {showAddUser && (
        <div className="admin-page__add-form-wrap" style={{ animation: 'slideUp 0.3s ease-out both' }}>
          <form className="admin-page__add-form" onSubmit={handleAddUser}>
            <span className="admin-page__add-form-title">New User</span>
            <input
              className="admin-page__input" placeholder="Full Name"
              value={addForm.name} onChange={(e) => setAddForm((p) => ({ ...p, name: e.target.value }))}
            />
            <input
              className="admin-page__input" placeholder="Email" type="email"
              value={addForm.email} onChange={(e) => setAddForm((p) => ({ ...p, email: e.target.value }))}
            />
            <select
              className="admin-page__select"
              value={addForm.role} onChange={(e) => setAddForm((p) => ({ ...p, role: e.target.value }))}
            >
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
            {addError && <span className="admin-page__add-error">{addError}</span>}
            <div className="admin-page__add-buttons">
              <button type="button" className="admin-page__btn-cancel" onClick={() => { setShowAddUser(false); setAddError(''); }}>Cancel</button>
              <button type="submit" className="admin-page__btn-save">Create User</button>
            </div>
          </form>
        </div>
      )}

      {/* ── Tabs ── */}
      <div className="admin-page__tabs">
        {TABS.map(({ id, label, Icon }) => (
          <button
            key={id}
            className={`admin-page__tab ${activeTab === id ? 'admin-page__tab--active' : ''}`}
            onClick={() => setActiveTab(id)}
          >
            <Icon /> {label}
          </button>
        ))}
      </div>

      {/* ── Users Tab ── */}
      {activeTab === 'users' && (
        <div className="admin-page__content">
          <div className="admin-page__toolbar">
            <div className="admin-page__search">
              <IconSearch />
              <input
                className="admin-page__search-input"
                placeholder="Search users…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <span className="admin-page__user-count">{filtered.length} user{filtered.length !== 1 ? 's' : ''}</span>
          </div>

          <div className="admin-page__table-wrap">
            <table className="admin-page__table">
              <thead>
                <tr>
                  <th>User</th><th>Role</th><th>Status</th><th>Queries</th><th>Last Active</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((user) => (
                  <tr key={user.id} style={{ animation: 'fadeRow 0.3s ease-out both' }}>
                    {/* User cell */}
                    <td>
                      <div className="admin-page__user-cell">
                        <div className="admin-page__user-avatar">{makeAvatar(user.name)}</div>
                        <div>
                          <div className="admin-page__user-name">{user.name}</div>
                          <div className="admin-page__user-email">{user.email}</div>
                        </div>
                      </div>
                    </td>

                    {/* Role cell — editable */}
                    <td>
                      {editingId === user.id ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <select
                            className="admin-page__select admin-page__select--inline"
                            value={editRole}
                            onChange={(e) => setEditRole(e.target.value)}
                          >
                            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                          </select>
                          <button className="admin-page__btn-icon admin-page__btn-icon--save" title="Save" onClick={() => saveEdit(user.id)}>
                            <IconCheck />
                          </button>
                        </div>
                      ) : (
                        <span className={`admin-page__role-badge admin-page__role-badge--${user.role}`}>
                          {user.role}
                        </span>
                      )}
                    </td>

                    {/* Status */}
                    <td>
                      <span className={`admin-page__status-chip ${user.status === 'active' ? 'admin-page__status-chip--active' : 'admin-page__status-chip--inactive'}`}>
                        <span className="admin-page__status-dot" />
                        {user.status}
                      </span>
                    </td>

                    <td><span className="admin-page__mono">{user.queries ?? 0}</span></td>
                    <td><span className="admin-page__last-active">{user.lastActive}</span></td>

                    {/* Actions */}
                    <td>
                      <div className="admin-page__actions">
                        {/* Edit */}
                        <button
                          className={`admin-page__btn-icon ${editingId === user.id ? 'admin-page__btn-icon--active' : ''}`}
                          title="Edit role"
                          onClick={() => editingId === user.id ? setEditingId(null) : startEdit(user)}
                        >
                          <IconEdit />
                        </button>

                        {/* Reset Password */}
                        <button
                          className={`admin-page__btn-icon ${resetDone[user.id] ? 'admin-page__btn-icon--done' : ''}`}
                          title="Reset password"
                          onClick={() => handleResetPassword(user)}
                          disabled={!!resetDone[user.id]}
                        >
                          {resetDone[user.id] ? <IconCheck /> : <IconKey />}
                        </button>

                        {/* Delete */}
                        <button
                          className="admin-page__btn-icon admin-page__btn-icon--danger"
                          title="Delete user"
                          onClick={() => handleDelete(user.id)}
                        >
                          <IconTrash />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Security Logs Tab ── */}
      {activeTab === 'security' && (
        <div className="admin-page__content">
          <div className="admin-page__security-list">
            {securityLogs.map((log, i) => (
              <div key={log.id} className="admin-page__security-item" style={{ animation: `fadeRow 0.3s ease-out ${i * 0.04}s both` }}>
                <div className="admin-page__severity-icon" style={{ color: severityColor[log.severity] || 'currentColor' }}>
                  <IconAlert />
                </div>
                <div className="admin-page__security-info">
                  <div className="admin-page__security-event">{log.event}</div>
                  <div className="admin-page__security-meta">{log.user} · {log.time}</div>
                </div>
                <span className={`admin-page__severity-badge admin-page__severity-badge--${log.severity}`}>
                  {log.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
