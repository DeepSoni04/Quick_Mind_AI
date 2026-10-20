import { useState, useEffect } from 'react';
<<<<<<< Updated upstream
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getSettings, updateSettings } from '../context/api';
=======
import { getSettings, updateSettings } from '../context/api';
import { useAuth } from '../context/AuthContext';
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
  const navigate = useNavigate();
  const { user } = useAuth();
  const [settings, setSettings] = useState({
    confirmUpdates: true,
    confirmDeletes: true,
    rowLimit: 100,
    queryTimeout: 30,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: replace mock with real API call
    getSettings().then((data) => { setSettings(data); setLoading(false); });
  }, []);

  const handleToggle = async (key) => {
    const updated = { ...settings, [key]: !settings[key] };
    setSettings(updated);
    // TODO: replace mock with real API call
    await updateSettings({ [key]: updated[key] });
  };

  const handleSelect = async (key, value) => {
    const updated = { ...settings, [key]: Number(value) };
    setSettings(updated);
    // TODO: replace mock with real API call
    await updateSettings({ [key]: Number(value) });
  };
=======
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
>>>>>>> Stashed changes

  return (
    <div className="settings-viewport">
      <header className="settings-header">
        <h2>Settings</h2>
        <p>QueryMind preferences</p>
      </header>

<<<<<<< Updated upstream
      {loading ? (
=======
      {isLoading ? (
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
                  {[50, 100, 250, 500].map((v) => (
=======
                  {[50, 100, 250, 500, 1000].map((v) => (
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span className="settings-section-label" style={{ marginBottom: 0 }}>Account</span>
              <button
                type="button"
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-butter)',
                  fontSize: '12px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  padding: '2px 6px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
                onClick={() => navigate('/profile')}
              >
                Manage Profile & Security →
              </button>
            </div>
            <div className="settings-card">
              <div className="settings-row">
                <span className="settings-row-label">Name</span>
                <span className="settings-mono-value">{user?.name || 'Administrator'}</span>
              </div>
              <div className="settings-row">
                <span className="settings-row-label">Email</span>
                <span className="settings-mono-value">{user?.email || 'admin@querymind.ai'}</span>
=======
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
>>>>>>> Stashed changes
              </div>
              <div className="settings-row">
                <span className="settings-row-label">Role</span>
                <span className="settings-role-badge" style={{ textTransform: 'capitalize' }}>
<<<<<<< Updated upstream
                  {user?.role || 'Viewer'}
=======
                  {user?.role || '—'}
>>>>>>> Stashed changes
                </span>
              </div>
            </div>
          </div>

<<<<<<< Updated upstream
=======
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

>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
                  Natural language database assistant · MongoDB
=======
                  Natural language database assistant · MongoDB + MySQL
>>>>>>> Stashed changes
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
