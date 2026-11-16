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
    getConnections().then((data) => { setConnections(data); setLoading(false); });
  }, []);

  const toggleManage = (id) =>
    setShowManage((prev) => ({ ...prev, [id]: !prev[id] }));

  const handleDisconnect = async (id) => {
    await disconnectConnection(id);
    setConnections((prev) => prev.filter((c) => c.id !== id));
  };

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
  const dbTypeLabel = conn.db_type === 'mongodb' ? 'MongoDB'
            : conn.db_type === 'postgresql' ? 'PostgreSQL'
            : 'MySQL';
          const stats = conn.db_type === 'mongodb'
            ? [
                { label: 'Collections', value: String(conn.collectionsCount || conn.collections_count || 0) },
                { label: 'Last synced',  value: conn.lastSynced || conn.last_synced || '—' },
                { label: 'Database',     value: conn.database_name || conn.database || '—' },
                { label: 'Type',         value: dbTypeLabel },
              ]
            : [
                { label: 'Tables',      value: String(conn.collectionsCount || conn.collections_count || 0) },
                { label: 'Last synced', value: conn.lastSynced || conn.last_synced || '—' },
                { label: 'Host',        value: conn.host || '—' },
                { label: 'Database',    value: conn.database_name || conn.database || '—' },
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
                  <div className="conn-card-type">{dbTypeLabel}</div>
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

              {/* Manage panel */}
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
 * Supports both MongoDB (URI-based) and MySQL (host/port/credentials).
 */
function AddConnectionScreen() {
  const navigate = useNavigate();

  // --- Database type ---
  const [dbType, setDbType] = useState('mongodb'); // 'mongodb' | 'mysql' | 'postgresql'

  // --- Shared field ---
  const [connName, setConnName] = useState('');

  // --- MongoDB fields ---
  const [mongoUri, setMongoUri] = useState('');
  const [mongoDb,  setMongoDb]  = useState('');

  // --- MySQL fields ---
  const [mysqlHost, setMysqlHost] = useState('');
  const [mysqlPort, setMysqlPort] = useState('3306');
  const [mysqlDb,   setMysqlDb]   = useState('');
  const [mysqlUser, setMysqlUser] = useState('');
  const [mysqlPass, setMysqlPass] = useState('');

  // --- PostgreSQL fields ---
  const [pgHost, setPgHost] = useState('');
  const [pgPort, setPgPort] = useState('5432');
  const [pgDb,   setPgDb]   = useState('');
  const [pgUser, setPgUser] = useState('');
  const [pgPass, setPgPass] = useState('');

  // --- UI state ---
  const [testState,    setTestState]    = useState('idle'); // idle | testing | success | error
  const [testMsg,      setTestMsg]      = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectError, setConnectError] = useState('');

  // Clear test result when db type changes
  const handleTypeChange = (type) => {
    setDbType(type);
    setTestState('idle');
    setTestMsg('');
    setConnectError('');
  };

  const buildPayload = () => {
    if (dbType === 'mongodb') {
      return {
        name: connName,
        db_type: 'mongodb',
        connection_string: mongoUri,
        database_name: mongoDb || undefined,
      };
    }
    if (dbType === 'postgresql') {
      return {
        name: connName,
        db_type: 'postgresql',
        host: pgHost,
        port: parseInt(pgPort, 10) || 5432,
        database_name: pgDb,
        username: pgUser,
        password: pgPass,
      };
    }
    return {
      name: connName,
      db_type: 'mysql',
      host: mysqlHost,
      port: parseInt(mysqlPort, 10) || 3306,
      database_name: mysqlDb,
      username: mysqlUser,
      password: mysqlPass,
    };
  };

  const handleTest = async () => {
    if (testState === 'testing') return;
    setTestState('testing');
    setTestMsg('');
    const result = await testConnection(buildPayload());
    setTestState(result.success ? 'success' : 'error');
    setTestMsg(result.message || '');
  };

  const handleConnect = async () => {
    if (isConnecting) return;
    setIsConnecting(true);
    setConnectError('');
    const result = await addConnection(buildPayload());
    setIsConnecting(false);
    if (result.success) {
      navigate('/connections');
    } else {
      setConnectError(result.message || 'Failed to save connection.');
    }
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

      <h2 className="add-conn-title">Add Database Connection</h2>

      <form
        className="add-conn-form"
        onSubmit={(e) => { e.preventDefault(); handleConnect(); }}
      >
        {/* ── Connection Name ── */}
        <div className="add-conn-field">
          <label className="add-conn-label">Connection Name</label>
          <input
            className="add-conn-input"
            name="name"
            value={connName}
            onChange={(e) => setConnName(e.target.value)}
            placeholder="e.g. Student Database"
            required
          />
        </div>

        {/* ── Database Type Selector ── */}
        <div className="add-conn-field">
          <label className="add-conn-label">Database Type</label>
          <div style={{ display: 'flex', gap: 10 }}>
            {['mongodb', 'mysql', 'postgresql'].map((type) => {
              const label = type === 'mongodb' ? 'MongoDB' : type === 'postgresql' ? 'PostgreSQL' : 'MySQL';
              const isActive = dbType === type;
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => handleTypeChange(type)}
                  style={{
                    flex: 1,
                    padding: '10px 0',
                    borderRadius: 8,
                    border: isActive
                      ? '1.5px solid #dc2626'
                      : '1.5px solid rgba(224,224,230,0.15)',
                    background: isActive
                      ? 'rgba(220,38,38,0.12)'
                      : 'rgba(255,255,255,0.03)',
                    color: isActive ? '#f87171' : 'rgba(224,224,230,0.55)',
                    fontWeight: isActive ? 700 : 500,
                    fontSize: 13,
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>

        {/* ── MongoDB fields ── */}
        {dbType === 'mongodb' && (
          <>
            <div className="add-conn-field">
              <label className="add-conn-label">Connection URI</label>
              <input
                className="add-conn-input"
                name="connection_string"
                value={mongoUri}
                onChange={(e) => setMongoUri(e.target.value)}
                placeholder="mongodb+srv://user:pass@cluster.example.mongodb.net"
                required
              />
            </div>
            <div className="add-conn-field">
              <label className="add-conn-label">Database Name <span style={{ opacity: 0.45 }}>(optional — inferred from URI)</span></label>
              <input
                className="add-conn-input"
                name="database_name"
                value={mongoDb}
                onChange={(e) => setMongoDb(e.target.value)}
                placeholder="e.g. college_db"
              />
            </div>
          </>
        )}

        {/* ── PostgreSQL fields ── */}
        {dbType === 'postgresql' && (
          <>
            <div className="add-conn-field">
              <label className="add-conn-label">Host</label>
              <input
                className="add-conn-input"
                name="pg_host"
                value={pgHost}
                onChange={(e) => setPgHost(e.target.value)}
                placeholder="e.g. 127.0.0.1 or db.example.com"
                required
              />
            </div>
            <div className="add-conn-field">
              <label className="add-conn-label">Port</label>
              <input
                className="add-conn-input"
                name="pg_port"
                type="number"
                min={1}
                max={65535}
                value={pgPort}
                onChange={(e) => setPgPort(e.target.value)}
                placeholder="5432"
                required
              />
            </div>
            <div className="add-conn-field">
              <label className="add-conn-label">Database Name</label>
              <input
                className="add-conn-input"
                name="pg_database_name"
                value={pgDb}
                onChange={(e) => setPgDb(e.target.value)}
                placeholder="e.g. myapp_db"
                required
              />
            </div>
            <div className="add-conn-field">
              <label className="add-conn-label">Username</label>
              <input
                className="add-conn-input"
                name="pg_username"
                value={pgUser}
                onChange={(e) => setPgUser(e.target.value)}
                placeholder="e.g. postgres"
              />
            </div>
            <div className="add-conn-field">
              <label className="add-conn-label">Password</label>
              <input
                className="add-conn-input"
                name="pg_password"
                type="password"
                value={pgPass}
                onChange={(e) => setPgPass(e.target.value)}
                placeholder="Database password"
                autoComplete="new-password"
              />
            </div>
          </>
        )}

        {/* ── MySQL fields ── */}
        {dbType === 'mysql' && (
          <>
            <div className="add-conn-field">
              <label className="add-conn-label">Host</label>
              <input
                className="add-conn-input"
                name="host"
                value={mysqlHost}
                onChange={(e) => setMysqlHost(e.target.value)}
                placeholder="e.g. 127.0.0.1 or db.example.com"
                required
              />
            </div>
            <div className="add-conn-field">
              <label className="add-conn-label">Port</label>
              <input
                className="add-conn-input"
                name="port"
                type="number"
                min={1}
                max={65535}
                value={mysqlPort}
                onChange={(e) => setMysqlPort(e.target.value)}
                placeholder="3306"
                required
              />
            </div>
            <div className="add-conn-field">
              <label className="add-conn-label">Database Name</label>
              <input
                className="add-conn-input"
                name="database_name"
                value={mysqlDb}
                onChange={(e) => setMysqlDb(e.target.value)}
                placeholder="e.g. college_db"
                required
              />
            </div>
            <div className="add-conn-field">
              <label className="add-conn-label">Username</label>
              <input
                className="add-conn-input"
                name="username"
                value={mysqlUser}
                onChange={(e) => setMysqlUser(e.target.value)}
                placeholder="e.g. root"
              />
            </div>
            <div className="add-conn-field">
              <label className="add-conn-label">Password</label>
              <input
                className="add-conn-input"
                name="password"
                type="password"
                value={mysqlPass}
                onChange={(e) => setMysqlPass(e.target.value)}
                placeholder="Database password"
                autoComplete="new-password"
              />
            </div>
          </>
        )}

        {/* ── Test result banner ── */}
        {testState === 'success' && (
          <div className="add-conn-banner add-conn-banner--success">
            <svg className="banner-svg" viewBox="0 0 14 14" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 7l4 4 6-6" />
            </svg>
            {testMsg || 'Connection successful — database reachable'}
          </div>
        )}
        {testState === 'error' && (
          <div className="add-conn-banner add-conn-banner--error">
            <svg className="banner-svg" viewBox="0 0 14 14" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="7" cy="7" r="5.5" />
              <line x1="7" y1="4.5" x2="7" y2="7.5" strokeWidth="1.5" />
              <circle cx="7" cy="9.5" r="0.6" fill="currentColor" stroke="none" />
            </svg>
            {testMsg || 'Could not connect — check your settings.'}
          </div>
        )}

        {/* ── Connect error ── */}
        {connectError && (
          <div className="add-conn-banner add-conn-banner--error">
            <svg className="banner-svg" viewBox="0 0 14 14" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="7" cy="7" r="5.5" />
              <line x1="7" y1="4.5" x2="7" y2="7.5" strokeWidth="1.5" />
              <circle cx="7" cy="9.5" r="0.6" fill="currentColor" stroke="none" />
            </svg>
            {connectError}
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
