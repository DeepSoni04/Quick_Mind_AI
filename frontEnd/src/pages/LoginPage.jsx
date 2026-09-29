import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AmbientCanvas from '../components/AmbientCanvas';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';

export default function LoginPage() {
  const [email, setEmail]           = useState('');
  const [password, setPassword]     = useState('');
  const [error, setError]           = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please enter your email and password.');
      return;
    }
    setError('');
    setIsSubmitting(true);
    await new Promise((r) => setTimeout(r, 380)); // realistic delay
    const result = login(email.trim(), password);
    setIsSubmitting(false);
    if (result.success) {
      navigate('/workspace');
    } else {
      setError('Invalid credentials. Please try again.');
    }
  };

  return (
    <div className="login-viewport">
      <AmbientCanvas loginGradients={true} />
      <div className="login-orb login-orb--bottom-left" />
      <div className="login-orb login-orb--top-right" />

      <div className="login-panel">
        {/* Left half: Branding */}
        <div className="login-branding">
          <div className="login-logo">
            <svg className="login-logo-svg" viewBox="0 0 40 40" width="40" height="40">
              <circle cx="20" cy="20" r="18" stroke="rgba(254,239,184,0.30)" strokeWidth="1" fill="none" />
              <circle cx="20" cy="20" r="11" stroke="rgba(254,239,184,0.50)" strokeWidth="1" fill="none" />
              <circle cx="20" cy="20" r="3.5" fill="rgba(254,239,184,0.90)" />
              <line x1="20" y1="2"  x2="20" y2="7"  stroke="rgba(254,239,184,0.35)" strokeWidth="1.2" strokeLinecap="round" />
              <line x1="20" y1="33" x2="20" y2="38" stroke="rgba(254,239,184,0.35)" strokeWidth="1.2" strokeLinecap="round" />
              <line x1="2"  y1="20" x2="7"  y2="20" stroke="rgba(254,239,184,0.35)" strokeWidth="1.2" strokeLinecap="round" />
              <line x1="33" y1="20" x2="38" y2="20" stroke="rgba(254,239,184,0.35)" strokeWidth="1.2" strokeLinecap="round" />
            </svg>
          </div>
          <h1 className="login-heading">QueryMind</h1>
          <p className="login-tagline">Natural language access to your database.</p>
          <div className="login-bullets">
            <div className="login-bullet"><span className="login-bullet-dot" /><span className="login-bullet-text">Ask in plain English or Hinglish</span></div>
            <div className="login-bullet"><span className="login-bullet-dot" /><span className="login-bullet-text">Safe execution with confirmation</span></div>
            <div className="login-bullet"><span className="login-bullet-dot" /><span className="login-bullet-text">Role-based access control</span></div>
          </div>


        </div>

        {/* Right half: Form */}
        <div className="login-form-pane">
          <span className="login-eyebrow">Authenticated Access</span>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="login-field">
              <label htmlFor="login-email" className="login-label">Email</label>
              <input
                id="login-email"
                type="email"
                className="login-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@querymind.ai"
                required
              />
            </div>
            <div className="login-field">
              <label htmlFor="login-password" className="login-label">Password</label>
              <input
                id="login-password"
                type="password"
                className="login-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>

            {/* Forgot password link */}
            <div className="login-forgot-row">
              <Link to="/forgot-password" className="login-link">Forgot password?</Link>
            </div>

            {error && <div className="login-error">{error}</div>}

            <button type="submit" className="login-submit-btn" disabled={isSubmitting}>
              {isSubmitting ? 'Authenticating…' : 'Access QueryMind'}
            </button>

            <div className="login-signup-row">
              <span className="login-signup-text">Don't have an account?</span>
              <Link to="/signup" className="login-link login-link--signup">Create account</Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
