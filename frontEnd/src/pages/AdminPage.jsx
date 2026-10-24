import { useState, useEffect } from 'react';
import { getAdminUsers, updateUserRole, resetUserPassword, deleteUser, getSecurityLogs, getAdminRoleRequests, approveRoleRequest, rejectRoleRequest } from '../context/api';
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



const ROLES = ['admin', 'analyst', 'viewer'];

function makeAvatar(name = '') {
  const parts = name.trim().split(/\s+/);
  return (parts[0]?.[0] || '?').toUpperCase() + (parts[1]?.[0] || '').toUpperCase();
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers]         = useState([]);
  const [search, setSearch]       = useState('');
  const [securityLogs, setSecurityLogs] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);

  // Role request state
  const [roleRequests, setRoleRequests]         = useState([]);
  const [roleReqFilter, setRoleReqFilter]       = useState('pending');
  const [roleReqLoading, setRoleReqLoading]     = useState(false);
  const [roleReqActionMsg, setRoleReqActionMsg] = useState({});

  // Edit state
  const [editingId, setEditingId] = useState(null);
  const [editRole, setEditRole]   = useState('');

  // Add User form state
  const [showAddUser, setShowAddUser] = useState(false);
  const [addForm, setAddForm]         = useState({ name: '', email: '', role: 'analyst' });
  const [addError, setAddError]       = useState('');

  // Reset password feedback
  const [resetDone, setResetDone] = useState({});

  // Load users, security logs, and role requests on mount
  useEffect(() => {
    setLoadingUsers(true);
    getAdminUsers()
      .then((data) => setUsers(Array.isArray(data) ? data : []))
      .catch(() => setUsers([]))
      .finally(() => setLoadingUsers(false));

    getSecurityLogs()
      .then((data) => setSecurityLogs(Array.isArray(data) ? data : []))
      .catch(() => setSecurityLogs([]));

    loadRoleRequests('pending');
  }, []);

  const loadRoleRequests = (filter) => {
    setRoleReqLoading(true);
    setRoleReqFilter(filter);
    getAdminRoleRequests(filter)
      .then((data) => setRoleRequests(Array.isArray(data) ? data : []))
      .catch(() => setRoleRequests([]))
      .finally(() => setRoleReqLoading(false));
  };

  const handleApproveRequest = async (id) => {
    setRoleReqActionMsg((m) => ({ ...m, [id]: { type: 'loading', text: 'Approving…' } }));
    try {
      await approveRoleRequest(id);
      setRoleReqActionMsg((m) => ({ ...m, [id]: { type: 'success', text: '✓ Approved' } }));
      setRoleRequests((prev) => prev.map((r) => r.id === id ? { ...r, status: 'approved' } : r));
    } catch (err) {
      setRoleReqActionMsg((m) => ({ ...m, [id]: { type: 'error', text: `Error: ${err.message}` } }));
    }
  };

  const handleRejectRequest = async (id) => {
    setRoleReqActionMsg((m) => ({ ...m, [id]: { type: 'loading', text: 'Rejecting…' } }));
    try {
      await rejectRoleRequest(id);
      setRoleReqActionMsg((m) => ({ ...m, [id]: { type: 'success', text: '✓ Rejected' } }));
      setRoleRequests((prev) => prev.map((r) => r.id === id ? { ...r, status: 'rejected' } : r));
    } catch (err) {
      setRoleReqActionMsg((m) => ({ ...m, [id]: { type: 'error', text: `Error: ${err.message}` } }));
    }
  };


  const filtered = users.filter(
    (u) => u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase())
  );

  /* ── User actions ── */
  const startEdit = (u) => { setEditingId(u.id); setEditRole(u.role); };

  const saveEdit = async (id) => {
    try {
      await updateUserRole(id, editRole);
      setUsers((prev) => prev.map((u) => u.id === id ? { ...u, role: editRole } : u));
      setEditingId(null);
    } catch (err) {
      alert(`Failed to update role: ${err.message}`);
    }
  };

  const handleResetPassword = async (u) => {
    try {
      await resetUserPassword(u.id);
      setResetDone((prev) => ({ ...prev, [u.id]: true }));
      setTimeout(() => setResetDone((prev) => ({ ...prev, [u.id]: false })), 2500);
    } catch (err) {
      alert(`Reset failed: ${err.message}`);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this user? This cannot be undone.')) return;
    try {
      await deleteUser(id);
      setUsers((prev) => prev.filter((u) => u.id !== id));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleAddUser = (e) => {
    e.preventDefault();
    setAddError('User creation via the admin panel is not yet supported through the API. Users must register directly.');
  };

  const TABS = [
    { id: 'users',    label: 'Users',         Icon: IconUsers },
    { id: 'requests', label: 'Role Requests',  Icon: IconAlert, badge: roleRequests.filter((r) => r.status === 'pending').length || null },
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
        {TABS.map(({ id, label, Icon, badge }) => (
          <button
            key={id}
            className={`admin-page__tab ${activeTab === id ? 'admin-page__tab--active' : ''}`}
            onClick={() => { setActiveTab(id); if (id === 'requests') loadRoleRequests(roleReqFilter); }}
            style={{ position: 'relative' }}
          >
            <Icon /> {label}
            {badge > 0 && (
              <span style={{
                position: 'absolute', top: 4, right: 4, background: '#dc2626', color: '#fff',
                fontSize: 10, fontWeight: 700, borderRadius: '50%', width: 16, height: 16,
                display: 'flex', alignItems: 'center', justifyContent: 'center', lineHeight: 1,
              }}>{badge}</span>
            )}
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

      {/* ── Role Requests Tab ── */}
      {activeTab === 'requests' && (
        <div className="admin-page__content">
          <div className="admin-page__toolbar" style={{ marginBottom: 16 }}>
            {['pending', 'approved', 'rejected', 'all'].map((f) => (
              <button
                key={f}
                onClick={() => loadRoleRequests(f)}
                style={{
                  padding: '5px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                  border: 'none', cursor: 'pointer', textTransform: 'capitalize',
                  background: roleReqFilter === f ? '#dc2626' : 'rgba(255,255,255,0.07)',
                  color: roleReqFilter === f ? '#fff' : 'rgba(224,224,230,0.7)',
                  marginRight: 6,
                }}
              >
                {f}
              </button>
            ))}
          </div>

          {roleReqLoading && (
            <p style={{ color: 'rgba(224,224,230,0.5)', fontSize: 13, textAlign: 'center', padding: '32px 0' }}>Loading…</p>
          )}
          {!roleReqLoading && roleRequests.length === 0 && (
            <p style={{ color: 'rgba(224,224,230,0.4)', fontSize: 13, textAlign: 'center', padding: '48px 0' }}>
              No {roleReqFilter === 'all' ? '' : roleReqFilter} role requests found.
            </p>
          )}

          {!roleReqLoading && roleRequests.map((req) => {
            const msg = roleReqActionMsg[req.id];
            const isPending = req.status === 'pending';
            return (
              <div key={req.id} style={{
                background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(224,224,230,0.08)',
                borderRadius: 10, padding: '14px 18px', marginBottom: 10,
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
                animation: 'fadeRow 0.3s ease-out both',
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                    <div className="admin-page__user-avatar" style={{ width: 30, height: 30, fontSize: 12 }}>
                      {makeAvatar(req.user_name)}
                    </div>
                    <div>
                      <span style={{ color: 'rgba(224,224,230,0.9)', fontWeight: 600, fontSize: 14 }}>
                        {req.user_name}
                      </span>
                      <span style={{ color: 'rgba(224,224,230,0.45)', fontSize: 12, marginLeft: 8 }}>
                        {req.user_email}
                      </span>
                    </div>
                  </div>
                  <div style={{ fontSize: 13, color: 'rgba(224,224,230,0.65)', paddingLeft: 40 }}>
                    Requesting role → <strong style={{ color: '#feefb8' }}>{req.requested_role}</strong>
                    {req.reason && <span style={{ marginLeft: 10, fontStyle: 'italic' }}>"{req.reason}"</span>}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                  {!isPending && (
                    <span style={{
                      fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 12,
                      background: req.status === 'approved' ? 'rgba(34,197,94,0.15)' : 'rgba(248,113,113,0.15)',
                      color: req.status === 'approved' ? '#22c55e' : '#f87171',
                    }}>
                      {req.status.toUpperCase()}
                    </span>
                  )}
                  {msg ? (
                    <span style={{
                      fontSize: 12, fontWeight: 600,
                      color: msg.type === 'success' ? '#22c55e' : msg.type === 'error' ? '#f87171' : 'rgba(224,224,230,0.5)',
                    }}>{msg.text}</span>
                  ) : isPending ? (
                    <>
                      <button
                        onClick={() => handleApproveRequest(req.id)}
                        style={{
                          background: 'rgba(34,197,94,0.15)', color: '#22c55e',
                          border: '1px solid rgba(34,197,94,0.3)',
                          borderRadius: 7, padding: '5px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                        }}
                      >✓ Approve</button>
                      <button
                        onClick={() => handleRejectRequest(req.id)}
                        style={{
                          background: 'rgba(248,113,113,0.12)', color: '#f87171',
                          border: '1px solid rgba(248,113,113,0.3)',
                          borderRadius: 7, padding: '5px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                        }}
                      >✕ Reject</button>
                    </>
                  ) : null}
                </div>
              </div>
            );
          })}
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
