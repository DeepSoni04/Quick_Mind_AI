import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import AmbientCanvas from '../components/AmbientCanvas';
<<<<<<< Updated upstream
import { submitQuery, addBlockedQuery } from '../context/api';
import { useAuth } from '../context/AuthContext';
import './ChatPage.css';

/** Detect query type from natural language text */
export function detectQueryType(query) {
  const text  = (query || '').trim();
  const lower = text.toLowerCase();
  if (/^(delete|remove|erase|purge)\b/i.test(text))                                               return 'delete';
=======
import {
  generateQuery,
  revalidateQuery,
  approveQuery,
  executeQuery,
  exportQueryCSV
} from '../context/api';
import { useAuth } from '../context/AuthContext';
import './ChatPage.css';

/** Detect query operation type from natural language text */
export function detectQueryType(query) {
  const text  = (query || '').trim();
  const lower = text.toLowerCase();
  if (/^(delete|remove|erase|purge)\b/i.test(text)) return 'delete';
>>>>>>> Stashed changes
  if (/^(change|update|set|modify)\b/i.test(text) || lower.includes("'s department") || lower.includes("'s name")) return 'update';
  return 'select';
}

const EXAMPLE_PILLS = [
  { text: 'Which students have unpaid fees this semester?', type: 'select' },
  { text: 'Show all students enrolled in Computer Science.', type: 'select' },
  { text: "Change Rahul's department to Computer Science.",  type: 'update' },
  { text: 'Delete all inactive student records.',            type: 'delete' },
];
<<<<<<< Updated upstream

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

=======

// ─── Screen 2: Workspace with Voice Input ─────────────────────────────────────
function WorkspaceScreen({ onRunQuery, initialText = '' }) {
  const [queryText, setQueryText] = useState(initialText);
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef(null);

  useEffect(() => { if (initialText) textareaRef.current?.focus(); }, [initialText]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (queryText.trim()) onRunQuery(queryText, isListening ? 'voice' : 'text');
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

>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
          <span className="workspace-eyebrow">Student Database · MongoDB</span>
=======
          <span className="workspace-eyebrow">Database Assistant · MongoDB / MySQL / PostgreSQL</span>
>>>>>>> Stashed changes
          <h1 className="workspace-title">Ask your database anything.</h1>
        </header>

        <div className="composer-wrapper" onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)}>
          <div className={`composer-rim ${rimClass}`} />
          <div className={`composer-inner ${innerClass}`}>
            <textarea
              ref={textareaRef}
              className="composer-textarea"
              rows={3}
<<<<<<< Updated upstream
              placeholder="Which students have unpaid fees this semester?"
=======
              placeholder="Which students have unpaid fees this semester? (English / Hinglish)"
>>>>>>> Stashed changes
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
            />
            <div className="composer-bottom">
<<<<<<< Updated upstream
              <span className="composer-hint">
                {hasText ? `${charCount} chars · Enter to run` : 'Enter to run · Shift+Enter for newline'}
              </span>
=======
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
                  {hasText ? `${charCount} chars · Enter to generate SQL` : 'Enter to generate SQL · Shift+Enter for newline'}
                </span>
              </div>

>>>>>>> Stashed changes
              <button
                type="button"
                className={`composer-run-btn ${hasText ? 'composer-run-btn--active' : 'composer-run-btn--inactive'}`}
                disabled={!hasText}
<<<<<<< Updated upstream
                onClick={() => onRunQuery(queryText)}
              >
                <span>Run Query</span>
=======
                onClick={() => onRunQuery(queryText, isListening ? 'voice' : 'text')}
              >
                <span>Generate SQL</span>
>>>>>>> Stashed changes
                <svg className="composer-run-icon" viewBox="0 0 12 12">
                  <path d="M2 6h8M7 3l3 3-3 3" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
<<<<<<< Updated upstream
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
=======
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
>>>>>>> Stashed changes
      </div>
    </div>
  );
}

<<<<<<< Updated upstream
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
=======
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
                      {stmt.sql}
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
>>>>>>> Stashed changes
                  )}
                </div>
              )}
            </div>
          );
        })}
<<<<<<< Updated upstream
      </div>

      <div key={stageLabel} className={`processing-stage-label ${complete ? 'processing-stage-label--complete' : ''}`}>
        {stageLabel}
=======

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
>>>>>>> Stashed changes
      </div>
    </div>
  );
}

<<<<<<< Updated upstream
// ─── Screen 4: Result ────────────────────────────────────────────────────────
function ResultScreen({ query, data, onNewQuery, onRegenerate, userRole }) {
  const rows = data?.data || [];
=======
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
>>>>>>> Stashed changes

  return (
    <div className="result-viewport">
      <header className="result-header">
        <div className="result-header-left">
          <div className="result-status-row">
            <div className="result-status-dot" />
<<<<<<< Updated upstream
            <span className="result-status-text">{rows.length} records found</span>
          </div>
          <span className="result-query-text">{query}</span>
        </div>
        <div className="result-header-actions">
          {/* Regenerate — available to all roles for select results */}
=======
            <span className="result-status-text">{rowCount} records ({execTime}ms)</span>
          </div>
          <span className="result-query-text">{query}</span>
          <p style={{ color: 'rgba(254,239,184,0.8)', fontSize: 12, marginTop: 4, fontStyle: 'italic' }}>{summary}</p>
        </div>
        <div className="result-header-actions">
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
          {/* Export CSV — only for SELECT results (read-only) */}
          <button type="button" className="btn-export-csv" onClick={() => exportCSV(rows)}>
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6.5 1v8M3.5 6l3 3 3-3M1 10v1.5a.5.5 0 0 0 .5.5h10a.5.5 0 0 0 .5-.5V10" />
            </svg>
            Export CSV
=======
          <button type="button" className="btn-export-csv" onClick={handleDownloadCSV} disabled={isExporting}>
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6.5 1v8M3.5 6l3 3 3-3M1 10v1.5a.5.5 0 0 0 .5.5h10a.5.5 0 0 0 .5-.5V10" />
            </svg>
            {isExporting ? 'Exporting…' : 'Export CSV'}
>>>>>>> Stashed changes
          </button>
        </div>
      </header>

      <div className="result-table-container">
<<<<<<< Updated upstream
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
=======
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
>>>>>>> Stashed changes
      </div>
    </div>
  );
}

// ─── Main ChatPage ─────────────────────────────────────────────────────────────
export default function ChatPage({ view = 'workspace' }) {
<<<<<<< Updated upstream
  const { user }    = useAuth();
  const role        = user?.role || 'viewer';

  const [activeQuery,  setActiveQuery]  = useState('');
  const [detectedType, setDetectedType] = useState('select');
  const [queryResult,  setQueryResult]  = useState(null);
  const [currentView,  setCurrentView]  = useState(view);
  const [initialText,  setInitialText]  = useState(() => {
    // Check if history page sent a re-run query
=======
  const { user } = useAuth();
  const role = user?.role || 'viewer';

  const [activeQuery,  setActiveQuery]  = useState('');
  const [queryResult,  setQueryResult]  = useState(null);
  const [currentView,  setCurrentView]  = useState(view);
  const [initialText,  setInitialText]  = useState(() => {
>>>>>>> Stashed changes
    const stored = sessionStorage.getItem('qm_rerun_query');
    if (stored) { sessionStorage.removeItem('qm_rerun_query'); return stored; }
    return '';
  });

  useEffect(() => { setCurrentView(view); }, [view]);

<<<<<<< Updated upstream
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
=======
  // Step 1: User runs Natural Language Query -> Call POST /api/queries
  const handleRunQuery = useCallback(async (text, inputType = 'text') => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setActiveQuery(trimmed);
    setInitialText('');

    setCurrentView('processing');
    try {
      const res = await generateQuery({ nl_query: trimmed, input_type: inputType });
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
>>>>>>> Stashed changes
  }, []);

  const handleNewQuery   = useCallback(() => { setCurrentView('workspace'); setActiveQuery(''); setQueryResult(null); }, []);
  const handleCancel     = useCallback(() => { setCurrentView('workspace'); }, []);
  const handleRegenerate = useCallback(async () => {
    if (!activeQuery) return;
    setCurrentView('processing');
    try {
<<<<<<< Updated upstream
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
=======
      const res = await generateQuery({ nl_query: activeQuery });
      setQueryResult(res);
      setCurrentView('approval');
    } catch (err) {
      console.error('Regenerate error:', err);
      setCurrentView('workspace');
    }
  }, [activeQuery]);

  if (currentView === 'workspace')  return <WorkspaceScreen onRunQuery={handleRunQuery} initialText={initialText} />;
  if (currentView === 'processing') return (
    <div className="processing-viewport">
      <div className="processing-header">
        <span className="processing-eyebrow">Generating & Validating SQL</span>
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
>>>>>>> Stashed changes

  return <WorkspaceScreen onRunQuery={handleRunQuery} initialText={initialText} />;
}
