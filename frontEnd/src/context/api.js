/**
 * QueryMind AI — Real REST API Client
 *
 * Connects to the FastAPI backend at http://localhost:8000/api
 * Replaces the former mock data layer while preserving the same
 * exported function signatures so every existing component keeps working.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// ---------------------------------------------------------------------------
// Token helpers
// ---------------------------------------------------------------------------

function getToken() {
  return localStorage.getItem('qm_token') || '';
}

function setToken(token) {
  if (token) localStorage.setItem('qm_token', token);
  else localStorage.removeItem('qm_token');
}

// ---------------------------------------------------------------------------
// Base fetch wrapper
// ---------------------------------------------------------------------------

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    setToken(null);
    window.location.href = '/login';
    throw new Error('Session expired. Please log in again.');
  }

  if (!res.ok) {
    let errMsg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      errMsg = body?.detail || body?.message || errMsg;
    } catch (_) {}
    throw new Error(errMsg);
  }

  // 204 No Content
  if (res.status === 204) return null;

  return res.json();
}

// ---------------------------------------------------------------------------
// Auth — called by AuthContext
// ---------------------------------------------------------------------------

export async function authRegister(name, email, password) {
  const data = await apiFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  });
  if (data?.access_token) setToken(data.access_token);
  return data; // { access_token, token_type, user }
}

export async function authLogin(email, password) {
  const data = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (data?.access_token) setToken(data.access_token);
  return data; // { access_token, token_type, user }
}

export async function authMe() {
  return apiFetch('/auth/me');
}

export async function updateProfile(profileData) {
  const body = typeof profileData === 'string' ? { name: profileData } : profileData;
  return apiFetch('/auth/me', {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}

export async function changePassword(currentPassword, newPassword) {
  return apiFetch('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}

export async function toggleTwoFactor() {
  return apiFetch('/auth/toggle-2fa', {
    method: 'POST',
  });
}

export async function regenerateApiToken() {
  return apiFetch('/auth/regenerate-token', {
    method: 'POST',
  });
}

export function authLogout() {
  setToken(null);
}

// ---------------------------------------------------------------------------
// Legacy login() used by some older components — wraps authLogin
// ---------------------------------------------------------------------------

export async function login(credentials) {
  try {
    const data = await authLogin(credentials?.email, credentials?.password);
    return { success: true, user: data.user };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/**
 * POST /queries
 * Generates SQL from natural language query.
 */
export async function generateQuery({ nl_query, database_id = null, session_id = null, language = 'English', input_type = 'text' }) {
  return apiFetch('/queries', {
    method: 'POST',
    body: JSON.stringify({ nl_query, database_id, session_id, language, input_type }),
  });
}

/**
 * Legacy submitQuery() wrapper — keeps ChatPage working.
 */
export async function submitQuery(queryText, userInfo = {}) {
  const result = await generateQuery({
    nl_query: queryText,
    database_id: userInfo.database_id || null,
    session_id: userInfo.session_id || null,
    input_type: userInfo.input_type || 'text',
    language: userInfo.language || 'English'
  });
  return result;
}

/**
 * POST /queries/:id/validate — re-validate after user edits SQL
 */
export async function revalidateQuery(queryId, editedSql) {
  return apiFetch(`/queries/${queryId}/validate`, {
    method: 'POST',
    body: JSON.stringify({ edited_sql: editedSql }),
  });
}

export const validateQuery = revalidateQuery;

/**
 * POST /queries/:id/approve — approve a specific statement
 */
export async function approveQuery(queryId, statementIndex = 0) {
  return apiFetch(`/queries/${queryId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ statement_index: statementIndex }),
  });
}

/**
 * POST /queries/:id/reject — reject the generated query
 */
export async function rejectQuery(queryId) {
  return apiFetch(`/queries/${queryId}/reject`, { method: 'POST' });
}

/**
 * POST /queries/:id/execute — execute approved statements
 */
export async function executeQuery(queryId, statementIndices = null) {
  return apiFetch(`/queries/${queryId}/execute`, {
    method: 'POST',
    body: JSON.stringify({ statement_indices: statementIndices }),
  });
}

/**
 * GET /queries/:id/export — download results as CSV
 */
export async function exportQueryCSV(queryId) {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}/queries/${queryId}/export`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`CSV export failed: HTTP ${res.status}`);
  return res.blob(); // caller creates object URL
}

// ---------------------------------------------------------------------------
// History & Dashboard
// ---------------------------------------------------------------------------

export async function getHistory() {
  const items = await apiFetch('/history');
  return items || [];
}

export async function getDashboardStats() {
  return apiFetch('/dashboard/stats');
}

// Stub — no saved-queries endpoint yet; return empty list gracefully
export async function getSavedQueries() {
  return [];
}

// addBlockedQuery is now a no-op; backend logs it automatically
export function addBlockedQuery() {}

// ---------------------------------------------------------------------------
// Database Connections
// ---------------------------------------------------------------------------

export async function getConnections() {
  const list = await apiFetch('/databases');
  return list || [];
}

/** Alias for ChatPage database selector */
export const getDatabaseConnections = getConnections;

/**
 * POST /databases — create & test connection
 * Accepts: { name, db_type, host, port, database_name, username, password }
 * OR:      { name, connection_string }
 */
export async function addConnection(data) {
  try {
    const conn = await apiFetch('/databases', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return { success: true, connection: conn };
  } catch (err) {
    return { success: false, message: err.message };
  }
}

/**
 * POST /databases/test — test connectivity before saving
 */
export async function testConnection(data) {
  try {
    const res = await apiFetch('/databases/test', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res; // { success, message }
  } catch (err) {
    return { success: false, message: err.message };
  }
}

/**
 * POST /databases/:id/test — test an existing saved connection
 */
export async function testExistingConnection(connId) {
  try {
    const res = await apiFetch(`/databases/${connId}/test`, { method: 'POST' });
    return res;
  } catch (err) {
    return { success: false, message: err.message };
  }
}

/**
 * DELETE /databases/:id — disconnect & remove connection
 */
export async function disconnectConnection(id) {
  try {
    await apiFetch(`/databases/${id}`, { method: 'DELETE' });
    return { success: true };
  } catch (err) {
    return { success: false, message: err.message };
  }
}

/**
 * GET /databases/:id/schema — discover tables & columns
 */
export async function getDatabaseSchema(connId) {
  return apiFetch(`/databases/${connId}/schema`);
}

/**
 * GET /databases/:id/permissions
 */
export async function getDatabasePermissions(connId) {
  return apiFetch(`/databases/${connId}/permissions`);
}

/**
 * POST /databases/:id/permissions
 */
export async function updateDatabasePermissions(connId, tables) {
  return apiFetch(`/databases/${connId}/permissions`, {
    method: 'POST',
    body: JSON.stringify({ tables }),
  });
}

// ---------------------------------------------------------------------------
// Sessions
// ---------------------------------------------------------------------------

export async function getSessions() {
  return apiFetch('/sessions');
}

export async function createSession(database_id, title = 'New Chat') {
  return apiFetch('/sessions', {
    method: 'POST',
    body: JSON.stringify({ database_id, title }),
  });
}

export async function closeSession(sessionId) {
  return apiFetch(`/sessions/${sessionId}/close`, { method: 'POST' });
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export async function getSettings() {
  try {
    return await apiFetch('/settings');
  } catch (_) {
    return { confirmUpdates: true, confirmDeletes: true, rowLimit: 1000, queryTimeout: 20 };
  }
}

export async function updateSettings(data) {
  return apiFetch('/settings', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------

export async function getAdminUsers() {
  return apiFetch('/admin/users');
}

export async function updateUserRole(userId, role) {
  return apiFetch(`/admin/users/${userId}/role`, {
    method: 'PUT',
    body: JSON.stringify({ role }),
  });
}

export async function resetUserPassword(userId) {
  return apiFetch(`/admin/users/${userId}/reset-password`, { method: 'POST' });
}

export async function deleteUser(userId) {
  return apiFetch(`/admin/users/${userId}`, { method: 'DELETE' });
}

export async function getSecurityLogs() {
  return apiFetch('/admin/security-logs');
}

// ---------------------------------------------------------------------------
// Role Request Workflow
// ---------------------------------------------------------------------------

/**
 * POST /admin/role-requests — any user submits a request for elevated role
 */
export async function submitRoleRequest(requestedRole, reason = '') {
  return apiFetch('/admin/role-requests', {
    method: 'POST',
    body: JSON.stringify({ requested_role: requestedRole, reason }),
  });
}

/**
 * GET /admin/role-requests/my — current user's own requests
 */
export async function getMyRoleRequests() {
  try {
    return await apiFetch('/admin/role-requests/my');
  } catch (_) {
    return [];
  }
}

/**
 * GET /admin/role-requests — admin: all role requests (filtered by status)
 */
export async function getAdminRoleRequests(statusFilter = 'pending') {
  return apiFetch(`/admin/role-requests?status_filter=${statusFilter}`);
}

/**
 * POST /admin/role-requests/:id/approve — admin approves a request
 */
export async function approveRoleRequest(requestId) {
  return apiFetch(`/admin/role-requests/${requestId}/approve`, { method: 'POST' });
}

/**
 * POST /admin/role-requests/:id/reject — admin rejects a request
 */
export async function rejectRoleRequest(requestId) {
  return apiFetch(`/admin/role-requests/${requestId}/reject`, { method: 'POST' });
}

// ---------------------------------------------------------------------------
// Legacy exports used by AdminPage mock helpers (now safe no-ops)
// ---------------------------------------------------------------------------

export function getMockUsers() { return []; }
export function setMockUsers() {}
