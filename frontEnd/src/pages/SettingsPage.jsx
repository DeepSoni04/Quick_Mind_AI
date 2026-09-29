import { useState, useEffect } from 'react';
import { getSettings, updateSettings } from '../context/api';
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

  return (
    <div className="settings-viewport">
      <header className="settings-header">
        <h2>Settings</h2>
        <p>QueryMind preferences</p>
      </header>

      {loading ? (
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
                  {[50, 100, 250, 500].map((v) => (
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
                <span className="settings-mono-value">Heer Sachdev</span>
              </div>
              <div className="settings-row">
                <span className="settings-row-label">Email</span>
                <span className="settings-mono-value">heer@college.edu</span>
              </div>
              <div className="settings-row">
                <span className="settings-row-label">Role</span>
                <span className="settings-role-badge">Analyst</span>
              </div>
            </div>
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
                  Natural language database assistant · MongoDB
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
