import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Brain, Eye, EyeOff, ArrowRight, Sparkles, Database, Shield, Mic } from 'lucide-react';
import './LoginPage.css';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }
    setIsLoading(true);
    // simulate network delay
    setTimeout(() => {
      const result = login(email, password);
      if (result.success) {
        navigate('/chat');
      } else {
        setError('Invalid credentials');
      }
      setIsLoading(false);
    }, 800);
  };

  const features = [
    { icon: Database, title: 'Multi-Database', desc: 'MySQL, PostgreSQL & MongoDB' },
    { icon: Sparkles, title: 'AI-Powered', desc: 'Natural language to SQL' },
    { icon: Shield, title: 'Secure', desc: 'Query validation & safety' },
    { icon: Mic, title: 'Voice Input', desc: 'English & Hinglish support' },
  ];

  return (
    <div className="login-page">
      {/* Animated Background */}
      <div className="login-page__bg">
        <div className="login-page__orb login-page__orb--1" />
        <div className="login-page__orb login-page__orb--2" />
        <div className="login-page__orb login-page__orb--3" />
        <div className="login-page__grid" />
      </div>

      <div className="login-page__container">
        {/* Left — Hero Panel */}
        <div className="login-page__hero">
          <div className="login-page__hero-content">
            <div className="login-page__logo animate-float">
              <Brain size={48} />
            </div>
            <h1 className="login-page__hero-title">
              Query<span className="gradient-text">Mind</span> AI
            </h1>
            <p className="login-page__hero-desc">
              Transform natural language into powerful database queries.
              Ask questions in English or Hinglish — no SQL knowledge required.
            </p>

            <div className="login-page__features">
              {features.map((f, i) => (
                <div key={i} className="login-page__feature" style={{ animationDelay: `${i * 0.1}s` }}>
                  <div className="login-page__feature-icon">
                    <f.icon size={20} />
                  </div>
                  <div>
                    <div className="login-page__feature-title">{f.title}</div>
                    <div className="login-page__feature-desc">{f.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right — Login Form */}
        <div className="login-page__form-panel">
          <div className="login-page__form-wrapper">
            <div className="login-page__form-header">
              <h2>Welcome Back</h2>
              <p>Sign in to access your workspace</p>
            </div>

            <form onSubmit={handleSubmit} className="login-page__form">
              {error && <div className="login-page__error">{error}</div>}

              <div className="login-page__field">
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  className="input-field"
                  placeholder="you@querymind.ai"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </div>

              <div className="login-page__field">
                <label htmlFor="password">Password</label>
                <div className="login-page__password-wrap">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    className="input-field"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    className="login-page__eye"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="login-page__options">
                <label className="login-page__remember">
                  <input type="checkbox" />
                  <span>Remember me</span>
                </label>
                <a href="#" className="login-page__forgot">Forgot password?</a>
              </div>

              <button
                type="submit"
                className={`btn btn-primary btn-lg login-page__submit ${isLoading ? 'login-page__submit--loading' : ''}`}
                disabled={isLoading}
              >
                {isLoading ? (
                  <div className="login-page__spinner" />
                ) : (
                  <>
                    Sign In
                    <ArrowRight size={18} />
                  </>
                )}
              </button>
            </form>

            <div className="login-page__demo">
              <p>Demo accounts:</p>
              <div className="login-page__demo-accounts">
                <button onClick={() => { setEmail('deep@querymind.ai'); setPassword('demo'); }}>
                  Admin
                </button>
                <button onClick={() => { setEmail('heer@querymind.ai'); setPassword('demo'); }}>
                  Analyst
                </button>
                <button onClick={() => { setEmail('neel@querymind.ai'); setPassword('demo'); }}>
                  Viewer
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
