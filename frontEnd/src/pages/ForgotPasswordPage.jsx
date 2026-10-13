import { useState } from 'react';
import { Link } from 'react-router-dom';
import AmbientCanvas from '../components/AmbientCanvas';
import './LoginPage.css';
import './ForgotPasswordPage.css';

export default function ForgotPasswordPage() {
  const [email, setEmail]   = useState('');
  const [phase, setPhase]   = useState('idle'); // 'idle' | 'sending' | 'sent'
  const [error, setError]   = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) { setError('Please enter your email address.'); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError('Enter a valid email address.'); return; }
    setError('');
    setPhase('sending');
    // TODO: replace mock with real API call
    await new Promise((r) => setTimeout(r, 1200));
    setPhase('sent');
  };

  return (
    <div className="login-viewport">
      <AmbientCanvas loginGradients={true} />
      <div className="login-orb login-orb--bottom-left" />
      <div className="login-orb login-orb--top-right" />

      <div className="forgot-panel">
        {/* Logo */}
        <div style={{ marginBottom: 28 }}>
          <svg viewBox="0 0 40 40" width="32" height="32">
            <circle cx="20" cy="20" r="18" stroke="rgba(184,39,76,0.35)" strokeWidth="1" fill="none" />
            <circle cx="20" cy="20" r="11" stroke="rgba(184,39,76,0.55)" strokeWidth="1" fill="none" />
            <circle cx="20" cy="20" r="3.5" fill="rgba(184,39,76,0.9)" />
          </svg>
        </div>

        <span className="login-eyebrow">Password Reset</span>

        {phase === 'sent' ? (
          /* Success state */
          <div className="forgot-success" style={{ animation: 'slideUp 0.4s ease-out both' }}>
            <div className="forgot-success-icon">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="rgba(42,157,92,0.9)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 10l5 5 8-8" />
              </svg>
            </div>
            <h2 className="forgot-success-title">Check your email</h2>
            <p className="forgot-success-body">
              If an account exists for <strong style={{ color: 'rgba(224,224,230,0.7)' }}>{email}</strong>,
              a reset link has been sent.
            </p>
            <Link to="/login" className="login-link" style={{ marginTop: 18, display: 'inline-block', fontSize: 13 }}>
              ← Back to login
            </Link>
          </div>
        ) : (
          /* Form state */
          <>
            <p className="forgot-description">
              Enter your account email and we'll send you a reset link.
            </p>
            <form onSubmit={handleSubmit} className="login-form" style={{ marginTop: 8 }}>
              <div className="login-field">
                <label htmlFor="fp-email" className="login-label">Email</label>
                <input
                  id="fp-email"
                  type="email"
                  className="login-input"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setError(''); }}
                  placeholder="name@querymind.ai"
                />
              </div>
              {error && <div className="login-error">{error}</div>}
              <button type="submit" className="login-submit-btn" disabled={phase === 'sending'}>
                {phase === 'sending' ? 'Sending…' : 'Send Reset Link'}
              </button>
              <div className="login-signup-row">
                <Link to="/login" className="login-link">← Back to login</Link>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
