import {
  LayoutDashboard, TrendingUp, Database, MessageSquare,
  Shield, Clock, Users, Activity, ArrowUpRight, ArrowDownRight, Zap
} from 'lucide-react';
import './DashboardPage.css';

const stats = [
  { label: 'Total Queries', value: '1,247', change: '+12.5%', up: true, icon: MessageSquare, color: 'primary' },
  { label: 'Success Rate', value: '94.2%', change: '+2.1%', up: true, icon: TrendingUp, color: 'accent' },
  { label: 'Queries Blocked', value: '73', change: '-8.3%', up: false, icon: Shield, color: 'danger' },
  { label: 'Avg Response Time', value: '0.34s', change: '-15%', up: false, icon: Clock, color: 'cyan' },
];

const recentQueries = [
  { user: 'Deep Soni', query: 'Show employees above 1L salary', db: 'hr_prod', time: '2 min ago', status: 'success' },
  { user: 'Heer Sachdev', query: 'Kitne patients admitted hain?', db: 'hospital_db', time: '8 min ago', status: 'success' },
  { user: 'Neel Shah', query: 'DROP TABLE users', db: 'main_db', time: '15 min ago', status: 'blocked' },
  { user: 'Parshwa Jain', query: 'Low stock products report', db: 'inventory_db', time: '22 min ago', status: 'success' },
  { user: 'Harsh Rathod', query: 'Monthly revenue breakdown', db: 'sales_db', time: '35 min ago', status: 'success' },
];

const databases = [
  { name: 'hr_production', type: 'PostgreSQL', tables: 24, status: 'connected', queries: 412 },
  { name: 'hospital_db', type: 'MySQL', tables: 18, status: 'connected', queries: 298 },
  { name: 'inventory_db', type: 'PostgreSQL', tables: 12, status: 'connected', queries: 187 },
  { name: 'sales_db', type: 'MySQL', tables: 31, status: 'maintenance', queries: 350 },
];

export default function DashboardPage() {
  return (
    <div className="dashboard-page">
      <header className="dashboard-page__header">
        <div>
          <h1><LayoutDashboard size={24} /> Dashboard</h1>
          <p>Overview of your QueryMind AI workspace</p>
        </div>
        <div className="dashboard-page__header-actions">
          <span className="dashboard-page__live">
            <Activity size={14} /> Live
          </span>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="dashboard-page__stats">
        {stats.map((stat, i) => (
          <div key={i} className="dashboard-page__stat-card card" style={{ animationDelay: `${i * 0.1}s` }}>
            <div className={`dashboard-page__stat-icon dashboard-page__stat-icon--${stat.color}`}>
              <stat.icon size={20} />
            </div>
            <div className="dashboard-page__stat-info">
              <span className="dashboard-page__stat-label">{stat.label}</span>
              <span className="dashboard-page__stat-value">{stat.value}</span>
              <span className={`dashboard-page__stat-change ${stat.up ? 'dashboard-page__stat-change--up' : 'dashboard-page__stat-change--down'}`}>
                {stat.up ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                {stat.change} this week
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-page__grid">
        {/* Recent Queries */}
        <div className="dashboard-page__section card">
          <div className="dashboard-page__section-header">
            <h2><Zap size={18} /> Recent Queries</h2>
            <button className="btn btn-ghost btn-sm">View All</button>
          </div>
          <div className="dashboard-page__query-list">
            {recentQueries.map((q, i) => (
              <div key={i} className="dashboard-page__query-item">
                <div className="dashboard-page__query-avatar">
                  {q.user.split(' ').map(n => n[0]).join('')}
                </div>
                <div className="dashboard-page__query-info">
                  <div className="dashboard-page__query-text">{q.query}</div>
                  <div className="dashboard-page__query-meta">
                    <span>{q.user}</span> · <span>{q.db}</span> · <span>{q.time}</span>
                  </div>
                </div>
                <span className={`badge ${q.status === 'success' ? 'badge-success' : 'badge-danger'}`}>
                  {q.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Connected Databases */}
        <div className="dashboard-page__section card">
          <div className="dashboard-page__section-header">
            <h2><Database size={18} /> Connected Databases</h2>
            <button className="btn btn-ghost btn-sm">Manage</button>
          </div>
          <div className="dashboard-page__db-list">
            {databases.map((db, i) => (
              <div key={i} className="dashboard-page__db-item">
                <div className="dashboard-page__db-icon">
                  <Database size={18} />
                </div>
                <div className="dashboard-page__db-info">
                  <div className="dashboard-page__db-name">{db.name}</div>
                  <div className="dashboard-page__db-meta">
                    {db.type} · {db.tables} tables · {db.queries} queries
                  </div>
                </div>
                <span className={`badge ${db.status === 'connected' ? 'badge-success' : 'badge-warning'}`}>
                  {db.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Query Activity Chart Placeholder */}
      <div className="dashboard-page__chart card">
        <div className="dashboard-page__section-header">
          <h2><TrendingUp size={18} /> Query Activity (Last 7 Days)</h2>
        </div>
        <div className="dashboard-page__chart-visual">
          {[65, 40, 80, 55, 95, 70, 85].map((h, i) => (
            <div key={i} className="dashboard-page__chart-bar-wrap">
              <div
                className="dashboard-page__chart-bar"
                style={{ height: `${h}%`, animationDelay: `${i * 0.1}s` }}
              />
              <span className="dashboard-page__chart-label">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i]}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
