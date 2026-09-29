import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDashboardStats, getConnections } from '../context/api';
import './DashboardPage.css';

function makeAvatar(name = '') {
  const parts = name.trim().split(/\s+/);
  return (parts[0]?.[0] || '?').toUpperCase() + (parts[1]?.[0] || '').toUpperCase();
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats]         = useState(null);
  const [connections, setConnections] = useState([]);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    Promise.all([getDashboardStats(), getConnections()]).then(([s, c]) => {
      setStats(s);
      setConnections(c);
      setLoading(false);
    });
  }, []);

  const statCards = stats ? [
    { label: 'Total Queries',     value: stats.total,           suffix: '',    colorClass: '',                        sub: 'all time' },
    { label: 'Success Rate',      value: `${stats.successRate}%`, suffix: '',  colorClass: 'dashboard-stat-value--green', sub: 'of queries succeeded' },
    { label: 'Queries Blocked',   value: stats.blocked,         suffix: '',    colorClass: 'dashboard-stat-value--red',  sub: 'permission denials' },
    { label: 'Avg Response Time', value: stats.avgResponseTime, suffix: '',    colorClass: 'dashboard-stat-value--blue', sub: 'per query' },
  ] : [];

  return (
    <div className="dashboard-viewport">
      {/* Header */}
      <header className="dashboard-header">
        <div className="dashboard-header-left">
          <h2>Dashboard</h2>
          <p>QueryMind AI workspace overview</p>
        </div>
        <div className="dashboard-live-badge">
          <div className="dashboard-live-dot" />
          <span className="dashboard-live-text">Live</span>
        </div>
      </header>

      {loading ? (
        <div style={{ padding: '28px 36px', color: 'var(--text-muted)', fontSize: 13 }}>Loading…</div>
      ) : (
        <div className="dashboard-body">

          {/* ── Stat Cards ── */}
          <div className="dashboard-stat-grid">
            {statCards.map((card, i) => (
              <div
                key={card.label}
                className="dashboard-stat-card"
                style={{ animationDelay: `${i * 0.07}s` }}
              >
                <span className="dashboard-stat-label">{card.label}</span>
                <span className={`dashboard-stat-value ${card.colorClass}`}>{card.value}</span>
                <span className="dashboard-stat-sub">{card.sub}</span>
              </div>
            ))}
          </div>

          {/* ── Recent Queries ── */}
          <div>
            <div className="dashboard-section-header">
              <span className="dashboard-section-title">Recent Queries</span>
              <button type="button" className="btn-view-all" onClick={() => navigate('/history')}>
                View All →
              </button>
            </div>
            <div className="dashboard-recent-list">
              {(stats.recent || []).map((row, i) => (
                <div
                  key={row.id}
                  className="dashboard-recent-row"
                  style={{ animationDelay: `${i * 0.05}s` }}
                >
                  <div className="dashboard-recent-user" title={row.user}>
                    {makeAvatar(row.user)}
                  </div>
                  <div className="dashboard-recent-center">
                    <span className="dashboard-recent-query">{row.query}</span>
                    <span className="dashboard-recent-meta">{row.collection} · {row.count}</span>
                  </div>
                  <div className="dashboard-recent-right">
                    <span className="dashboard-recent-time">{row.time}</span>
                    <span className={`dash-status dash-status--${row.status}`}>
                      {row.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Connected Databases ── */}
          <div>
            <div className="dashboard-section-header">
              <span className="dashboard-section-title">Connected Databases</span>
              <button type="button" className="btn-view-all" onClick={() => navigate('/connections')}>
                Manage →
              </button>
            </div>
            <div className="dashboard-db-list">
              {connections.map((conn, i) => (
                <div
                  key={conn.id}
                  className="dashboard-db-card"
                  style={{ animationDelay: `${i * 0.06}s` }}
                >
                  <div className="dashboard-db-status-dot" />
                  <div className="dashboard-db-info">
                    <div className="dashboard-db-name">{conn.name}</div>
                    <div className="dashboard-db-type">{conn.type} · {conn.database}</div>
                  </div>
                  <div className="dashboard-db-stats">
                    <div className="dashboard-db-stat">
                      <span className="dashboard-db-stat-value">{conn.collectionsCount}</span>
                      <span className="dashboard-db-stat-label">Collections</span>
                    </div>
                    <div className="dashboard-db-stat">
                      <span className="dashboard-db-stat-value">{conn.queriesCount ?? '—'}</span>
                      <span className="dashboard-db-stat-label">Queries</span>
                    </div>
                  </div>
                  <button type="button" className="btn-manage-db" onClick={() => navigate('/connections')}>
                    Manage
                  </button>
                </div>
              ))}
              {connections.length === 0 && (
                <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No databases connected.</p>
              )}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
