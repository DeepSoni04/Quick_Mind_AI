import { useState } from 'react';
import {
  Database, Plus, RefreshCw, Settings, Trash2, CheckCircle2,
  AlertCircle, Eye, Table2, Link2, Server
} from 'lucide-react';
import './DatabasesPage.css';

const MOCK_DATABASES = [
  {
    id: 1,
    name: 'hr_production',
    type: 'PostgreSQL',
    host: 'db-hr.querymind.ai',
    port: 5432,
    status: 'connected',
    tables: 24,
    size: '156 MB',
    lastSync: '2 minutes ago',
    schemas: ['public', 'hr', 'payroll'],
  },
  {
    id: 2,
    name: 'hospital_db',
    type: 'MySQL',
    host: 'db-hospital.querymind.ai',
    port: 3306,
    status: 'connected',
    tables: 18,
    size: '89 MB',
    lastSync: '5 minutes ago',
    schemas: ['main'],
  },
  {
    id: 3,
    name: 'inventory_db',
    type: 'PostgreSQL',
    host: 'db-inv.querymind.ai',
    port: 5432,
    status: 'connected',
    tables: 12,
    size: '42 MB',
    lastSync: '10 minutes ago',
    schemas: ['public', 'warehouse'],
  },
  {
    id: 4,
    name: 'sales_db',
    type: 'MySQL',
    host: 'db-sales.querymind.ai',
    port: 3306,
    status: 'maintenance',
    tables: 31,
    size: '234 MB',
    lastSync: '1 hour ago',
    schemas: ['main', 'analytics'],
  },
];

export default function DatabasesPage() {
  const [showModal, setShowModal] = useState(false);

  return (
    <div className="databases-page">
      <header className="databases-page__header">
        <div>
          <h1><Database size={24} /> Database Connections</h1>
          <p>Manage your connected databases and schema mappings</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={16} /> Add Database
        </button>
      </header>

      {/* Database Grid */}
      <div className="databases-page__grid">
        {MOCK_DATABASES.map((db, i) => (
          <div key={db.id} className="databases-page__card card" style={{ animationDelay: `${i * 0.1}s` }}>
            <div className="databases-page__card-header">
              <div className="databases-page__card-icon">
                <Server size={22} />
              </div>
              <div>
                <h3 className="databases-page__card-name">{db.name}</h3>
                <span className="databases-page__card-type">{db.type}</span>
              </div>
              <span className={`badge ${db.status === 'connected' ? 'badge-success' : 'badge-warning'}`}>
                {db.status === 'connected' ? <><CheckCircle2 size={10} /> Connected</> : <><AlertCircle size={10} /> Maintenance</>}
              </span>
            </div>

            <div className="databases-page__card-details">
              <div className="databases-page__detail">
                <Link2 size={14} />
                <span>{db.host}:{db.port}</span>
              </div>
              <div className="databases-page__detail">
                <Table2 size={14} />
                <span>{db.tables} tables</span>
              </div>
              <div className="databases-page__detail">
                <Database size={14} />
                <span>{db.size}</span>
              </div>
            </div>

            <div className="databases-page__card-schemas">
              <span className="databases-page__schemas-label">Schemas:</span>
              {db.schemas.map(s => (
                <span key={s} className="badge badge-primary">{s}</span>
              ))}
            </div>

            <div className="databases-page__card-footer">
              <span className="databases-page__sync">Last sync: {db.lastSync}</span>
              <div className="databases-page__card-actions">
                <button className="btn btn-ghost btn-sm" title="Refresh schema"><RefreshCw size={14} /></button>
                <button className="btn btn-ghost btn-sm" title="View tables"><Eye size={14} /></button>
                <button className="btn btn-ghost btn-sm" title="Settings"><Settings size={14} /></button>
                <button className="btn btn-danger btn-sm" title="Remove"><Trash2 size={14} /></button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Database Modal */}
      {showModal && (
        <div className="databases-page__modal-overlay" onClick={() => setShowModal(false)}>
          <div className="databases-page__modal card" onClick={(e) => e.stopPropagation()}>
            <h2>Add New Database</h2>
            <p>Connect a new database to QueryMind AI</p>

            <form className="databases-page__form" onSubmit={(e) => { e.preventDefault(); setShowModal(false); }}>
              <div className="databases-page__form-row">
                <div className="databases-page__field">
                  <label>Database Name</label>
                  <input className="input-field" placeholder="my_database" />
                </div>
                <div className="databases-page__field">
                  <label>Database Type</label>
                  <select className="input-field">
                    <option>PostgreSQL</option>
                    <option>MySQL</option>
                    <option>MongoDB</option>
                  </select>
                </div>
              </div>

              <div className="databases-page__form-row">
                <div className="databases-page__field" style={{ flex: 2 }}>
                  <label>Host</label>
                  <input className="input-field" placeholder="localhost or hostname" />
                </div>
                <div className="databases-page__field" style={{ flex: 1 }}>
                  <label>Port</label>
                  <input className="input-field" placeholder="5432" type="number" />
                </div>
              </div>

              <div className="databases-page__form-row">
                <div className="databases-page__field">
                  <label>Username</label>
                  <input className="input-field" placeholder="db_user" />
                </div>
                <div className="databases-page__field">
                  <label>Password</label>
                  <input className="input-field" type="password" placeholder="••••••••" />
                </div>
              </div>

              <div className="databases-page__form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="button" className="btn btn-secondary"><RefreshCw size={14} /> Test Connection</button>
                <button type="submit" className="btn btn-primary"><Plus size={14} /> Connect</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
