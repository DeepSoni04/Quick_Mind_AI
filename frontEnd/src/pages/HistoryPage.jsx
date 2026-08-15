import { useState } from 'react';
import { History, Search, Trash2, Play, Clock, Database, Filter, Calendar } from 'lucide-react';
import './HistoryPage.css';

const MOCK_HISTORY = [
  {
    id: 1,
    query: 'Show me all employees with salary above 1 lakh',
    sql: 'SELECT * FROM employees WHERE salary > 100000;',
    database: 'hr_production',
    timestamp: '2026-08-15 19:22',
    rows: 12,
    status: 'success',
  },
  {
    id: 2,
    query: 'Kitne patients abhi admitted hain ICU mein?',
    sql: "SELECT COUNT(*) FROM patients WHERE ward = 'ICU' AND status = 'admitted';",
    database: 'hospital_db',
    timestamp: '2026-08-15 18:45',
    rows: 3,
    status: 'success',
  },
  {
    id: 3,
    query: 'Delete all records from users table',
    sql: 'DELETE FROM users;',
    database: 'main_db',
    timestamp: '2026-08-15 17:30',
    rows: 0,
    status: 'blocked',
  },
  {
    id: 4,
    query: 'Show product inventory below reorder level',
    sql: 'SELECT * FROM products WHERE quantity < reorder_level;',
    database: 'inventory_db',
    timestamp: '2026-08-15 16:10',
    rows: 5,
    status: 'success',
  },
  {
    id: 5,
    query: 'Monthly sales report for July 2026',
    sql: "SELECT DATE(order_date) as date, SUM(total) as revenue FROM orders WHERE MONTH(order_date) = 7 AND YEAR(order_date) = 2026 GROUP BY DATE(order_date);",
    database: 'sales_db',
    timestamp: '2026-08-14 14:20',
    rows: 31,
    status: 'success',
  },
  {
    id: 6,
    query: 'Attendance report for engineering department this week',
    sql: "SELECT e.name, a.date, a.check_in, a.check_out FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE e.department = 'Engineering' AND a.date >= CURRENT_DATE - INTERVAL '7 days';",
    database: 'hr_production',
    timestamp: '2026-08-14 11:05',
    rows: 28,
    status: 'success',
  },
];

export default function HistoryPage() {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');

  const filtered = MOCK_HISTORY.filter(h => {
    const matchSearch = h.query.toLowerCase().includes(search.toLowerCase()) ||
      h.sql.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === 'all' || h.status === filter;
    return matchSearch && matchFilter;
  });

  return (
    <div className="history-page">
      <header className="history-page__header">
        <div>
          <h1><History size={24} /> Query History</h1>
          <p>Review your past queries and results</p>
        </div>
        <div className="history-page__stats">
          <div className="history-page__stat">
            <span className="history-page__stat-value">{MOCK_HISTORY.length}</span>
            <span className="history-page__stat-label">Total Queries</span>
          </div>
          <div className="history-page__stat">
            <span className="history-page__stat-value">{MOCK_HISTORY.filter(h => h.status === 'success').length}</span>
            <span className="history-page__stat-label">Successful</span>
          </div>
          <div className="history-page__stat">
            <span className="history-page__stat-value">{MOCK_HISTORY.filter(h => h.status === 'blocked').length}</span>
            <span className="history-page__stat-label">Blocked</span>
          </div>
        </div>
      </header>

      {/* Filters */}
      <div className="history-page__filters">
        <div className="history-page__search">
          <Search size={16} />
          <input
            type="text"
            className="input-field"
            placeholder="Search queries..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="history-page__filter-group">
          {['all', 'success', 'blocked'].map(f => (
            <button
              key={f}
              className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' : f === 'success' ? '✓ Success' : '✗ Blocked'}
            </button>
          ))}
        </div>
      </div>

      {/* History List */}
      <div className="history-page__list">
        {filtered.map((item, index) => (
          <div key={item.id} className="history-page__item card" style={{ animationDelay: `${index * 0.05}s` }}>
            <div className="history-page__item-top">
              <span className={`badge ${item.status === 'success' ? 'badge-success' : 'badge-danger'}`}>
                {item.status === 'success' ? '✓ Success' : '✗ Blocked'}
              </span>
              <span className="history-page__item-db">
                <Database size={12} /> {item.database}
              </span>
              <span className="history-page__item-time">
                <Clock size={12} /> {item.timestamp}
              </span>
            </div>
            <div className="history-page__item-query">{item.query}</div>
            <pre className="history-page__item-sql"><code>{item.sql}</code></pre>
            <div className="history-page__item-bottom">
              <span className="history-page__item-rows">{item.rows} rows returned</span>
              <div className="history-page__item-actions">
                <button className="btn btn-ghost btn-sm"><Play size={14} /> Re-run</button>
                <button className="btn btn-ghost btn-sm"><Trash2 size={14} /></button>
              </div>
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="history-page__empty">
            <Search size={48} />
            <p>No queries found matching your search.</p>
          </div>
        )}
      </div>
    </div>
  );
}
