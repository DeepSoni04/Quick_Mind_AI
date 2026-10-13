import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AmbientCanvas from '../components/AmbientCanvas';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css'; /* reuses login visual design */
import './SignUpPage.css';

export default function SignUpPage() {
  const [form, setForm]             = useState({ name: '', email: '', password: '', confirm: '' });
  const [errors, setErrors]         = useState({});
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();
  const { signup } = useAuth();

  const validate = () => {
    const e = {};
    if (!form.name.trim())    e.name = 'Full name is required.';
    if (!form.email.trim())   e.email = 'Email is required.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email address.';
    if (!form.password)       e.password = 'Password is required.';
    else if (form.password.length < 8) e.password = 'Password must be at least 8 characters.';
    if (form.confirm !== form.password) e.confirm = 'Passwords do not match.';
    return e;
  };

  const handleChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setErrors((prev) => ({ ...prev, [field]: '' }));
    setSubmitError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) { setErrors(errs); return; }
    setIsSubmitting(true);
    await new Promise((r) => setTimeout(r, 450));
    const result = signup(form.name.trim(), form.email.trim(), form.password);
    setIsSubmitting(false);
    if (result.success) {
      navigate('/workspace');
    } else {
      setSubmitError(result.error || 'Could not create account. Please try again.');
    }
  };

  return (
    <div className="login-viewport">
      <AmbientCanvas loginGradients={true} />
      <div className="login-orb login-orb--bottom-left" />
      <div className="login-orb login-orb--top-right" />

      <div className="login-panel signup-panel">
        {/* Left: Branding */}
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
          <p className="login-tagline">Create your account to get started.</p>
          <div className="login-bullets">
            <div className="login-bullet"><span className="login-bullet-dot" /><span className="login-bullet-text">Ask in plain English or Hinglish</span></div>
            <div className="login-bullet"><span className="login-bullet-dot" /><span className="login-bullet-text">Safe execution with confirmation</span></div>
            <div className="login-bullet"><span className="login-bullet-dot" /><span className="login-bullet-text">Role-based access control</span></div>
          </div>
        </div>

        {/* Right: Sign Up Form */}
        <div className="login-form-pane">
          <span className="login-eyebrow">Create Account</span>
          <form onSubmit={handleSubmit} className="login-form" noValidate>

            <div className="login-field">
              <label htmlFor="su-name" className="login-label">Full Name</label>
              <input id="su-name" type="text" className={`login-input ${errors.name ? 'login-input--error' : ''}`}
                value={form.name} onChange={handleChange('name')} placeholder="Your full name" />
              {errors.name && <span className="signup-field-error">{errors.name}</span>}
            </div>

            <div className="login-field">
              <label htmlFor="su-email" className="login-label">Email</label>
              <input id="su-email" type="email" className={`login-input ${errors.email ? 'login-input--error' : ''}`}
                value={form.email} onChange={handleChange('email')} placeholder="name@querymind.ai" />
              {errors.email && <span className="signup-field-error">{errors.email}</span>}
            </div>

            <div className="login-field">
              <label htmlFor="su-password" className="login-label">Password</label>
              <input id="su-password" type="password" className={`login-input ${errors.password ? 'login-input--error' : ''}`}
                value={form.password} onChange={handleChange('password')} placeholder="Min. 8 characters" />
              {errors.password && <span className="signup-field-error">{errors.password}</span>}
            </div>

            <div className="login-field">
              <label htmlFor="su-confirm" className="login-label">Confirm Password</label>
              <input id="su-confirm" type="password" className={`login-input ${errors.confirm ? 'login-input--error' : ''}`}
                value={form.confirm} onChange={handleChange('confirm')} placeholder="Repeat password" />
              {errors.confirm && <span className="signup-field-error">{errors.confirm}</span>}
            </div>

            {submitError && <div className="login-error">{submitError}</div>}

            <button type="submit" className="login-submit-btn" disabled={isSubmitting}>
              {isSubmitting ? 'Creating account…' : 'Create Account'}
            </button>

            <div className="login-signup-row">
              <span className="login-signup-text">Already have an account?</span>
              <Link to="/login" className="login-link login-link--signup">Sign in</Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
