import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHistory } from '../context/api';
import './HistoryPage.css';

export default function HistoryPage() {
  const navigate               = useNavigate();
  const [allRows, setAllRows]  = useState([]);
  const [filter, setFilter]    = useState('all'); // 'all' | 'success' | 'blocked'
  const [loading, setLoading]  = useState(true);
  const [error, setError]      = useState(null);

  useEffect(() => {
    getHistory()
      .then((data) => { setAllRows(data); setLoading(false); })
      .catch((e)   => { setError(e.message || 'Failed to load history'); setLoading(false); });
  }, []);

  const counts = {
    all:     allRows.length,
    success: allRows.filter((r) => r.status === 'success').length,
    blocked: allRows.filter((r) => r.status === 'blocked').length,
  };

  const displayed = filter === 'all'     ? allRows
                  : filter === 'success' ? allRows.filter((r) => r.status === 'success')
                  : allRows.filter((r) => r.status === 'blocked');

  const handleRowClick = useCallback((row) => {
    if (row.status === 'blocked') return; // don't rerun blocked queries
    sessionStorage.setItem('qm_rerun_query', row.query);
    navigate('/workspace');
  }, [navigate]);

  const FILTERS = [
    { key: 'all',     label: 'All' },
    { key: 'success', label: 'Successful' },
    { key: 'blocked', label: 'Blocked' },
  ];

  return (
    <div className="history-viewport">
      <header className="history-header">
        <div>
          <h2>Query History</h2>
          <p>Previous natural-language queries — click to re-run</p>
        </div>

        {/* Filter tabs */}
        <div className="history-filters">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              type="button"
              className={`history-filter-btn ${filter === f.key ? 'history-filter-btn--active' : ''}`}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
              <span className={`history-filter-count ${filter === f.key ? 'history-filter-count--active' : ''}`}>
                {counts[f.key]}
              </span>
            </button>
          ))}
        </div>
      </header>

      <div className="history-list">
        {loading && <span style={{ color: 'rgba(224,224,230,0.32)', fontSize: 13 }}>Loading…</span>}
        {error   && <span style={{ color: '#e74c3c', fontSize: 13 }}>{error}</span>}

        {!loading && !error && displayed.length === 0 && (
          <span style={{ color: 'rgba(224,224,230,0.22)', fontSize: 13, padding: '20px 0' }}>
            No {filter !== 'all' ? filter : ''} queries found.
          </span>
        )}

        {!loading && !error && displayed.map((row, i) => (
          <button
            key={row.id}
            type="button"
            className={`history-row ${row.status === 'blocked' ? 'history-row--blocked' : ''}`}
            style={{ animation: `fadeRow 0.35s ease-out ${i * 0.04}s both` }}
            onClick={() => handleRowClick(row)}
            title={row.status === 'blocked' ? 'Blocked — cannot re-run' : 'Click to re-run'}
          >
            {/* Type badge */}
            <span className={`history-type-badge history-type-badge--${row.type}`}>
              {row.type}
            </span>

            {/* Center */}
            <div className="history-row-center">
              <span className="history-query-text">{row.query}</span>
              <span className="history-collection">{row.collection}</span>
            </div>

            {/* Right */}
            <div className="history-row-right">
              <span className="history-time">{row.time}</span>
              <span className={`history-count history-count--${row.type}`}>{row.count}</span>
            </div>

            {/* Status chip */}
            <span className={`history-status-chip history-status-chip--${row.status}`}>
              {row.status}
            </span>

            {/* Arrow (only for non-blocked) */}
            {row.status !== 'blocked' && (
              <svg className="history-row-arrow" viewBox="0 0 11 11" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 5.5h7M6 2l3 3.5-3 3.5" />
              </svg>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
