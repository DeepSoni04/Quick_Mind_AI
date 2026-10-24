import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import AmbientCanvas from '../components/AmbientCanvas';
import {
  generateQuery,
  revalidateQuery,
  approveQuery,
  executeQuery,
  exportQueryCSV,
  getDatabaseConnections
} from '../context/api';
import { useAuth } from '../context/AuthContext';
import './ChatPage.css';

/** Detect query operation type from natural language text */
export function detectQueryType(query) {
  const text  = (query || '').trim();
  const lower = text.toLowerCase();
  if (/^(delete|remove|erase|purge)\b/i.test(text)) return 'delete';
  if (/^(change|update|set|modify)\b/i.test(text) || lower.includes("'s department") || lower.includes("'s name")) return 'update';
  return 'select';
}

const EXAMPLE_PILLS = [
  { text: 'Which students have unpaid fees this semester?', type: 'select' },
  { text: 'Show all students enrolled in Computer Science.', type: 'select' },
  { text: "Change Rahul's department to Computer Science.",  type: 'update' },
  { text: 'Delete all inactive student records.',            type: 'delete' },
];

// ─── Screen 2: Workspace with Voice Input ─────────────────────────────────────
function WorkspaceScreen({ onRunQuery, initialText = '', selectedDbId, selectedDbType, onDbChange, connections }) {
  const [queryText, setQueryText] = useState(initialText);
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef(null);

  useEffect(() => { if (initialText) textareaRef.current?.focus(); }, [initialText]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (queryText.trim()) onRunQuery(queryText, isListening ? 'voice' : 'text', selectedDbId, selectedDbType);
    }
  };

  // Browser Web Speech API for voice to text
  const toggleVoiceInput = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Voice input is not supported in your browser. Please use Google Chrome or Microsoft Edge.');
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map((res) => res[0].transcript)
          .join('');
        setQueryText(transcript);
      };

      recognition.start();
    } catch (err) {
      console.error('Voice recognition error:', err);
      setIsListening(false);
    }
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
          <span className="workspace-eyebrow">Database Assistant · MongoDB / MySQL / PostgreSQL</span>
          <h1 className="workspace-title">Ask your database anything.</h1>
        </header>

        {/* ── Database Connection Selector ── */}
        {connections && connections.length > 0 && (
          <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 12, color: 'rgba(224,224,230,0.55)', fontWeight: 600, letterSpacing: '0.04em' }}>TARGET DATABASE</span>
            <select
              id="chat-db-selector"
              value={selectedDbId || ''}
              onChange={(e) => {
                const conn = connections.find(c => c.id === e.target.value);
                onDbChange(e.target.value, conn?.db_type || '');
              }}
              style={{
                background: 'rgba(255,255,255,0.07)',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: 8,
                color: 'rgba(224,224,230,0.85)',
                fontSize: 13,
                padding: '5px 12px',
                cursor: 'pointer',
                outline: 'none',
                fontFamily: 'inherit',
              }}
            >
              <option value="">— No connection selected —</option>
              {connections.map(conn => (
                <option key={conn.id} value={conn.id}>
                  [{conn.db_type?.toUpperCase()}] {conn.name || conn.database_name}
                </option>
              ))}
            </select>
          </div>
        )}


        <div className="composer-wrapper" onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)}>
          <div className={`composer-rim ${rimClass}`} />
          <div className={`composer-inner ${innerClass}`}>
            <textarea
              ref={textareaRef}
              className="composer-textarea"
              rows={3}
              placeholder="Which students have unpaid fees this semester? (English / Hinglish)"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
            />
            <div className="composer-bottom">
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {/* Voice Input Button */}
                <button
                  type="button"
                  title="Voice Input (Speech to text)"
                  onClick={toggleVoiceInput}
                  style={{
                    background: isListening ? 'rgba(231,76,60,0.25)' : 'rgba(255,255,255,0.06)',
                    border: isListening ? '1px solid rgba(231,76,60,0.6)' : '1px solid rgba(255,255,255,0.12)',
                    borderRadius: '8px',
                    padding: '6px 10px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    color: isListening ? '#e74c3c' : 'rgba(255,255,255,0.7)',
                    fontSize: '12px',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="23"/>
                    <line x1="8" y1="23" x2="16" y2="23"/>
                  </svg>
                  <span>{isListening ? 'Listening…' : 'Voice'}</span>
                </button>
                <span className="composer-hint">
                  {hasText ? `${charCount} chars · Enter to generate` : 'Enter to generate query · Shift+Enter for newline'}
                </span>
              </div>

              <button
                type="button"
                className={`composer-run-btn ${hasText ? 'composer-run-btn--active' : 'composer-run-btn--inactive'}`}
                disabled={!hasText}
                onClick={() => onRunQuery(queryText, isListening ? 'voice' : 'text', selectedDbId, selectedDbType)}
              >
                <span>Generate Query</span>
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

// ─── SQL Approval Screen (Natural Language -> SQL -> Validate -> Approval Flow) ──
function ApprovalScreen({ queryRes, onApproveAndExecute, onCancel, onRevalidate }) {
  const [editingIndex, setEditingIndex] = useState(null);
  const [editedSql, setEditedSql]       = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError]               = useState('');

  if (!queryRes || !queryRes.statements) return null;

  const { query_id, nl_query, status, statements, clarification_needed, clarification_question, clarification_choices } = queryRes;

  const isBlocked = status === 'blocked';

  const handleStartEdit = (idx, currentSql) => {
    setEditingIndex(idx);
    setEditedSql(currentSql);
  };

  const handleSaveEdit = async () => {
    if (!editedSql.trim()) return;
    setIsSubmitting(true);
    setError('');
    try {
      await onRevalidate(query_id, editedSql.trim());
      setEditingIndex(null);
    } catch (err) {
      setError(err.message || 'Validation failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmApproval = async (idx) => {
    setIsSubmitting(true);
    setError('');
    try {
      await onApproveAndExecute(query_id, idx);
    } catch (err) {
      setError(err.message || 'Execution failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="action-viewport">
      <div className="action-content" style={{ maxWidth: 760, animation: 'slideUp 0.45s ease-out both' }}>
        <div className="action-header">
          <span className="action-eyebrow--update">
            {isBlocked ? 'Security Policy Block' : 'SQL Confirmation Required'}
          </span>
          <p className="action-query">"{nl_query}"</p>
        </div>

        {/* Ambiguity Clarification Prompt */}
        {clarification_needed && (
          <div className="action-card action-card--update" style={{ borderColor: 'rgba(241,196,15,0.4)' }}>
            <div className="action-card-header">
              <span className="action-card-title" style={{ color: '#f1c40f' }}>Clarification Needed</span>
            </div>
            <div className="action-card-body">
              <p style={{ color: '#e0e0e6', fontSize: 14 }}>{clarification_question}</p>
              {clarification_choices && (
                <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
                  {clarification_choices.map((choice) => (
                    <button
                      key={choice}
                      className="example-pill"
                      onClick={() => onRevalidate(query_id, `SELECT * FROM ${choice};`)}
                    >
                      {choice}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Statement Cards */}
        {statements.map((stmt, idx) => {
          const op = (stmt.operation || 'SELECT').toUpperCase();
          const isWarning = stmt.validation_status === 'warning' || stmt.warning_broad_impact;
          const isStmtBlocked = stmt.validation_status === 'blocked';
          const isEditing = editingIndex === idx;

          return (
            <div
              key={idx}
              className={`action-card ${op === 'DELETE' ? 'action-card--delete' : 'action-card--update'}`}
              style={{
                marginBottom: 16,
                borderColor: isStmtBlocked ? 'rgba(231,76,60,0.5)' : isWarning ? 'rgba(241,196,15,0.5)' : 'rgba(254,239,184,0.25)'
              }}
            >
              <div className="action-card-header" style={{ justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className={`status-badge status-badge--${op === 'SELECT' ? 'active' : op === 'DELETE' ? 'inactive' : 'pending'}`}>
                    {op}
                  </span>
                  <span className="action-card-id">Statement #{idx + 1}</span>
                  {stmt.affected_table && <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)' }}>Table: {stmt.affected_table}</span>}
                </div>
                <span className="action-card-subtitle" style={{ color: isStmtBlocked ? '#e74c3c' : isWarning ? '#f1c40f' : '#2ecc71' }}>
                  {stmt.validation_status.toUpperCase()}
                </span>
              </div>

              <div className="action-card-body">
                {isEditing ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10, width: '100%' }}>
                    <textarea
                      rows={3}
                      value={editedSql}
                      onChange={(e) => setEditedSql(e.target.value)}
                      style={{
                        width: '100%',
                        backgroundColor: '#111318',
                        color: '#feefb8',
                        fontFamily: 'monospace',
                        fontSize: '13px',
                        padding: '12px',
                        borderRadius: '8px',
                        border: '1px solid rgba(254,239,184,0.4)',
                        outline: 'none'
                      }}
                    />
                    <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                      <button className="btn-cancel" onClick={() => setEditingIndex(null)}>Cancel Edit</button>
                      <button className="btn-confirm-action btn-confirm-action--update" onClick={handleSaveEdit} disabled={isSubmitting}>
                        {isSubmitting ? 'Validating…' : 'Validate & Save'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div style={{ width: '100%' }}>
                    <pre style={{
                      backgroundColor: 'rgba(0,0,0,0.35)',
                      padding: '14px',
                      borderRadius: '8px',
                      fontFamily: 'monospace',
                      fontSize: '13px',
                      color: '#feefb8',
                      overflowX: 'auto',
                      whiteSpace: 'pre-wrap',
                      margin: 0
                    }}>
                      {/* Show MQL (MongoDB) or SQL nicely */}
                      {stmt.mql
                        ? JSON.stringify(stmt.mql, null, 2)
                        : stmt.sql
                      }
                    </pre>

                    {/* Impact Preview: estimated rows affected for DELETE/UPDATE */}
                    {stmt.estimated_rows_affected != null && (op === 'DELETE' || op === 'UPDATE') && (
                      <div style={{
                        marginTop: 10,
                        padding: '8px 12px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        backgroundColor: op === 'DELETE' ? 'rgba(231,76,60,0.12)' : 'rgba(241,196,15,0.12)',
                        color: op === 'DELETE' ? '#e74c3c' : '#f1c40f',
                        border: `1px solid ${op === 'DELETE' ? 'rgba(231,76,60,0.3)' : 'rgba(241,196,15,0.3)'}`
                      }}>
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10"/>
                          <line x1="12" y1="8" x2="12" y2="12"/>
                          <line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                        <span>
                          <strong>Impact Preview:</strong> This {op.toLowerCase()} will affect approximately{' '}
                          <strong>{stmt.estimated_rows_affected.toLocaleString()} row{stmt.estimated_rows_affected !== 1 ? 's' : ''}</strong>.
                          {op === 'DELETE' && stmt.estimated_rows_affected > 100 && ' ⚠ Large deletion — verify the WHERE clause before approving.'}
                        </span>
                      </div>
                    )}

                    {/* Warning / Validation Message */}
                    {stmt.validation_message && (
                      <div style={{
                        marginTop: 10,
                        padding: '8px 12px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        backgroundColor: isStmtBlocked ? 'rgba(231,76,60,0.15)' : isWarning ? 'rgba(241,196,15,0.15)' : 'rgba(46,204,113,0.15)',
                        color: isStmtBlocked ? '#e74c3c' : isWarning ? '#f1c40f' : '#2ecc71',
                        border: `1px solid ${isStmtBlocked ? 'rgba(231,76,60,0.3)' : isWarning ? 'rgba(241,196,15,0.3)' : 'rgba(46,204,113,0.3)'}`
                      }}>
                        {stmt.validation_message}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {!isEditing && (
                <div className="action-card-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)' }}>
                    Approval: {stmt.approval_status}
                  </span>
                  {!isStmtBlocked && (
                    <button
                      type="button"
                      onClick={() => handleStartEdit(idx, stmt.sql)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#c4dae8',
                        fontSize: '12px',
                        cursor: 'pointer',
                        textDecoration: 'underline'
                      }}
                    >
                      Edit SQL
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {error && <div style={{ color: '#e74c3c', fontSize: 13, marginBottom: 12 }}>{error}</div>}

        <div className="action-buttons-row">
          <button type="button" className="btn-cancel" onClick={onCancel}>Cancel</button>
          {!isBlocked && (
            <button
              type="button"
              className="btn-confirm-action btn-confirm-action--update"
              onClick={() => handleConfirmApproval(0)}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Executing Query…' : 'Approve & Execute Query'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Screen 4: Dynamic Results Screen ─────────────────────────────────────────
function ResultScreen({ query, data, onNewQuery, onRegenerate, queryId }) {
  const [isExporting, setIsExporting] = useState(false);

  const columns = data?.columns || [];
  const rows = data?.rows || [];
  const rowCount = data?.row_count ?? rows.length;
  const execTime = data?.execution_time_ms ?? 0;
  const summary = data?.summary || `${rowCount} records returned.`;

  const handleDownloadCSV = async () => {
    if (!queryId) return;
    setIsExporting(true);
    try {
      const blob = await exportQueryCSV(queryId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `querymind-result-${queryId}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`CSV Export error: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="result-viewport">
      <header className="result-header">
        <div className="result-header-left">
          <div className="result-status-row">
            <div className="result-status-dot" />
            <span className="result-status-text">{rowCount} records ({execTime}ms)</span>
          </div>
          <span className="result-query-text">{query}</span>
          <p style={{ color: 'rgba(254,239,184,0.8)', fontSize: 12, marginTop: 4, fontStyle: 'italic' }}>{summary}</p>
        </div>
        <div className="result-header-actions">
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

          <button type="button" className="btn-export-csv" onClick={handleDownloadCSV} disabled={isExporting}>
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6.5 1v8M3.5 6l3 3 3-3M1 10v1.5a.5.5 0 0 0 .5.5h10a.5.5 0 0 0 .5-.5V10" />
            </svg>
            {isExporting ? 'Exporting…' : 'Export CSV'}
          </button>
        </div>
      </header>

      <div className="result-table-container">
        {columns.length > 0 ? (
          <table className="result-table">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col} className="result-th">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((rowArr, i) => (
                <tr key={i} className="result-row" style={{ animation: `fadeRow 0.38s ease-out ${Math.min(i * 0.03, 1)}s both` }}>
                  {rowArr.map((val, cellIdx) => (
                    <td key={cellIdx} className="result-td">
                      {val === null || val === undefined ? <span style={{ color: 'rgba(255,255,255,0.2)' }}>NULL</span> : String(val)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ padding: 40, textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: 14 }}>
            Operation executed successfully. {rowCount} rows affected.
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main ChatPage ─────────────────────────────────────────────────────────────
export default function ChatPage({ view = 'workspace' }) {
  const { user } = useAuth();
  const role = user?.role || 'viewer';

  const [activeQuery,    setActiveQuery]    = useState('');
  const [queryResult,    setQueryResult]    = useState(null);
  const [currentView,    setCurrentView]    = useState(view);
  const [connections,    setConnections]    = useState([]);
  const [selectedDbId,   setSelectedDbId]   = useState('');
  const [selectedDbType, setSelectedDbType] = useState('');
  const [initialText,    setInitialText]    = useState(() => {
    const stored = sessionStorage.getItem('qm_rerun_query');
    if (stored) { sessionStorage.removeItem('qm_rerun_query'); return stored; }
    return '';
  });

  useEffect(() => { setCurrentView(view); }, [view]);

  // Load user's database connections for selector
  useEffect(() => {
    getDatabaseConnections().then(data => {
      const list = Array.isArray(data) ? data : (data?.connections || []);
      setConnections(list);
      if (list.length > 0 && !selectedDbId) {
        setSelectedDbId(list[0].id);
        setSelectedDbType(list[0].db_type || '');
      }
    }).catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Step 1: User runs Natural Language Query -> Call POST /api/queries
  const handleRunQuery = useCallback(async (text, inputType = 'text', dbId, dbType) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setActiveQuery(trimmed);
    setInitialText('');

    setCurrentView('processing');
    try {
      const payload = { nl_query: trimmed, input_type: inputType };
      if (dbId) payload.database_id = dbId;
      const res = await generateQuery(payload);
      setQueryResult(res);
      setCurrentView('approval');
    } catch (err) {
      console.error('Query generation error:', err);
      alert(`Query error: ${err.message}`);
      setCurrentView('workspace');
    }
  }, []);

  // Step 2: User edits SQL -> Call POST /api/queries/:id/validate
  const handleRevalidate = useCallback(async (queryId, editedSql) => {
    try {
      const res = await revalidateQuery(queryId, editedSql);
      setQueryResult(res);
      return res;
    } catch (err) {
      console.error('Revalidation error:', err);
      throw err;
    }
  }, []);

  // Step 3: User approves statement -> Call POST /api/queries/:id/approve & POST /api/queries/:id/execute
  const handleApproveAndExecute = useCallback(async (queryId, statementIndex = 0) => {
    try {
      await approveQuery(queryId, statementIndex);
      const execRes = await executeQuery(queryId);
      setQueryResult(execRes);
      setCurrentView('result');
    } catch (err) {
      console.error('Execution error:', err);
      throw err;
    }
  }, []);

  const handleNewQuery   = useCallback(() => { setCurrentView('workspace'); setActiveQuery(''); setQueryResult(null); }, []);
  const handleCancel     = useCallback(() => { setCurrentView('workspace'); }, []);
  const handleRegenerate = useCallback(async () => {
    if (!activeQuery) return;
    setCurrentView('processing');
    try {
      const payload = { nl_query: activeQuery };
      if (selectedDbId) payload.database_id = selectedDbId;
      const res = await generateQuery(payload);
      setQueryResult(res);
      setCurrentView('approval');
    } catch (err) {
      console.error('Regenerate error:', err);
      setCurrentView('workspace');
    }
  }, [activeQuery, selectedDbId]);

  if (currentView === 'workspace')  return (
    <WorkspaceScreen
      onRunQuery={handleRunQuery}
      initialText={initialText}
      connections={connections}
      selectedDbId={selectedDbId}
      selectedDbType={selectedDbType}
      onDbChange={(id, type) => { setSelectedDbId(id); setSelectedDbType(type); }}
    />
  );
  if (currentView === 'processing') return (
    <div className="processing-viewport">
      <div className="processing-header">
        <span className="processing-eyebrow">Generating &amp; Validating Query</span>
        <span className="processing-query">{activeQuery}</span>
      </div>
      <div className="processing-nodes-container">
        <div className="processing-node-card processing-node-card--active">
          <div className="processing-node-dot processing-node-dot--active" />
          <span className="processing-node-label processing-node-label--active">Analyzing Schema & Validating AST…</span>
        </div>
      </div>
    </div>
  );
  if (currentView === 'approval')   return <ApprovalScreen queryRes={queryResult} onApproveAndExecute={handleApproveAndExecute} onCancel={handleCancel} onRevalidate={handleRevalidate} />;
  if (currentView === 'result')     return <ResultScreen query={activeQuery} data={queryResult} onNewQuery={handleNewQuery} onRegenerate={handleRegenerate} queryId={queryResult?.query_id} />;

  return (
    <WorkspaceScreen
      onRunQuery={handleRunQuery}
      initialText={initialText}
      connections={connections}
      selectedDbId={selectedDbId}
      selectedDbType={selectedDbType}
      onDbChange={(id, type) => { setSelectedDbId(id); setSelectedDbType(type); }}
    />
  );
}
