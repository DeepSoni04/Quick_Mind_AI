import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Send, Mic, MicOff, Sparkles, Copy, Check, Download,
  ThumbsUp, ThumbsDown, RotateCcw, Database, Table2, ChevronDown
} from 'lucide-react';
import './ChatPage.css';

// Mock response generator
function generateMockResponse(query) {
  const lower = query.toLowerCase();
  if (lower.includes('employee') || lower.includes('staff') || lower.includes('karmachari')) {
    return {
      sql: `SELECT e.employee_id, e.first_name, e.last_name, d.department_name, e.salary\nFROM employees e\nJOIN departments d ON e.department_id = d.department_id\nORDER BY e.salary DESC\nLIMIT 10;`,
      summary: 'Here are the top 10 employees by salary across all departments.',
      table: {
        headers: ['ID', 'First Name', 'Last Name', 'Department', 'Salary'],
        rows: [
          ['101', 'Rahul', 'Sharma', 'Engineering', '₹1,85,000'],
          ['102', 'Priya', 'Patel', 'Marketing', '₹1,62,000'],
          ['103', 'Amit', 'Gupta', 'Finance', '₹1,55,000'],
          ['104', 'Sneha', 'Reddy', 'Engineering', '₹1,48,000'],
          ['105', 'Vikram', 'Singh', 'HR', '₹1,35,000'],
        ],
      },
      rowCount: 5,
      executionTime: '0.042s',
      database: 'hr_production',
    };
  }
  if (lower.includes('patient') || lower.includes('hospital') || lower.includes('doctor')) {
    return {
      sql: `SELECT p.patient_id, p.patient_name, p.admission_date, w.ward_name, p.status\nFROM patients p\nJOIN wards w ON p.ward_id = w.ward_id\nWHERE p.status = 'admitted'\nORDER BY p.admission_date DESC;`,
      summary: 'Currently 8 patients are admitted across 4 wards. ICU has the highest occupancy.',
      table: {
        headers: ['Patient ID', 'Name', 'Admission Date', 'Ward', 'Status'],
        rows: [
          ['P-2041', 'Arjun Mehta', '2026-08-14', 'ICU', 'Critical'],
          ['P-2039', 'Kavita Joshi', '2026-08-13', 'General', 'Stable'],
          ['P-2038', 'Rajesh Kumar', '2026-08-12', 'Surgical', 'Recovering'],
          ['P-2035', 'Meera Iyer', '2026-08-10', 'Pediatrics', 'Stable'],
        ],
      },
      rowCount: 4,
      executionTime: '0.038s',
      database: 'hospital_db',
    };
  }
  if (lower.includes('stock') || lower.includes('inventory') || lower.includes('product')) {
    return {
      sql: `SELECT p.product_id, p.product_name, p.quantity, p.reorder_level,\n  CASE WHEN p.quantity <= p.reorder_level THEN 'Low Stock' ELSE 'OK' END AS status\nFROM products p\nORDER BY p.quantity ASC\nLIMIT 10;`,
      summary: '3 products are below reorder level and need restocking immediately.',
      table: {
        headers: ['Product ID', 'Name', 'Qty', 'Reorder Level', 'Status'],
        rows: [
          ['SKU-001', 'Wireless Mouse', '5', '20', 'Low Stock'],
          ['SKU-014', 'USB-C Cable', '8', '30', 'Low Stock'],
          ['SKU-009', 'Monitor Stand', '12', '15', 'Low Stock'],
          ['SKU-022', 'Keyboard', '45', '20', 'OK'],
          ['SKU-031', 'Webcam HD', '62', '25', 'OK'],
        ],
      },
      rowCount: 5,
      executionTime: '0.029s',
      database: 'inventory_db',
    };
  }
  // Default
  return {
    sql: `SELECT *\nFROM information_schema.tables\nWHERE table_schema = 'public'\nORDER BY table_name;`,
    summary: `I understood your query: "${query}". Here's what I found in the connected database.`,
    table: {
      headers: ['Table Name', 'Rows', 'Size', 'Last Updated'],
      rows: [
        ['users', '1,245', '2.4 MB', '2026-08-15'],
        ['orders', '8,932', '12.1 MB', '2026-08-15'],
        ['products', '456', '1.8 MB', '2026-08-14'],
      ],
    },
    rowCount: 3,
    executionTime: '0.015s',
    database: 'main_db',
  };
}

export default function ChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      type: 'bot',
      text: `Hi ${user?.name || 'there'}! 👋 I'm QueryMind AI — your natural language database assistant.\n\nAsk me anything about your connected databases in English or Hinglish, and I'll generate the SQL for you.\n\nTry something like:\n• "Show me all employees with salary above 1 lakh"\n• "Kitne patients abhi admitted hain?"\n• "Which products are low on stock?"`,
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = {
      id: Date.now().toString(),
      type: 'user',
      text: input.trim(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const result = generateMockResponse(userMsg.text);
      const botMsg = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        text: result.summary,
        sql: result.sql,
        table: result.table,
        meta: {
          rowCount: result.rowCount,
          executionTime: result.executionTime,
          database: result.database,
        },
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMsg]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleVoice = () => {
    if (isListening) {
      setIsListening(false);
      return;
    }
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-IN';
      recognition.interimResults = false;
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      recognition.start();
      setIsListening(true);
    } else {
      alert('Speech recognition is not supported in this browser.');
    }
  };

  const copySQL = (sql, id) => {
    navigator.clipboard.writeText(sql);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const quickQueries = [
    'Show all employees with salary above 1 lakh',
    'Kitne patients abhi admitted hain?',
    'Which products are low on stock?',
    'Show me today\'s sales summary',
  ];

  return (
    <div className="chat-page">
      {/* Header */}
      <header className="chat-page__header glass">
        <div className="chat-page__header-left">
          <Sparkles size={20} className="chat-page__sparkle" />
          <div>
            <h1>Query Chat</h1>
            <p>Ask questions in English or Hinglish</p>
          </div>
        </div>
        <div className="chat-page__header-right">
          <div className="chat-page__db-indicator">
            <Database size={14} />
            <span>3 databases connected</span>
            <span className="chat-page__db-dot" />
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="chat-page__messages">
        {messages.length === 1 && (
          <div className="chat-page__quick-queries animate-fade-in">
            <p>Quick queries to try:</p>
            <div className="chat-page__quick-grid">
              {quickQueries.map((q, i) => (
                <button key={i} className="chat-page__quick-btn" onClick={() => setInput(q)}>
                  <Sparkles size={14} />
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`chat-page__msg chat-page__msg--${msg.type} animate-slide-up`}>
            {msg.type === 'bot' && (
              <div className="chat-page__msg-avatar">
                <Sparkles size={16} />
              </div>
            )}
            <div className="chat-page__msg-content">
              <div className="chat-page__msg-text">{msg.text}</div>

              {/* SQL Block */}
              {msg.sql && (
                <div className="chat-page__sql-block">
                  <div className="chat-page__sql-header">
                    <span>Generated SQL</span>
                    <button onClick={() => copySQL(msg.sql, msg.id)} className="chat-page__sql-copy">
                      {copiedId === msg.id ? <Check size={14} /> : <Copy size={14} />}
                      {copiedId === msg.id ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <pre className="chat-page__sql-code"><code>{msg.sql}</code></pre>
                </div>
              )}

              {/* Result Table */}
              {msg.table && (
                <div className="chat-page__table-wrap">
                  <div className="chat-page__table-header">
                    <Table2 size={14} />
                    <span>Query Results</span>
                    {msg.meta && (
                      <span className="chat-page__table-meta">
                        {msg.meta.rowCount} rows · {msg.meta.executionTime} · {msg.meta.database}
                      </span>
                    )}
                  </div>
                  <div className="chat-page__table-scroll">
                    <table className="chat-page__table">
                      <thead>
                        <tr>
                          {msg.table.headers.map((h, i) => (
                            <th key={i}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {msg.table.rows.map((row, ri) => (
                          <tr key={ri}>
                            {row.map((cell, ci) => (
                              <td key={ci}>
                                {cell === 'Low Stock' || cell === 'Critical' ? (
                                  <span className="badge badge-danger">{cell}</span>
                                ) : cell === 'Stable' || cell === 'OK' ? (
                                  <span className="badge badge-success">{cell}</span>
                                ) : cell === 'Recovering' ? (
                                  <span className="badge badge-warning">{cell}</span>
                                ) : (
                                  cell
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Actions */}
              {msg.type === 'bot' && msg.sql && (
                <div className="chat-page__msg-actions">
                  <button className="btn btn-ghost btn-sm"><ThumbsUp size={14} /> Helpful</button>
                  <button className="btn btn-ghost btn-sm"><ThumbsDown size={14} /> Not right</button>
                  <button className="btn btn-ghost btn-sm"><RotateCcw size={14} /> Regenerate</button>
                  <button className="btn btn-ghost btn-sm"><Download size={14} /> Export PDF</button>
                </div>
              )}

              <div className="chat-page__msg-time">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>

            {msg.type === 'user' && (
              <div className="chat-page__msg-avatar chat-page__msg-avatar--user">
                {user?.avatar}
              </div>
            )}
          </div>
        ))}

        {isTyping && (
          <div className="chat-page__msg chat-page__msg--bot animate-fade-in">
            <div className="chat-page__msg-avatar"><Sparkles size={16} /></div>
            <div className="chat-page__msg-content">
              <div className="chat-page__typing">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="chat-page__input-area glass">
        <div className="chat-page__input-wrap">
          <textarea
            ref={inputRef}
            className="chat-page__input"
            placeholder="Ask a question in English or Hinglish..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <div className="chat-page__input-actions">
            <button
              className={`btn btn-icon btn-ghost chat-page__mic ${isListening ? 'chat-page__mic--active' : ''}`}
              onClick={toggleVoice}
              title={isListening ? 'Stop listening' : 'Voice input'}
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
            <button
              className="btn btn-icon btn-primary chat-page__send"
              onClick={handleSend}
              disabled={!input.trim()}
              title="Send query"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
        <p className="chat-page__disclaimer">
          QueryMind AI generates SQL from your questions. Always review the SQL before executing on production databases.
        </p>
      </div>
    </div>
  );
}
