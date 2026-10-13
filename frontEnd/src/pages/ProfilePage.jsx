import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import './ProfilePage.css';

// Clean inline SVGs for zero dependencies and high performance
const IconUser = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M15 15.5v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 3 14v1.5" />
    <circle cx="9" cy="5.5" r="3.5" />
  </svg>
);

const IconShield = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 1.5L15 4.5v4c0 4-6 7.5-6 7.5S3 12.5 3 8.5v-4z" />
    <polyline points="6.5 9 8.5 11 12 7.5" />
  </svg>
);

const IconKey = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="6" cy="6" r="3.5" />
    <line x1="8.5" y1="8.5" x2="15" y2="15" />
    <line x1="12" y1="12" x2="14.5" y2="9.5" />
    <line x1="13.5" y1="13.5" x2="16" y2="11" />
  </svg>
);

const IconActivity = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16.5 9 13.5 9 11.25 15 6.75 3 4.5 9 1.5 9" />
  </svg>
);

const IconCheck = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="2.5 7 5.5 10 11.5 4" />
  </svg>
);

const IconCopy = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4.5" y="4.5" width="7.5" height="7.5" rx="1.5" />
    <path d="M3 9.5H2.5A1.5 1.5 0 0 1 1 8V2.5A1.5 1.5 0 0 1 2.5 1H8a1.5 1.5 0 0 1 1.5 1.5V3" />
  </svg>
);

const IconRefresh = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12.5 2.5v3.5h-3.5" />
    <path d="M1.5 11.5V8h3.5" />
    <path d="M10.8 5.2A5 5 0 0 0 2.6 6.3L1.5 8" />
    <path d="M3.2 8.8a5 5 0 0 0 8.2-1.1l1.1-1.7" />
  </svg>
);

const IconEye = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 7s2.5-4.5 6-4.5 6 4.5 6 4.5-2.5 4.5-6 4.5-6-4.5-6-4.5z" />
    <circle cx="7" cy="7" r="2" />
  </svg>
);

const IconEyeOff = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.5 10.5L3.5 3.5" />
    <path d="M6 3.6A6.1 6.1 0 0 1 7 3.5c3.5 0 6 3.5 6 3.5a10.8 10.8 0 0 1-2.2 2.6" />
    <path d="M8.5 8.5a2 2 0 0 1-2.8-2.8" />
    <path d="M1 7s1.3-2.3 3.5-3.3" />
    <path d="M3.5 10.5A10.8 10.8 0 0 0 7 11.5c3.5 0 6-3.5 6-3.5a11 11 0 0 0-1.5-1.9" />
  </svg>
);

const IconDevices = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="2" width="12" height="8.5" rx="1.5" />
    <line x1="5.5" y1="14" x2="10.5" y2="14" />
    <line x1="8" y1="10.5" x2="8" y2="14" />
  </svg>
);

export default function ProfilePage() {
  const {
    user,
    updateProfile,
    changePassword,
    toggleTwoFactor,
    regenerateApiToken,
  } = useAuth();

  const [activeTab, setActiveTab] = useState('profile');
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // Profile edit form state
  const [profileForm, setProfileForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    title: user?.title || 'Data Analyst',
    department: user?.department || 'Analytics & Data Platforms',
    bio: user?.bio || 'QueryMind database engineer exploring automated NL query models.',
    phone: user?.phone || '+91 98765 43210',
    location: user?.location || 'Ahmedabad, India',
    avatar: user?.avatar || 'DS',
  });

  const [isSavingProfile, setIsSavingProfile] = useState(false);

  // Security password form state
  const [pwForm, setPwForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [pwError, setPwError] = useState('');
  const [isUpdatingPw, setIsUpdatingPw] = useState(false);

  // API Token state
  const [showToken, setShowToken] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);
  const [copiedCurl, setCopiedCurl] = useState(false);

  // Active sessions mock state
  const [sessions, setSessions] = useState([
    {
      id: 1,
      device: 'Windows 11 · Chrome 124',
      location: 'Ahmedabad, India',
      ip: '103.24.120.45',
      time: 'Active now',
      isCurrent: true,
    },
    {
      id: 2,
      device: 'macOS Sonoma · Safari 17',
      location: 'Mumbai, India',
      ip: '115.112.98.14',
      time: '2 days ago',
      isCurrent: false,
    },
    {
      id: 3,
      device: 'Apple iPhone 15 · Safari Mobile',
      location: 'Ahmedabad, India',
      ip: '103.24.120.89',
      time: '5 days ago',
      isCurrent: false,
    },
  ]);

  const triggerToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => {
      setToast((prev) => ({ ...prev, show: false }));
    }, 3200);
  };

  /* ── Profile Update Handler ── */
  const handleSaveProfile = (e) => {
    e.preventDefault();
    if (!profileForm.name.trim()) {
      triggerToast('Full name cannot be blank', 'error');
      return;
    }
    if (!profileForm.email.trim()) {
      triggerToast('Email address cannot be blank', 'error');
      return;
    }

    setIsSavingProfile(true);
    setTimeout(() => {
      const result = updateProfile({
        name: profileForm.name.trim(),
        email: profileForm.email.trim(),
        title: profileForm.title.trim(),
        department: profileForm.department.trim(),
        bio: profileForm.bio.trim(),
        phone: profileForm.phone.trim(),
        location: profileForm.location.trim(),
      });
      setIsSavingProfile(false);
      if (result.success) {
        triggerToast('Profile updated successfully!');
      } else {
        triggerToast(result.error || 'Failed to update profile', 'error');
      }
    }, 350);
  };

  /* ── Reset Profile Changes ── */
  const handleResetProfile = () => {
    setProfileForm({
      name: user?.name || '',
      email: user?.email || '',
      title: user?.title || 'Data Analyst',
      department: user?.department || 'Analytics & Data Platforms',
      bio: user?.bio || '',
      phone: user?.phone || '+91 98765 43210',
      location: user?.location || 'Ahmedabad, India',
      avatar: user?.avatar || 'DS',
    });
    triggerToast('Profile form reset', 'info');
  };

  /* ── Password Change Handler ── */
  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    setPwError('');

    if (!pwForm.currentPassword) {
      setPwError('Please enter your current password.');
      return;
    }
    if (!pwForm.newPassword || pwForm.newPassword.length < 6) {
      setPwError('New password must be at least 6 characters.');
      return;
    }
    if (pwForm.newPassword !== pwForm.confirmPassword) {
      setPwError('New passwords do not match.');
      return;
    }

    setIsUpdatingPw(true);
    setTimeout(() => {
      const res = changePassword(pwForm.currentPassword, pwForm.newPassword);
      setIsUpdatingPw(false);
      if (res.success) {
        setPwForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
        triggerToast('Password changed successfully!');
      } else {
        setPwError(res.error || 'Failed to update password');
      }
    }, 400);
  };

  /* ── 2FA Toggle Handler ── */
  const handleToggle2FA = () => {
    const newState = toggleTwoFactor();
    triggerToast(newState ? 'Two-Factor Authentication enabled!' : 'Two-Factor Authentication disabled');
  };

  /* ── Token Copy Handler ── */
  const handleCopyToken = () => {
    if (user?.apiToken) {
      navigator.clipboard.writeText(user.apiToken);
      setCopiedToken(true);
      triggerToast('API token copied to clipboard!');
      setTimeout(() => setCopiedToken(false), 2000);
    }
  };

  /* ── Regenerate Token Handler ── */
  const handleRegenerateToken = () => {
    if (window.confirm('Regenerate personal API token? Existing scripts using this key will immediately lose access.')) {
      const newToken = regenerateApiToken();
      if (newToken) {
        triggerToast('New API token generated successfully!');
      }
    }
  };

  /* ── Copy cURL snippet ── */
  const curlSnippet = `curl -X POST https://api.querymind.ai/v1/query \\
  -H "Authorization: Bearer ${user?.apiToken || 'qm_live_demo'}" \\
  -H "Content-Type: application/json" \\
  -d '{"database": "student_database", "prompt": "Find top 10 students by GPA"}'`;

  const handleCopyCurl = () => {
    navigator.clipboard.writeText(curlSnippet);
    setCopiedCurl(true);
    triggerToast('cURL example copied to clipboard!');
    setTimeout(() => setCopiedCurl(false), 2000);
  };

  /* ── Terminate Other Sessions ── */
  const handleRevokeSessions = () => {
    setSessions((prev) => prev.filter((s) => s.isCurrent));
    triggerToast('All other sessions terminated successfully!');
  };

  // Password strength calculator
  const getPasswordStrength = (pwd) => {
    if (!pwd) return { score: 0, label: 'None', color: 'transparent' };
    let score = 0;
    if (pwd.length >= 6) score += 1;
    if (pwd.length >= 10) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;

    if (score <= 2) return { score: 30, label: 'Weak', color: 'var(--text-red)' };
    if (score <= 4) return { score: 70, label: 'Good', color: 'var(--accent-amber)' };
    return { score: 100, label: 'Strong', color: 'var(--accent-green)' };
  };

  const pwStrength = getPasswordStrength(pwForm.newPassword);

  const TABS = [
    { id: 'profile', label: 'Profile Details', Icon: IconUser },
    { id: 'security', label: 'Security & 2FA', Icon: IconShield },
    { id: 'tokens', label: 'API & Developer', Icon: IconKey },
    { id: 'activity', label: 'Roles & Activity', Icon: IconActivity },
  ];

  return (
    <div className="profile-viewport">
      {/* ── Toast notification ── */}
      {toast.show && (
        <div className={`profile-toast profile-toast--${toast.type}`}>
          <span className="profile-toast__icon">
            {toast.type === 'success' ? <IconCheck /> : 'ℹ'}
          </span>
          <span className="profile-toast__msg">{toast.message}</span>
        </div>
      )}

      {/* ── Page Header ── */}
      <header className="profile-header">
        <div className="profile-header__left">
          <h2>Account Profile</h2>
          <p>Manage your identity, personal details, security credentials, and API access.</p>
        </div>
        <div className="profile-header__right">
          <span className="profile-status-badge">
            <span className="profile-status-dot" />
            Active Session
          </span>
        </div>
      </header>

      <div className="profile-content">
        {/* ── Hero Profile Card ── */}
        <div className="profile-hero-card">
          <div className="profile-hero-card__glow" />
          <div className="profile-hero-card__left">
            <div className="profile-avatar-wrapper">
              <div className="profile-avatar">
                {user?.avatar || 'QM'}
              </div>
              <span className="profile-avatar-indicator" title="User online" />
            </div>
            <div className="profile-hero-info">
              <div className="profile-hero-name-row">
                <h1 className="profile-hero-name">{user?.name || 'Administrator'}</h1>
                <span className={`profile-role-pill profile-role-pill--${user?.role || 'viewer'}`}>
                  {user?.role || 'viewer'}
                </span>
              </div>
              <div className="profile-hero-title">
                {user?.title || 'Data Platform Engineer'} · <span className="profile-hero-dept">{user?.department || 'QueryMind'}</span>
              </div>
              <div className="profile-hero-meta">
                <span className="profile-hero-meta-item">
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.4">
                    <path d="M1.5 2.5h10a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1h-10a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1z" />
                    <polyline points="1.5 3.5 6.5 7.5 11.5 3.5" />
                  </svg>
                  {user?.email || 'admin@querymind.ai'}
                </span>
                <span className="profile-hero-meta-item">
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.4">
                    <path d="M6.5 1.5A3.5 3.5 0 0 0 3 5c0 2.5 3.5 6.5 3.5 6.5s3.5-4 3.5-6.5a3.5 3.5 0 0 0-3.5-3.5z" />
                    <circle cx="6.5" cy="5" r="1.2" />
                  </svg>
                  {user?.location || 'Ahmedabad, India'}
                </span>
                <span className="profile-hero-meta-item">
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.4">
                    <circle cx="6.5" cy="6.5" r="5" />
                    <polyline points="6.5 3.5 6.5 6.5 8.5 7.5" />
                  </svg>
                  Joined {user?.joinedDate || '2026'}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="profile-hero-metrics">
            <div className="profile-metric-box">
              <span className="profile-metric-val">{user?.stats?.queriesRun ?? 142}</span>
              <span className="profile-metric-lbl">Queries Executed</span>
            </div>
            <div className="profile-metric-box">
              <span className="profile-metric-val">{user?.stats?.savedQueries ?? 18}</span>
              <span className="profile-metric-lbl">Saved Queries</span>
            </div>
            <div className="profile-metric-box">
              <span className="profile-metric-val">{user?.stats?.connectedClusters ?? 3}</span>
              <span className="profile-metric-lbl">DB Clusters</span>
            </div>
            <div className="profile-metric-box">
              <span className="profile-metric-val">{user?.stats?.successRate ?? '99.4%'}</span>
              <span className="profile-metric-lbl">Query Success</span>
            </div>
          </div>
        </div>

        {/* ── Navigation Tabs ── */}
        <div className="profile-tabs">
          {TABS.map(({ id, label, Icon }) => (
            <button
              key={id}
              type="button"
              className={`profile-tab ${activeTab === id ? 'profile-tab--active' : ''}`}
              onClick={() => setActiveTab(id)}
            >
              <Icon />
              <span>{label}</span>
            </button>
          ))}
        </div>

        {/* ══════════════════════════════════════════════════════════════
            TAB 1: Profile Information
            ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'profile' && (
          <div className="profile-tab-content" style={{ animation: 'fadeRow 0.3s ease-out both' }}>
            <form onSubmit={handleSaveProfile} className="profile-form-grid">
              <div className="profile-card">
                <div className="profile-card-header">
                  <h3>Personal Information</h3>
                  <p>Update your display name, contact information, and role designation.</p>
                </div>

                <div className="profile-form-row profile-form-row--two-col">
                  <div className="profile-field">
                    <label className="profile-field-label">Full Name</label>
                    <input
                      type="text"
                      className="profile-input"
                      value={profileForm.name}
                      onChange={(e) => setProfileForm((p) => ({ ...p, name: e.target.value }))}
                      placeholder="e.g. Deep Soni"
                      required
                    />
                  </div>
                  <div className="profile-field">
                    <label className="profile-field-label">Email Address</label>
                    <input
                      type="email"
                      className="profile-input"
                      value={profileForm.email}
                      onChange={(e) => setProfileForm((p) => ({ ...p, email: e.target.value }))}
                      placeholder="e.g. deep@querymind.ai"
                      required
                    />
                  </div>
                </div>

                <div className="profile-form-row profile-form-row--two-col">
                  <div className="profile-field">
                    <label className="profile-field-label">Job Title / Designation</label>
                    <input
                      type="text"
                      className="profile-input"
                      value={profileForm.title}
                      onChange={(e) => setProfileForm((p) => ({ ...p, title: e.target.value }))}
                      placeholder="e.g. Lead Data Architect"
                    />
                  </div>
                  <div className="profile-field">
                    <label className="profile-field-label">Department / Team</label>
                    <input
                      type="text"
                      className="profile-input"
                      value={profileForm.department}
                      onChange={(e) => setProfileForm((p) => ({ ...p, department: e.target.value }))}
                      placeholder="e.g. Data Platform & AI"
                    />
                  </div>
                </div>

                <div className="profile-form-row profile-form-row--two-col">
                  <div className="profile-field">
                    <label className="profile-field-label">Phone Contact</label>
                    <input
                      type="text"
                      className="profile-input"
                      value={profileForm.phone}
                      onChange={(e) => setProfileForm((p) => ({ ...p, phone: e.target.value }))}
                      placeholder="+91 98765 43210"
                    />
                  </div>
                  <div className="profile-field">
                    <label className="profile-field-label">Location / City</label>
                    <input
                      type="text"
                      className="profile-input"
                      value={profileForm.location}
                      onChange={(e) => setProfileForm((p) => ({ ...p, location: e.target.value }))}
                      placeholder="Ahmedabad, India"
                    />
                  </div>
                </div>

                <div className="profile-form-row">
                  <div className="profile-field">
                    <div className="profile-field-header-row">
                      <label className="profile-field-label">Bio / Profile Summary</label>
                      <span className="profile-char-count">{profileForm.bio.length} / 250</span>
                    </div>
                    <textarea
                      rows={3}
                      className="profile-textarea"
                      maxLength={250}
                      value={profileForm.bio}
                      onChange={(e) => setProfileForm((p) => ({ ...p, bio: e.target.value }))}
                      placeholder="Brief note on your focus areas and database expertise..."
                    />
                  </div>
                </div>

                <div className="profile-card-footer">
                  <button
                    type="button"
                    className="profile-btn profile-btn--secondary"
                    onClick={handleResetProfile}
                    disabled={isSavingProfile}
                  >
                    Discard Changes
                  </button>
                  <button
                    type="submit"
                    className="profile-btn profile-btn--primary"
                    disabled={isSavingProfile}
                  >
                    {isSavingProfile ? (
                      <>
                        <span className="profile-spinner" /> Saving…
                      </>
                    ) : (
                      <>
                        <IconCheck /> Save Changes
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════
            TAB 2: Security & Password
            ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'security' && (
          <div className="profile-tab-content" style={{ animation: 'fadeRow 0.3s ease-out both' }}>
            <div className="profile-cards-stack">
              {/* Change Password Card */}
              <div className="profile-card">
                <div className="profile-card-header">
                  <h3>Change Password</h3>
                  <p>Choose a strong password with letters, numbers, and symbols.</p>
                </div>

                <form onSubmit={handlePasswordSubmit}>
                  {pwError && <div className="profile-alert profile-alert--error">{pwError}</div>}

                  <div className="profile-form-row">
                    <div className="profile-field">
                      <label className="profile-field-label">Current Password</label>
                      <div className="profile-input-wrapper">
                        <input
                          type={showCurrentPw ? 'text' : 'password'}
                          className="profile-input"
                          value={pwForm.currentPassword}
                          onChange={(e) => setPwForm((p) => ({ ...p, currentPassword: e.target.value }))}
                          placeholder="Enter your current password"
                        />
                        <button
                          type="button"
                          className="profile-input-icon-btn"
                          onClick={() => setShowCurrentPw(!showCurrentPw)}
                        >
                          {showCurrentPw ? <IconEyeOff /> : <IconEye />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="profile-form-row profile-form-row--two-col">
                    <div className="profile-field">
                      <label className="profile-field-label">New Password</label>
                      <div className="profile-input-wrapper">
                        <input
                          type={showNewPw ? 'text' : 'password'}
                          className="profile-input"
                          value={pwForm.newPassword}
                          onChange={(e) => setPwForm((p) => ({ ...p, newPassword: e.target.value }))}
                          placeholder="At least 6 characters"
                        />
                        <button
                          type="button"
                          className="profile-input-icon-btn"
                          onClick={() => setShowNewPw(!showNewPw)}
                        >
                          {showNewPw ? <IconEyeOff /> : <IconEye />}
                        </button>
                      </div>

                      {/* Password strength bar */}
                      {pwForm.newPassword && (
                        <div className="profile-pw-meter">
                          <div
                            className="profile-pw-meter-bar"
                            style={{ width: `${pwStrength.score}%`, backgroundColor: pwStrength.color }}
                          />
                          <span className="profile-pw-meter-lbl" style={{ color: pwStrength.color }}>
                            {pwStrength.label}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="profile-field">
                      <label className="profile-field-label">Confirm New Password</label>
                      <input
                        type="password"
                        className="profile-input"
                        value={pwForm.confirmPassword}
                        onChange={(e) => setPwForm((p) => ({ ...p, confirmPassword: e.target.value }))}
                        placeholder="Re-type new password"
                      />
                    </div>
                  </div>

                  <div className="profile-card-footer">
                    <button
                      type="submit"
                      className="profile-btn profile-btn--primary"
                      disabled={isUpdatingPw}
                    >
                      {isUpdatingPw ? 'Updating…' : 'Update Password'}
                    </button>
                  </div>
                </form>
              </div>

              {/* Two-Factor Authentication Card */}
              <div className="profile-card">
                <div className="profile-card-header">
                  <h3>Two-Factor Authentication (2FA)</h3>
                  <p>Add a robust layer of security using TOTP authenticator apps (Google Authenticator, Authy).</p>
                </div>

                <div className="profile-toggle-row">
                  <div className="profile-toggle-info">
                    <div className="profile-toggle-title">
                      TOTP Authentication Code
                      <span className={`profile-status-pill ${user?.twoFactorEnabled ? 'profile-status-pill--active' : ''}`}>
                        {user?.twoFactorEnabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <div className="profile-toggle-desc">
                      Require a 6-digit confirmation code generated by your mobile device whenever logging in.
                    </div>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={!!user?.twoFactorEnabled}
                    className={`profile-switch ${user?.twoFactorEnabled ? 'profile-switch--on' : 'profile-switch--off'}`}
                    onClick={handleToggle2FA}
                  >
                    <span className="profile-switch-thumb" />
                  </button>
                </div>
              </div>

              {/* Active Sessions Card */}
              <div className="profile-card">
                <div className="profile-card-header profile-card-header--row">
                  <div>
                    <h3>Active Login Sessions</h3>
                    <p>Devices and browsers currently authenticated to this account.</p>
                  </div>
                  {sessions.length > 1 && (
                    <button
                      type="button"
                      className="profile-btn profile-btn--danger-sm"
                      onClick={handleRevokeSessions}
                    >
                      Revoke Other Sessions
                    </button>
                  )}
                </div>

                <div className="profile-sessions-list">
                  {sessions.map((sess) => (
                    <div key={sess.id} className="profile-session-item">
                      <div className="profile-session-icon">
                        <IconDevices />
                      </div>
                      <div className="profile-session-info">
                        <div className="profile-session-name">
                          {sess.device}
                          {sess.isCurrent && <span className="profile-current-badge">Current Device</span>}
                        </div>
                        <div className="profile-session-meta">
                          {sess.location} · IP {sess.ip} · {sess.time}
                        </div>
                      </div>
                      <span className={`profile-session-status ${sess.isCurrent ? 'profile-session-status--live' : ''}`} />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════
            TAB 3: API & Developer Tokens
            ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'tokens' && (
          <div className="profile-tab-content" style={{ animation: 'fadeRow 0.3s ease-out both' }}>
            <div className="profile-cards-stack">
              <div className="profile-card">
                <div className="profile-card-header profile-card-header--row">
                  <div>
                    <h3>Personal Access Token</h3>
                    <p>Bearer credentials for scripting, backend microservices, or CLI queries.</p>
                  </div>
                  <button
                    type="button"
                    className="profile-btn profile-btn--secondary-sm"
                    onClick={handleRegenerateToken}
                  >
                    <IconRefresh /> Regenerate
                  </button>
                </div>

                <div className="profile-token-box">
                  <div className="profile-token-display">
                    <span className="profile-token-string">
                      {showToken
                        ? user?.apiToken || 'qm_live_demo1234567890abcdef'
                        : (user?.apiToken ? `${user.apiToken.slice(0, 10)}••••••••••••••••••••` : 'qm_live_••••••••••••••••••••')}
                    </span>
                  </div>
                  <div className="profile-token-actions">
                    <button
                      type="button"
                      className="profile-btn-icon"
                      onClick={() => setShowToken(!showToken)}
                      title={showToken ? 'Hide token' : 'Reveal token'}
                    >
                      {showToken ? <IconEyeOff /> : <IconEye />}
                    </button>
                    <button
                      type="button"
                      className={`profile-btn profile-btn--copy ${copiedToken ? 'profile-btn--copied' : ''}`}
                      onClick={handleCopyToken}
                    >
                      {copiedToken ? (
                        <>
                          <IconCheck /> Copied
                        </>
                      ) : (
                        <>
                          <IconCopy /> Copy Token
                        </>
                      )}
                    </button>
                  </div>
                </div>

                <div className="profile-quota-box">
                  <div className="profile-quota-row">
                    <span className="profile-quota-label">Daily API Request Quota</span>
                    <span className="profile-quota-count">742 / 1,000 (74.2%)</span>
                  </div>
                  <div className="profile-quota-bar">
                    <div className="profile-quota-bar-fill" style={{ width: '74.2%' }} />
                  </div>
                  <span className="profile-quota-hint">Quota resets in 5 hours at 00:00 UTC</span>
                </div>
              </div>

              {/* cURL integration snippet */}
              <div className="profile-card">
                <div className="profile-card-header profile-card-header--row">
                  <div>
                    <h3>Direct cURL Example</h3>
                    <p>Integrate automated Natural Language queries into your command line or scripts.</p>
                  </div>
                  <button
                    type="button"
                    className={`profile-btn profile-btn--copy ${copiedCurl ? 'profile-btn--copied' : ''}`}
                    onClick={handleCopyCurl}
                  >
                    {copiedCurl ? (
                      <>
                        <IconCheck /> Copied
                      </>
                    ) : (
                      <>
                        <IconCopy /> Copy cURL
                      </>
                    )}
                  </button>
                </div>

                <pre className="profile-code-block">
                  <code>{curlSnippet}</code>
                </pre>
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════
            TAB 4: Role Permissions & Activity
            ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'activity' && (
          <div className="profile-tab-content" style={{ animation: 'fadeRow 0.3s ease-out both' }}>
            <div className="profile-cards-stack">
              {/* Permissions matrix */}
              <div className="profile-card">
                <div className="profile-card-header">
                  <h3>Role & Capability Matrix</h3>
                  <p>
                    Your account is assigned the <span className="profile-bold-role">{user?.role || 'viewer'}</span> privilege tier.
                  </p>
                </div>

                <div className="profile-perms-grid">
                  <div className="profile-perm-item">
                    <span className="profile-perm-check">✓</span>
                    <div className="profile-perm-info">
                      <div className="profile-perm-title">Read & SELECT Queries</div>
                      <div className="profile-perm-desc">Query collection records using natural English or Hinglish</div>
                    </div>
                    <span className="profile-perm-badge profile-perm-badge--allowed">Allowed</span>
                  </div>

                  <div className="profile-perm-item">
                    <span className="profile-perm-check">✓</span>
                    <div className="profile-perm-info">
                      <div className="profile-perm-title">Aggregation & Analytics</div>
                      <div className="profile-perm-desc">Group, sort, count, and run MongoDB aggregation pipelines</div>
                    </div>
                    <span className="profile-perm-badge profile-perm-badge--allowed">Allowed</span>
                  </div>

                  <div className="profile-perm-item">
                    <span className="profile-perm-check">
                      {user?.role === 'viewer' ? '✕' : '✓'}
                    </span>
                    <div className="profile-perm-info">
                      <div className="profile-perm-title">UPDATE Operations</div>
                      <div className="profile-perm-desc">Modify existing documents (requires preview confirmation)</div>
                    </div>
                    <span className={`profile-perm-badge ${user?.role === 'viewer' ? 'profile-perm-badge--denied' : 'profile-perm-badge--allowed'}`}>
                      {user?.role === 'viewer' ? 'Denied' : 'Allowed'}
                    </span>
                  </div>

                  <div className="profile-perm-item">
                    <span className="profile-perm-check">
                      {user?.role === 'admin' ? '✓' : '✕'}
                    </span>
                    <div className="profile-perm-info">
                      <div className="profile-perm-title">DELETE & DROP Operations</div>
                      <div className="profile-perm-desc">Permanent document removal and destructive operations</div>
                    </div>
                    <span className={`profile-perm-badge ${user?.role === 'admin' ? 'profile-perm-badge--allowed' : 'profile-perm-badge--denied'}`}>
                      {user?.role === 'admin' ? 'Allowed' : 'Admin Only'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Recent activity timeline */}
              <div className="profile-card">
                <div className="profile-card-header">
                  <h3>Recent Workspace Activity</h3>
                  <p>Audit trail of queries executed and settings configured.</p>
                </div>

                <div className="profile-timeline">
                  <div className="profile-timeline-item">
                    <div className="profile-timeline-dot profile-timeline-dot--green" />
                    <div className="profile-timeline-body">
                      <div className="profile-timeline-action">Executed query on Student Database</div>
                      <div className="profile-timeline-sub">"Show all students with GPA greater than 3.5 in CS branch"</div>
                      <div className="profile-timeline-meta">14 minutes ago · MongoDB Cluster 1</div>
                    </div>
                  </div>

                  <div className="profile-timeline-item">
                    <div className="profile-timeline-dot profile-timeline-dot--butter" />
                    <div className="profile-timeline-body">
                      <div className="profile-timeline-action">Saved Query Snippet #28</div>
                      <div className="profile-timeline-sub">"Top 5 performers per semester with aggregate GPA"</div>
                      <div className="profile-timeline-meta">3 hours ago · Saved Templates</div>
                    </div>
                  </div>

                  <div className="profile-timeline-item">
                    <div className="profile-timeline-dot profile-timeline-dot--blue" />
                    <div className="profile-timeline-body">
                      <div className="profile-timeline-action">Connected to Student Analytics Replica Set</div>
                      <div className="profile-timeline-sub">Verified schema latency: 18ms</div>
                      <div className="profile-timeline-meta">Yesterday at 16:45 · Network Auth</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
