import { useState, useEffect } from 'react';
import { getSettings, updateSettings, submitRoleRequest, getMyRoleRequests } from '../context/api';
import { useAuth } from '../context/AuthContext';
import './SettingsPage.css';

/**
 * Custom sliding toggle component
 * 40×22px, crimson when on, grey when off, thumb slides on real state
 */
function Toggle({ checked, onChange }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      className={`settings-toggle-track ${checked ? 'settings-toggle-track--on' : 'settings-toggle-track--off'}`}
      onClick={() => onChange(!checked)}
    >
      <span className="settings-toggle-thumb" />
    </button>
  );
}

/**
 * Screen 11 — Settings
 * Spec: Section 6 Screen 11
 */
export default function SettingsPage() {
  const { user, updateUser } = useAuth();

  // --- Query / app preferences from backend ---
  const [settings, setSettings] = useState({
    confirmUpdates: true,
    confirmDeletes: true,
    rowLimit: 1000,
    queryTimeout: 30,
  });
  const [loadingSettings, setLoadingSettings] = useState(true);

  // --- Profile editable fields ---
  const [draftName, setDraftName] = useState('');
  const [savedName, setSavedName] = useState('');

  // --- Role Request State ---
  const [myRoleRequests, setMyRoleRequests] = useState([]);
  const [roleRequestRole, setRoleRequestRole] = useState('analyst');
  const [roleRequestReason, setRoleRequestReason] = useState('');
  const [roleRequestLoading, setRoleRequestLoading] = useState(false);
  const [roleRequestMsg, setRoleRequestMsg] = useState(null);

  // --- Save state ---
  const [saving, setSaving]       = useState(false);
  const [saveMsg, setSaveMsg]     = useState(null); // { type: 'success'|'error', text }

  // Populate profile from auth context once loaded
  useEffect(() => {
    if (user) {
      setDraftName(user.name || '');
      setSavedName(user.name || '');
    }
  }, [user]);

  // Load app settings from backend
  useEffect(() => {
    getSettings()
      .then((data) => {
        setSettings({
          confirmUpdates: data.confirmUpdates ?? true,
          confirmDeletes: data.confirmDeletes ?? true,
          rowLimit: data.row_limit ?? data.rowLimit ?? 1000,
          queryTimeout: data.query_timeout ?? data.queryTimeout ?? 30,
        });
      })
      .catch(() => {/* keep defaults */})
      .finally(() => setLoadingSettings(false));
  }, []);

  // Load own role requests for non-admin users
  useEffect(() => {
    if (user && user.role !== 'admin') {
      getMyRoleRequests().then(setMyRoleRequests).catch(() => {});
    }
  }, [user]);

  const handleToggle = (key) => {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSelect = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: Number(value) }));
  };

  const hasChanges =
    draftName.trim() !== savedName ||
    true; // always allow saving settings preferences

  const handleSave = async () => {
    if (saving) return;

    const trimmedName = draftName.trim();
    if (!trimmedName) {
      setSaveMsg({ type: 'error', text: 'Name cannot be empty.' });
      return;
    }

    setSaving(true);
    setSaveMsg(null);

    try {
      // 1. Persist name if changed
      if (trimmedName !== savedName) {
        const result = await updateUser(trimmedName);
        if (!result.success) {
          setSaveMsg({ type: 'error', text: result.error || 'Failed to update name.' });
          setSaving(false);
          return;
        }
        setSavedName(trimmedName);
      }

      // 2. Persist query preferences
      await updateSettings({
        confirmUpdates: settings.confirmUpdates,
        confirmDeletes: settings.confirmDeletes,
        rowLimit: settings.rowLimit,
        queryTimeout: settings.queryTimeout,
      });

      setSaveMsg({ type: 'success', text: 'Settings saved successfully.' });
    } catch (err) {
      setSaveMsg({ type: 'error', text: err.message || 'Failed to save settings.' });
    } finally {
      setSaving(false);
    }
  };

  const handleDiscard = () => {
    setDraftName(savedName);
    setSaveMsg(null);
  };

  const isLoading = loadingSettings || !user;

  return (
    <div className="settings-viewport">
      <header className="settings-header">
        <h2>Settings</h2>
        <p>QueryMind preferences</p>
      </header>

      {isLoading ? (
        <div style={{ padding: '28px 36px', color: 'rgba(224,224,230,0.32)', fontSize: 13 }}>Loading…</div>
      ) : (
        <div className="settings-body">
          {/* ── Section 1: Query Behaviour ──────────────────────── */}
          <div>
            <span className="settings-section-label">Query Behaviour</span>
            <div className="settings-card">
              <div className="settings-row">
                <div className="settings-row-left">
                  <span className="settings-row-label">Confirm before updates</span>
                  <span className="settings-row-hint">Show a preview before executing UPDATE operations</span>
                </div>
                <Toggle
                  checked={settings.confirmUpdates}
                  onChange={() => handleToggle('confirmUpdates')}
                />
              </div>

              <div className="settings-row">
                <div className="settings-row-left">
                  <span className="settings-row-label">Confirm before deletes</span>
                  <span className="settings-row-hint">Show a warning before executing DELETE operations</span>
                </div>
                <Toggle
                  checked={settings.confirmDeletes}
                  onChange={() => handleToggle('confirmDeletes')}
                />
              </div>

              <div className="settings-row">
                <div className="settings-row-left">
                  <span className="settings-row-label">Result row limit</span>
                  <span className="settings-row-hint">Maximum records returned per query</span>
                </div>
                <select
                  className="settings-select"
                  value={settings.rowLimit}
                  onChange={(e) => handleSelect('rowLimit', e.target.value)}
                >
                  {[50, 100, 250, 500, 1000].map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
              </div>

              <div className="settings-row">
                <div className="settings-row-left">
                  <span className="settings-row-label">Query timeout</span>
                  <span className="settings-row-hint">Seconds before a slow query is cancelled</span>
                </div>
                <select
                  className="settings-select"
                  value={settings.queryTimeout}
                  onChange={(e) => handleSelect('queryTimeout', e.target.value)}
                >
                  {[15, 30, 60, 120].map((v) => (
                    <option key={v} value={v}>{v}s</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* ── Section 2: Account ──────────────────────────────── */}
          <div>
            <span className="settings-section-label">Account</span>
            <div className="settings-card">
              <div className="settings-row">
                <span className="settings-row-label">Name</span>
                <input
                  className="settings-input"
                  type="text"
                  value={draftName}
                  onChange={(e) => { setDraftName(e.target.value); setSaveMsg(null); }}
                  placeholder="Your full name"
                  style={{
                    background: 'transparent',
                    border: '1px solid rgba(224,224,230,0.15)',
                    borderRadius: 6,
                    color: 'rgba(224,224,230,0.9)',
                    fontSize: 13,
                    padding: '5px 10px',
                    outline: 'none',
                    minWidth: 180,
                  }}
                />
              </div>
              <div className="settings-row">
                <span className="settings-row-label">Email</span>
                <span className="settings-mono-value">{user?.email || '—'}</span>
              </div>
              <div className="settings-row">
                <span className="settings-row-label">Role</span>
                <span className="settings-role-badge" style={{ textTransform: 'capitalize' }}>
                  {user?.role || '—'}
                </span>
              </div>
            </div>
          </div>

          {/* ── Section 2b: Request Role (non-admin only) ──────── */}
          {user?.role !== 'admin' && (
            <div>
              <span className="settings-section-label">Request Role Elevation</span>
              <div className="settings-card">
                {myRoleRequests.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    {myRoleRequests.slice(0, 3).map((rr) => (
                      <div key={rr.id} style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        padding: '8px 0', borderBottom: '1px solid rgba(224,224,230,0.08)', fontSize: 13
                      }}>
                        <span style={{ color: 'rgba(224,224,230,0.7)' }}>
                          Request for <strong style={{ color: '#feefb8' }}>{rr.requested_role}</strong>
                        </span>
                        <span style={{
                          fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 12,
                          background: rr.status === 'approved' ? 'rgba(34,197,94,0.15)'
                            : rr.status === 'rejected' ? 'rgba(248,113,113,0.15)'
                            : 'rgba(241,196,15,0.15)',
                          color: rr.status === 'approved' ? '#22c55e'
                            : rr.status === 'rejected' ? '#f87171'
                            : '#f1c40f',
                        }}>
                          {rr.status.toUpperCase()}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {!myRoleRequests.some((r) => r.status === 'pending') ? (
                  <>
                    <div className="settings-row">
                      <div className="settings-row-left">
                        <span className="settings-row-label">Requested role</span>
                        <span className="settings-row-hint">Choose the role you need access to</span>
                      </div>
                      <select
                        className="settings-select"
                        value={roleRequestRole}
                        onChange={(e) => setRoleRequestRole(e.target.value)}
                      >
                        {user?.role !== 'analyst' && <option value="analyst">Analyst</option>}
                        <option value="admin">Admin</option>
                      </select>
                    </div>
                    <div className="settings-row" style={{ alignItems: 'flex-start', flexDirection: 'column', gap: 8 }}>
                      <span className="settings-row-label">
                        Reason <span style={{ color: 'rgba(224,224,230,0.4)', fontWeight: 400 }}>(optional)</span>
                      </span>
                      <textarea
                        rows={2}
                        placeholder="Briefly explain why you need this access..."
                        value={roleRequestReason}
                        onChange={(e) => setRoleRequestReason(e.target.value)}
                        style={{
                          width: '100%', background: 'rgba(0,0,0,0.25)', color: 'rgba(224,224,230,0.9)',
                          border: '1px solid rgba(224,224,230,0.15)', borderRadius: 6, fontSize: 13,
                          padding: '7px 10px', outline: 'none', resize: 'none', boxSizing: 'border-box'
                        }}
                      />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 4 }}>
                      <button
                        type="button"
                        disabled={roleRequestLoading}
                        onClick={async () => {
                          setRoleRequestLoading(true);
                          setRoleRequestMsg(null);
                          try {
                            await submitRoleRequest(roleRequestRole, roleRequestReason);
                            setRoleRequestMsg({ type: 'success', text: 'Request submitted. An admin will review it shortly.' });
                            setRoleRequestReason('');
                            const updated = await getMyRoleRequests();
                            setMyRoleRequests(updated);
                          } catch (err) {
                            setRoleRequestMsg({ type: 'error', text: err.message || 'Failed to submit request.' });
                          } finally {
                            setRoleRequestLoading(false);
                          }
                        }}
                        style={{
                          background: roleRequestLoading ? 'rgba(220,38,38,0.5)' : '#dc2626',
                          color: '#fff', border: 'none', borderRadius: 8,
                          padding: '8px 18px', fontSize: 13, fontWeight: 600,
                          cursor: roleRequestLoading ? 'not-allowed' : 'pointer',
                        }}
                      >
                        {roleRequestLoading ? 'Submitting…' : 'Submit Request'}
                      </button>
                      {roleRequestMsg && (
                        <span style={{ fontSize: 13, color: roleRequestMsg.type === 'success' ? '#22c55e' : '#f87171', fontWeight: 500 }}>
                          {roleRequestMsg.type === 'success' ? '✓ ' : '✕ '}{roleRequestMsg.text}
                        </span>
                      )}
                    </div>
                  </>
                ) : (
                  <p style={{ color: 'rgba(241,196,15,0.8)', fontSize: 13, margin: 0 }}>
                    ⏳ You have a pending request. Please wait for admin review before submitting another.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* ── Save / Discard ───────────────────────────────────── */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 4 }}>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              style={{
                background: saving ? 'rgba(220,38,38,0.5)' : '#dc2626',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                padding: '9px 22px',
                fontSize: 13,
                fontWeight: 600,
                cursor: saving ? 'not-allowed' : 'pointer',
                opacity: saving ? 0.7 : 1,
                transition: 'opacity 0.15s',
              }}
            >
              {saving ? 'Saving…' : 'Save Changes'}
            </button>

            {draftName.trim() !== savedName && !saving && (
              <button
                type="button"
                onClick={handleDiscard}
                style={{
                  background: 'transparent',
                  color: 'rgba(224,224,230,0.5)',
                  border: '1px solid rgba(224,224,230,0.15)',
                  borderRadius: 8,
                  padding: '9px 18px',
                  fontSize: 13,
                  cursor: 'pointer',
                }}
              >
                Discard
              </button>
            )}

            {saveMsg && (
              <span
                style={{
                  fontSize: 13,
                  color: saveMsg.type === 'success' ? '#22c55e' : '#f87171',
                  fontWeight: 500,
                }}
              >
                {saveMsg.type === 'success' ? '✓ ' : '✕ '}{saveMsg.text}
              </span>
            )}
          </div>

          {/* ── Section 3: About ────────────────────────────────── */}
          <div>
            <span className="settings-section-label">About</span>
            <div className="settings-card">
              <div className="settings-row">
                <span className="settings-row-label">Version</span>
                <span className="settings-mono-value" style={{ color: 'rgba(224,224,230,0.28)' }}>
                  v0.1.0-alpha
                </span>
              </div>
              <div className="settings-row" style={{ borderBottom: 'none' }}>
                <p className="settings-about-footer">
                  MSc IT Application Development Project · 2026
                  <br />
                  Natural language database assistant · MongoDB + MySQL
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
