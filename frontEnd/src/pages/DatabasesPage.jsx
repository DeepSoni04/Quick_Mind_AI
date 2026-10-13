import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getConnections, addConnection, testConnection, disconnectConnection } from '../context/api';
import './DatabasesPage.css';

/**
 * Screen 9 — Connections
 * Spec: Section 6 Screen 9
 */
function ConnectionsScreen() {
  const navigate  = useNavigate();
  const [connections, setConnections] = useState([]);
  const [loading, setLoading]         = useState(true);
  const [showManage, setShowManage]   = useState({});

  useEffect(() => {
    // TODO: replace mock with real API call
    getConnections().then((data) => { setConnections(data); setLoading(false); });
  }, []);

  const toggleManage = (id) =>
    setShowManage((prev) => ({ ...prev, [id]: !prev[id] }));

  const handleDisconnect = async (id) => {
    // TODO: replace mock with real API call
    await disconnectConnection(id);
    setConnections((prev) => prev.filter((c) => c.id !== id));
  };

  const STATS_LABELS = ['Collections', 'Last synced', 'Host', 'Database'];

  return (
    <div className="connections-viewport">
      <header className="connections-header">
        <div className="connections-header-left">
          <h2>Connections</h2>
          <p>Manage your database connections</p>
        </div>
        <button type="button" className="btn-add-connection" onClick={() => navigate('/add-connection')}>
          <svg className="btn-add-connection-svg" viewBox="0 0 14 14" strokeLinecap="round" strokeLinejoin="round">
            <line x1="7" y1="2" x2="7" y2="12" />
            <line x1="2" y1="7" x2="12" y2="7" />
          </svg>
          Add Connection
        </button>
      </header>

      <div className="connections-body">
        {loading && (
          <span style={{ color: 'rgba(224,224,230,0.32)', fontSize: 13 }}>Loading…</span>
        )}

        {!loading && connections.map((conn) => {
          const stats = [
            { label: STATS_LABELS[0], value: String(conn.collectionsCount || 7) },
            { label: STATS_LABELS[1], value: conn.lastSynced || '3 min ago' },
            { label: STATS_LABELS[2], value: conn.host || 'cluster0.mongodb.net' },
            { label: STATS_LABELS[3], value: conn.database || 'college_db' },
          ];

          return (
            <div key={conn.id} className="conn-card">
              <div className="conn-card-top">
                <div className="conn-card-top-left">
                  <div className="conn-status-row">
                    <div className="conn-status-dot" />
                    <span className="conn-status-text">Connected</span>
                  </div>
                  <div className="conn-card-name">{conn.name}</div>
                  <div className="conn-card-type">{conn.type}</div>
                </div>
                <button
                  type="button"
                  className="btn-manage"
                  onClick={() => toggleManage(conn.id)}
                >
                  {showManage[conn.id] ? 'Done' : 'Manage'}
                </button>
              </div>

              {/* Stats grid */}
              <div className="conn-stats-grid">
                {stats.map((s) => (
                  <div key={s.label} className="conn-stat-tile">
                    <span className="conn-stat-label">{s.label}</span>
                    <span className="conn-stat-value">{s.value}</span>
                  </div>
                ))}
              </div>

              {/* Manage panel (toggled via real state) */}
              {showManage[conn.id] && (
                <div className="conn-manage-panel">
                  <button type="button" className="btn-sync">Sync Schema</button>
                  <button
                    type="button"
                    className="btn-disconnect"
                    onClick={() => handleDisconnect(conn.id)}
                  >
                    Disconnect
                  </button>
                </div>
              )}
            </div>
          );
        })}

        {/* Add-another dashed slot */}
        <button
          type="button"
          className="conn-add-slot"
          onClick={() => navigate('/add-connection')}
        >
          <svg className="conn-add-slot-svg" viewBox="0 0 16 16" strokeLinecap="round" strokeLinejoin="round">
            <line x1="8" y1="2" x2="8" y2="14" />
            <line x1="2" y1="8" x2="14" y2="8" />
          </svg>
          Add another connection
        </button>
      </div>
    </div>
  );
}

/**
 * Screen 10 — Add Connection
 * Spec: Section 6 Screen 10
 */
function AddConnectionScreen() {
  const navigate = useNavigate();
  const [formData, setFormData]     = useState({ name: '', connectionString: '', database: '' });
  const [testState, setTestState]   = useState('idle'); // 'idle' | 'testing' | 'success' | 'error'
  const [isConnecting, setIsConnecting] = useState(false);

  const handleField = (e) =>
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleTest = async () => {
    if (testState === 'testing') return;
    setTestState('testing');
    // TODO: replace mock with real API call
    const result = await testConnection(formData);
    setTestState(result.success ? 'success' : 'error');
  };

  const handleConnect = async () => {
    if (isConnecting) return;
    setIsConnecting(true);
    // TODO: replace mock with real API call
    await addConnection(formData);
    setIsConnecting(false);
    navigate('/connections');
  };

  const isTesting = testState === 'testing';

  return (
    <div className="add-conn-viewport">
      {/* Back link */}
      <button type="button" className="add-conn-back" onClick={() => navigate('/connections')}>
        <svg className="add-conn-back-svg" viewBox="0 0 10 10" strokeLinecap="round" strokeLinejoin="round">
          <path d="M7 1L3 5l4 4" />
        </svg>
        Connections
      </button>

      <h2 className="add-conn-title">Add MongoDB Connection</h2>

      <form
        className="add-conn-form"
        onSubmit={(e) => { e.preventDefault(); handleConnect(); }}
      >
        <div className="add-conn-field">
          <label className="add-conn-label">Connection Name</label>
          <input
            className="add-conn-input"
            name="name"
            value={formData.name}
            onChange={handleField}
            placeholder="e.g. Student Database"
          />
        </div>

        <div className="add-conn-field">
          <label className="add-conn-label">Connection String</label>
          <input
            className="add-conn-input"
            name="connectionString"
            value={formData.connectionString}
            onChange={handleField}
            placeholder="mongodb+srv://user:pass@cluster0.mongodb.net"
          />
        </div>

        <div className="add-conn-field">
          <label className="add-conn-label">Database Name</label>
          <input
            className="add-conn-input"
            name="database"
            value={formData.database}
            onChange={handleField}
            placeholder="e.g. college_db"
          />
        </div>

        {/* Database Type: static, non-editable */}
        <div className="add-conn-field">
          <label className="add-conn-label">Database Type</label>
          <div className="add-conn-static">
            <div className="add-conn-static-dot" />
            <span className="add-conn-static-text">MongoDB</span>
          </div>
        </div>

        {/* Test Connection result banner */}
        {testState === 'success' && (
          <div className="add-conn-banner add-conn-banner--success">
            <svg className="banner-svg" viewBox="0 0 14 14" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 7l4 4 6-6" />
            </svg>
            Connection successful — database reachable
          </div>
        )}
        {testState === 'error' && (
          <div className="add-conn-banner add-conn-banner--error">
            <svg className="banner-svg" viewBox="0 0 14 14" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="7" cy="7" r="5.5" />
              <line x1="7" y1="4.5" x2="7" y2="7.5" strokeWidth="1.5" />
              <circle cx="7" cy="9.5" r="0.6" fill="currentColor" stroke="none" />
            </svg>
            Could not connect — check your connection string.
          </div>
        )}

        <div className="add-conn-buttons">
          <button
            type="button"
            className="btn-test-conn"
            onClick={handleTest}
            disabled={isTesting}
          >
            {isTesting ? <><div className="spinner-small" /> Testing…</> : 'Test Connection'}
          </button>
          <button type="submit" className="btn-connect" disabled={isConnecting}>
            {isConnecting ? 'Connecting…' : 'Connect'}
          </button>
        </div>
      </form>
    </div>
  );
}

/**
 * DatabasesPage — Routes to either Connections or Add Connection
 * view prop: 'list' | 'add'
 */
export default function DatabasesPage({ view = 'list' }) {
  if (view === 'add') return <AddConnectionScreen />;
  return <ConnectionsScreen />;
}
