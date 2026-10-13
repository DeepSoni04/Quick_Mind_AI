import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import AmbientCanvas from '../components/AmbientCanvas';
import { submitQuery, addBlockedQuery } from '../context/api';
import { useAuth } from '../context/AuthContext';
import './ChatPage.css';

/** Detect query type from natural language text */
export function detectQueryType(query) {
  const text  = (query || '').trim();
  const lower = text.toLowerCase();
  if (/^(delete|remove|erase|purge)\b/i.test(text))                                               return 'delete';
  if (/^(change|update|set|modify)\b/i.test(text) || lower.includes("'s department") || lower.includes("'s name")) return 'update';
  return 'select';
}

const EXAMPLE_PILLS = [
  { text: 'Which students have unpaid fees this semester?', type: 'select' },
  { text: 'Show all students enrolled in Computer Science.', type: 'select' },
  { text: "Change Rahul's department to Computer Science.",  type: 'update' },
  { text: 'Delete all inactive student records.',            type: 'delete' },
];

const STAGE_LABELS = [
  'Understanding your question',
  'Finding relevant data',
  'Running database operation',
  'Operation complete',
];

const NODE_DEFS = [
  { key: 'user',     label: 'USER' },
  { key: 'ai',       label: 'QUERYMIND AI' },
  { key: 'database', label: 'DATABASE' },   // ← was MONGODB
  { key: 'result',   label: 'RESULT' },
];

/** Export rows to CSV and trigger browser download */
function exportCSV(rows) {
  if (!rows || rows.length === 0) return;
  const headers = ['Student ID', 'Name', 'Program', 'Semester', 'Fee Amount', 'Due Date', 'Status'];
  const keys    = ['id', 'name', 'program', 'semester', 'fee', 'dueDate', 'status'];
  const escape  = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const lines   = [headers.map(escape).join(','), ...rows.map((r) => keys.map((k) => escape(r[k])).join(','))];
  const blob    = new Blob([lines.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
  const url     = URL.createObjectURL(blob);
  const a       = document.createElement('a');
  a.href        = url;
  a.download    = 'querymind-results.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ─── Screen 2: Workspace ─────────────────────────────────────────────────────
function WorkspaceScreen({ onRunQuery, initialText = '' }) {
  const [queryText, setQueryText] = useState(initialText);
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef               = useRef(null);

  useEffect(() => { if (initialText) textareaRef.current?.focus(); }, [initialText]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (queryText.trim()) onRunQuery(queryText); }
  };

  const hasText   = queryText.trim().length > 0;
  const charCount = queryText.length;
  const rimClass   = isFocused ? 'composer-rim--focused'   : isHovered ? 'composer-rim--hovered'   : 'composer-rim--default';
  const innerClass = isFocused ? 'composer-inner--focused' : isHovered ? 'composer-inner--hovered' : 'composer-inner--default';

  return (
    <div className="workspace-viewport">
      <AmbientCanvas cursorInfluence={true} crimsonGlow={true} />
      <div className="workspace-drift-orb" />
      <div className="workspace-content">
        <header className="workspace-header">
          <span className="workspace-eyebrow">Student Database · MongoDB</span>
          <h1 className="workspace-title">Ask your database anything.</h1>
        </header>

        <div className="composer-wrapper" onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)}>
          <div className={`composer-rim ${rimClass}`} />
          <div className={`composer-inner ${innerClass}`}>
            <textarea
              ref={textareaRef}
              className="composer-textarea"
              rows={3}
              placeholder="Which students have unpaid fees this semester?"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
            />
            <div className="composer-bottom">
              <span className="composer-hint">
                {hasText ? `${charCount} chars · Enter to run` : 'Enter to run · Shift+Enter for newline'}
              </span>
              <button
                type="button"
                className={`composer-run-btn ${hasText ? 'composer-run-btn--active' : 'composer-run-btn--inactive'}`}
                disabled={!hasText}
                onClick={() => onRunQuery(queryText)}
              >
                <span>Run Query</span>
                <svg className="composer-run-icon" viewBox="0 0 12 12">
                  <path d="M2 6h8M7 3l3 3-3 3" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div className="example-pills-container">
          <span className="example-pills-label">Try an example</span>
          <div className="example-pills-row">
            {EXAMPLE_PILLS.map((pill, i) => (
              <button key={i} type="button" className="example-pill"
                onClick={() => { setQueryText(pill.text); textareaRef.current?.focus(); }}>
                <span className={`example-pill-dot example-pill-dot--${pill.type}`} />
                <span>{pill.text}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Screen 3: Processing ─────────────────────────────────────────────────────
function ProcessingScreen({ query, queryType, onComplete }) {
  const [stage, setStage]       = useState(0);
  const [complete, setComplete] = useState(false);

  useEffect(() => {
    const t1 = setTimeout(() => setStage(1), 1500);
    const t2 = setTimeout(() => setStage(2), 3000);
    const t3 = setTimeout(() => { setStage(3); setComplete(true); }, 4500);
    const t4 = setTimeout(() => onComplete(queryType), 5200);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const stageLabel = complete ? STAGE_LABELS[3] : STAGE_LABELS[stage];

  return (
    <div className="processing-viewport">
      <div className="processing-ambient-overlay" />
      <div className="processing-header">
        <span className="processing-eyebrow">Processing</span>
        <span className="processing-query">{query}</span>
      </div>

      <div className="processing-nodes-container">
        {NODE_DEFS.map((node, i) => {
          const isUser    = i === 0;
          const isActive  = !isUser && stage >= i;
          const isDone    = complete && i === 3;
          const showPings = isActive && !complete && i < 3;

          return (
            <div key={node.key}>
              <div className={`processing-node-card ${isUser ? 'processing-node-card--user' : isActive ? 'processing-node-card--active' : 'processing-node-card--inactive'}`}>
                <div className={`processing-node-dot ${isUser ? 'processing-node-dot--user' : isActive ? 'processing-node-dot--active' : 'processing-node-dot--inactive'}`} />
                <span className={`processing-node-label ${isUser ? 'processing-node-label--user' : isActive ? 'processing-node-label--active' : 'processing-node-label--inactive'}`}>
                  {node.label}
                </span>
                {showPings && (
                  <div className="processing-pings-wrapper">
                    {[0, 0.22, 0.44].map((d, idx) => (
                      <div key={idx} className="processing-ping-dot" style={{ animationDelay: `${d}s` }} />
                    ))}
                  </div>
                )}
                {isDone && (
                  <svg className="processing-check-icon" viewBox="0 0 15 15">
                    <path d="M2 7l4 4 6-6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </div>

              {i < NODE_DEFS.length - 1 && (
                <div className="processing-connector">
                  <div className={`processing-connector-line ${stage > i ? 'processing-connector-line--past' : 'processing-connector-line--future'}`} />
                  {stage === i && !complete && (
                    <div className={`processing-flowing-dot ${i === 0 ? 'processing-flowing-dot--crimson' : 'processing-flowing-dot--blue'}`} />
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div key={stageLabel} className={`processing-stage-label ${complete ? 'processing-stage-label--complete' : ''}`}>
        {stageLabel}
      </div>
    </div>
  );
}

// ─── Screen 4: Result ────────────────────────────────────────────────────────
function ResultScreen({ query, data, onNewQuery, onRegenerate, userRole }) {
  const rows = data?.data || [];

  return (
    <div className="result-viewport">
      <header className="result-header">
        <div className="result-header-left">
          <div className="result-status-row">
            <div className="result-status-dot" />
            <span className="result-status-text">{rows.length} records found</span>
          </div>
          <span className="result-query-text">{query}</span>
        </div>
        <div className="result-header-actions">
          {/* Regenerate — available to all roles for select results */}
          <button type="button" className="btn-regenerate" onClick={onRegenerate}>
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 6.5A4.5 4.5 0 0 1 6.5 2" />
              <path d="M11 6.5A4.5 4.5 0 0 1 6.5 11" />
              <polyline points="2 3.5 2 6.5 5 6.5" />
              <polyline points="11 9.5 11 6.5 8 6.5" />
            </svg>
            Regenerate
          </button>

          <button type="button" className="btn-new-query" onClick={onNewQuery}>New Query</button>

          {/* Export CSV — only for SELECT results (read-only) */}
          <button type="button" className="btn-export-csv" onClick={() => exportCSV(rows)}>
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6.5 1v8M3.5 6l3 3 3-3M1 10v1.5a.5.5 0 0 0 .5.5h10a.5.5 0 0 0 .5-.5V10" />
            </svg>
            Export CSV
          </button>
        </div>
      </header>

      <div className="result-table-container">
        <table className="result-table">
          <thead>
            <tr>
              {['Student ID', 'Name', 'Program', 'Semester', 'Fee Amount', 'Due Date', 'Status'].map((h) => (
                <th key={h} className="result-th">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={row.id} className="result-row" style={{ animation: `fadeRow 0.38s ease-out ${i * 0.04}s both` }}>
                <td className="result-td result-td--id">{row.id}</td>
                <td className="result-td result-td--name">{row.name}</td>
                <td className="result-td result-td--program">{row.program}</td>
                <td className="result-td result-td--semester">{row.semester}</td>
                <td className="result-td result-td--fee">{row.fee}</td>
                <td className="result-td result-td--date">{row.dueDate}</td>
                <td className="result-td">
                  <span className={`status-badge status-badge--${row.status.toLowerCase()}`}>{row.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Screen: Blocked Query (viewer tried UPDATE/DELETE) ───────────────────────
function BlockedQueryScreen({ query, queryType, onNewQuery }) {
  return (
    <div className="action-viewport">
      <div className="blocked-content" style={{ animation: 'slideUp 0.45s ease-out both' }}>
        <div className="blocked-icon-ring">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="rgba(231,76,60,0.85)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="9" />
            <line x1="12" y1="7" x2="12" y2="13" />
            <circle cx="12" cy="16.5" r="0.75" fill="rgba(231,76,60,0.85)" stroke="none" />
          </svg>
        </div>
        <div className="blocked-title">Permission Denied</div>
        <div className="blocked-subtitle">
          Your role (<strong>Viewer</strong>) does not allow{' '}
          <span className="blocked-type">{queryType.toUpperCase()}</span> operations.
        </div>
        <div className="blocked-query">{query}</div>
        <p className="blocked-hint">
          Contact your administrator to request Analyst or Admin access if you need to modify data.
        </p>
        <button type="button" className="btn-success-new-query" onClick={onNewQuery}>
          New Query
        </button>
      </div>
    </div>
  );
}

// ─── Screen 5: Update Preview ─────────────────────────────────────────────────
function UpdatePreviewScreen({ query, data, onNewQuery, onCancel }) {
  const [execState, setExecState] = useState('idle');
  const rec = data?.record || {};

  if (execState === 'done') {
    return (
      <div className="action-viewport">
        <div className="action-success-view">
          <div className="success-circle">
            <svg className="success-check-svg" viewBox="0 0 24 24"><path d="M4 10l5 5 8-8" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </div>
          <div className="success-title">Change completed</div>
          <div className="success-subtitle">1 record updated</div>
          <button type="button" className="btn-success-new-query" onClick={onNewQuery}>New Query</button>
        </div>
      </div>
    );
  }

  return (
    <div className="action-viewport">
      <div className="action-content">
        <div className="action-header">
          <span className="action-eyebrow--update">Update Record</span>
          <p className="action-query">{query}</p>
        </div>
        <div className="action-card action-card--update">
          <div className="action-card-header">
            <span className="action-card-title">{rec.name || 'Rahul Mehta'}</span>
            <span className="action-card-id">{rec.id || 'STU-2024-023'}</span>
          </div>
          <div className="action-card-body">
            <span className="action-section-label">{rec.field || 'Department'}</span>
            <div className="diff-row">
              <span className="diff-val-before">{rec.before || 'Information Technology'}</span>
              <svg className="diff-arrow" viewBox="0 0 20 10"><path d="M0 5h17M13 1l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" /></svg>
              <span className="diff-val-after">{rec.after || 'Computer Science'}</span>
            </div>
          </div>
          <div className="action-card-footer">This will modify {rec.affectedCount || 1} record.</div>
        </div>
        <div className="action-buttons-row">
          <button type="button" className="btn-cancel" onClick={onCancel}>Cancel</button>
          <button type="button"
            className={`btn-confirm-action ${execState === 'executing' ? 'btn-confirm-action--updating' : 'btn-confirm-action--update'}`}
            onClick={() => { setExecState('executing'); setTimeout(() => setExecState('done'), 1800); }}
            disabled={execState === 'executing'}
          >
            {execState === 'executing' ? <><div className="spinner-update" /><span>Executing change…</span></> : 'Confirm Change'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Screen 6: Delete Confirm ─────────────────────────────────────────────────
function DeleteConfirmScreen({ query, data, onNewQuery, onCancel }) {
  const [execState, setExecState] = useState('idle');
  const w = data?.warning || {};
  const count = w.affectedCount || 126;

  if (execState === 'done') {
    return (
      <div className="action-viewport">
        <div className="action-success-view">
          <div className="success-circle">
            <svg className="success-check-svg" viewBox="0 0 24 24"><path d="M4 10l5 5 8-8" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </div>
          <div className="success-title">Operation completed</div>
          <div className="success-subtitle">{count} records deleted</div>
          <button type="button" className="btn-success-new-query" onClick={onNewQuery}>New Query</button>
        </div>
      </div>
    );
  }

  return (
    <div className="action-viewport">
      <div className="action-content">
        <div className="action-header">
          <div className="action-header--delete">
            <div className="action-warning-dot" />
            <span className="action-eyebrow--delete">Destructive Action</span>
          </div>
          <p className="action-query">{query}</p>
        </div>
        <div className="action-card action-card--delete">
          <div className="action-card-header">
            <div className="action-card-title--delete">This will permanently delete <span className="action-highlight-red">{count} records</span>.</div>
            <span className="action-card-subtitle">This action cannot be undone.</span>
          </div>
          <div className="action-card-body" style={{ gap: 0 }}>
            {[
              { label: 'Collection', value: w.collection || 'students' },
              { label: 'Condition', value: w.condition || 'status = inactive' },
              { label: 'Records affected', value: String(count), red: true },
            ].map((row) => (
              <div key={row.label} className="delete-info-row">
                <span className="delete-info-label">{row.label}</span>
                <span className={`delete-info-value ${row.red ? 'delete-info-value--red' : ''}`}>{row.value}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="action-buttons-row">
          <button type="button" className="btn-cancel" onClick={onCancel}>Cancel</button>
          <button type="button"
            className={`btn-confirm-action ${execState === 'deleting' ? 'btn-confirm-action--deleting' : 'btn-confirm-action--delete'}`}
            onClick={() => { setExecState('deleting'); setTimeout(() => setExecState('done'), 2100); }}
            disabled={execState === 'deleting'}
          >
            {execState === 'deleting' ? <><div className="spinner-delete" /><span>Deleting…</span></> : `Delete ${count} Records`}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main ChatPage ─────────────────────────────────────────────────────────────
export default function ChatPage({ view = 'workspace' }) {
  const { user }    = useAuth();
  const role        = user?.role || 'viewer';

  const [activeQuery,  setActiveQuery]  = useState('');
  const [detectedType, setDetectedType] = useState('select');
  const [queryResult,  setQueryResult]  = useState(null);
  const [currentView,  setCurrentView]  = useState(view);
  const [initialText,  setInitialText]  = useState(() => {
    // Check if history page sent a re-run query
    const stored = sessionStorage.getItem('qm_rerun_query');
    if (stored) { sessionStorage.removeItem('qm_rerun_query'); return stored; }
    return '';
  });

  useEffect(() => { setCurrentView(view); }, [view]);

  const handleRunQuery = useCallback(async (text) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const qType = detectQueryType(trimmed);
    setActiveQuery(trimmed);
    setDetectedType(qType);
    setInitialText('');

    // Viewer permission check
    if (role === 'viewer' && qType !== 'select') {
      addBlockedQuery(trimmed, qType, user?.name || 'Viewer');
      setCurrentView('blocked');
      return;
    }

    setCurrentView('processing');
    try {
      const res = await submitQuery(trimmed, { name: user?.name });
      setQueryResult(res);
    } catch (err) {
      console.error('Query error:', err);
    }
  }, [role, user]);

  const handleProcessingComplete = useCallback((qType) => {
    setCurrentView(qType === 'update' ? 'update-preview' : qType === 'delete' ? 'delete-confirm' : 'result');
  }, []);

  const handleNewQuery   = useCallback(() => { setCurrentView('workspace'); setActiveQuery(''); setQueryResult(null); }, []);
  const handleCancel     = useCallback(() => { setCurrentView('workspace'); }, []);
  const handleRegenerate = useCallback(async () => {
    if (!activeQuery) return;
    setCurrentView('processing');
    try {
      const res = await submitQuery(activeQuery, { name: user?.name });
      setQueryResult(res);
    } catch (err) {
      console.error('Regenerate error:', err);
    }
  }, [activeQuery, user]);

  if (currentView === 'workspace') return <WorkspaceScreen onRunQuery={handleRunQuery} initialText={initialText} />;
  if (currentView === 'processing') return <ProcessingScreen query={activeQuery} queryType={detectedType} onComplete={handleProcessingComplete} />;
  if (currentView === 'result')     return <ResultScreen query={activeQuery} data={queryResult} onNewQuery={handleNewQuery} onRegenerate={handleRegenerate} userRole={role} />;
  if (currentView === 'blocked')    return <BlockedQueryScreen query={activeQuery} queryType={detectedType} onNewQuery={handleNewQuery} />;
  if (currentView === 'update-preview') return <UpdatePreviewScreen query={activeQuery} data={queryResult} onNewQuery={handleNewQuery} onCancel={handleCancel} />;
  if (currentView === 'delete-confirm') return <DeleteConfirmScreen query={activeQuery} data={queryResult} onNewQuery={handleNewQuery} onCancel={handleCancel} />;

  return <WorkspaceScreen onRunQuery={handleRunQuery} initialText={initialText} />;
}
