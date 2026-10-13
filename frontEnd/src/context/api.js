/**
 * QueryMind AI — Mock API & Data Layer Service
 *
 * Structured as a drop-in replacement for a real REST backend.
 * Each function returns a Promise with simulated network latency
 * and full documentation of expected HTTP method, endpoint, request, and response shape.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// Helper for realistic async network delay
const delay = (ms = 400) => new Promise((resolve) => setTimeout(resolve, ms));

// ==========================================
// MOCK DATA STORE (In-Memory Session State)
// ==========================================

const MOCK_STUDENTS = [
  { id: 'STU-2024-001', name: 'Priya Sharma',    program: 'B.Tech CSE',   semester: '5th', fee: '₹65,000', dueDate: '15 Jul 2026', status: 'Overdue' },
  { id: 'STU-2024-002', name: 'Arjun Patel',     program: 'B.Tech EE',    semester: '3rd', fee: '₹58,000', dueDate: '20 Jul 2026', status: 'Pending' },
  { id: 'STU-2024-003', name: 'Meera Nair',      program: 'MCA',          semester: '1st', fee: '₹48,000', dueDate: '12 Jul 2026', status: 'Overdue' },
  { id: 'STU-2024-004', name: 'Rohan Verma',     program: 'B.Tech Mech',  semester: '7th', fee: '₹72,000', dueDate: '25 Jul 2026', status: 'Pending' },
  { id: 'STU-2024-005', name: 'Kavya Reddy',     program: 'MBA',          semester: '3rd', fee: '₹78,000', dueDate: '18 Jul 2026', status: 'Overdue' },
  { id: 'STU-2024-006', name: 'Sanjay Gupta',    program: 'B.Sc IT',      semester: '5th', fee: '₹42,000', dueDate: '22 Jul 2026', status: 'Pending' },
  { id: 'STU-2024-007', name: 'Ananya Singh',    program: 'B.Tech Civil', semester: '3rd', fee: '₹54,000', dueDate: '10 Jul 2026', status: 'Overdue' },
  { id: 'STU-2024-008', name: 'Vikram Joshi',    program: 'B.Com',        semester: '1st', fee: '₹32,000', dueDate: '30 Jul 2026', status: 'Pending' },
  { id: 'STU-2024-009', name: 'Pooja Iyer',      program: 'B.Tech CSE',   semester: '7th', fee: '₹68,000', dueDate: '14 Jul 2026', status: 'Overdue' },
  { id: 'STU-2024-010', name: 'Rahul Mehta',     program: 'MCA',          semester: '3rd', fee: '₹52,000', dueDate: '28 Jul 2026', status: 'Pending' },
  { id: 'STU-2024-011', name: 'Ishita Kapoor',   program: 'MBA',          semester: '1st', fee: '₹76,000', dueDate: '19 Jul 2026', status: 'Overdue' },
  { id: 'STU-2024-012', name: 'Devraj Pandey',   program: 'B.Tech EE',    semester: '5th', fee: '₹60,000', dueDate: '24 Jul 2026', status: 'Pending' },
  { id: 'STU-2024-013', name: 'Shruti Menon',    program: 'B.Sc IT',      semester: '3rd', fee: '₹44,000', dueDate: '16 Jul 2026', status: 'Overdue' },
  { id: 'STU-2024-014', name: 'Karan Malhotra',  program: 'B.Tech Mech',  semester: '5th', fee: '₹66,000', dueDate: '02 Aug 2026', status: 'Pending' },
  { id: 'STU-2024-015', name: 'Nidhi Agrawal',   program: 'B.Com',        semester: '5th', fee: '₹36,000', dueDate: '05 Aug 2026', status: 'Overdue' },
  { id: 'STU-2024-016', name: 'Tarun Bhatia',    program: 'B.Tech Civil', semester: '7th', fee: '₹58,000', dueDate: '08 Aug 2026', status: 'Pending' },
  { id: 'STU-2024-017', name: 'Palak Saxena',    program: 'MCA',          semester: '5th', fee: '₹50,000', dueDate: '11 Aug 2026', status: 'Overdue' },
  { id: 'STU-2024-018', name: 'Ayush Chauhan',   program: 'B.Tech CSE',   semester: '3rd', fee: '₹64,000', dueDate: '15 Aug 2026', status: 'Pending' },
];

// queryStatus: 'success' | 'blocked'
// type: 'select' | 'update' | 'delete'
let queryHistory = [
  { id: 'hist-1', query: 'Which students have unpaid fees this semester?', type: 'select', status: 'success', time: '2 min ago',   count: '18 rows',    collection: 'students',   user: 'Heer Sachdev',   executionTime: '34ms' },
  { id: 'hist-2', query: 'Show all inactive student accounts.',            type: 'select', status: 'success', time: '14 min ago',  count: '126 rows',   collection: 'students',   user: 'Heer Sachdev',   executionTime: '41ms' },
  { id: 'hist-3', query: 'Find students enrolled in Computer Science.',    type: 'select', status: 'success', time: '1 hour ago',  count: '84 rows',    collection: 'students',   user: 'Neel Shah',      executionTime: '28ms' },
  { id: 'hist-4', query: "Change Rahul Mehta's department to CS.",         type: 'update', status: 'success', time: '2 hours ago', count: '1 updated',  collection: 'students',   user: 'Heer Sachdev',   executionTime: '57ms' },
  { id: 'hist-5', query: 'Show top 10 students by CGPA.',                  type: 'select', status: 'success', time: 'Yesterday',   count: '10 rows',    collection: 'students',   user: 'Deep Soni',      executionTime: '22ms' },
  { id: 'hist-6', query: 'List all students with attendance below 75%.',   type: 'select', status: 'success', time: 'Yesterday',   count: '37 rows',    collection: 'attendance', user: 'Deep Soni',      executionTime: '36ms' },
  { id: 'hist-7', query: 'Delete all inactive student records.',           type: 'delete', status: 'blocked', time: '2 days ago',  count: 'Blocked',    collection: 'students',   user: 'Neel Shah',      executionTime: '—' },
  { id: 'hist-8', query: 'Update fee status for Ishita Kapoor to paid.',   type: 'update', status: 'success', time: '2 days ago',  count: '1 updated',  collection: 'students',   user: 'Heer Sachdev',   executionTime: '49ms' },
  { id: 'hist-9', query: 'Show all students in the MBA programme.',        type: 'select', status: 'success', time: '3 days ago',  count: '96 rows',    collection: 'students',   user: 'Heer Sachdev',   executionTime: '31ms' },
];

const savedQueries = [
  { id: 'saved-1', title: 'Unpaid Fees Report',  query: 'Which students have unpaid fees this semester?',  collection: 'students',   date: '12 Aug 2026' },
  { id: 'saved-2', title: 'Inactive Students',   query: 'Show all inactive student accounts.',             collection: 'students',   date: '10 Aug 2026' },
  { id: 'saved-3', title: 'CS Enrolment',        query: 'Show all students enrolled in Computer Science.', collection: 'students',   date: '8 Aug 2026'  },
  { id: 'saved-4', title: 'Low Attendance Alert',query: 'List all students with attendance below 75%.',    collection: 'attendance', date: '5 Aug 2026'  },
  { id: 'saved-5', title: 'Top CGPA Students',   query: 'Show top 10 students by CGPA.',                  collection: 'students',   date: '3 Aug 2026'  },
  { id: 'saved-6', title: 'MBA Semester Fees',   query: 'Show all students in the MBA programme.',        collection: 'students',   date: '1 Aug 2026'  },
];

let activeConnections = [
  {
    id: 'conn-1',
    name: 'Student Database',
    type: 'MongoDB',
    status: 'Connected',
    collectionsCount: 7,
    queriesCount: 1134,
    lastSynced: '3 min ago',
    host: 'cluster0.mongodb.net',
    database: 'college_db',
  }
];

let sessionSettings = {
  confirmUpdates: true,
  confirmDeletes: true,
  rowLimit: 100,
  queryTimeout: 30,
};

// ==========================================
// API OPERATIONS
// ==========================================

/**
 * POST /auth/login
 * NOTE: Real auth uses AuthContext.login() — this is the legacy REST-shape mock.
 */
export async function login(credentials) {
  await delay(350);
  const email = credentials?.email || 'heer@querymind.ai';
  return { success: true, user: { name: 'Heer Sachdev', email, role: 'analyst', avatar: 'HS' } };
}

/**
 * POST /queries/execute
 */
export async function submitQuery(queryText, userInfo = {}) {
  await delay(250);
  const text  = (queryText || '').trim();
  const lower = text.toLowerCase();

  let queryType = 'select';
  if (/^(delete|remove|erase|purge)\b/i.test(text))  queryType = 'delete';
  else if (/^(change|update|set|modify)\b/i.test(text) || lower.includes("'s department") || lower.includes("'s name")) queryType = 'update';

  // Record into history
  const newHistItem = {
    id: `hist-${Date.now()}`,
    query: text,
    type: queryType,
    status: 'success',
    time: 'Just now',
    count: queryType === 'select' ? '18 rows' : queryType === 'update' ? '1 updated' : '126 deleted',
    collection: 'students',
    user: userInfo.name || 'User',
    executionTime: `${Math.floor(Math.random() * 60) + 15}ms`,
  };
  queryHistory = [newHistItem, ...queryHistory.slice(0, 15)];

  if (queryType === 'update') {
    return { query: text, queryType: 'update', record: { id: 'STU-2024-023', name: 'Rahul Mehta', field: 'Department', before: 'Information Technology', after: 'Computer Science', affectedCount: 1 } };
  }
  if (queryType === 'delete') {
    return { query: text, queryType: 'delete', warning: { affectedCount: 126, collection: 'students', condition: 'status = inactive' } };
  }
  return { query: text, queryType: 'select', count: MOCK_STUDENTS.length, data: MOCK_STUDENTS, executionTime: '34ms' };
}

/**
 * Add a blocked query entry to history (called by ChatPage when viewer attempts UPDATE/DELETE)
 */
export function addBlockedQuery(text, queryType, userName = 'Viewer') {
  const newHistItem = {
    id: `hist-${Date.now()}`,
    query: text,
    type: queryType,
    status: 'blocked',
    time: 'Just now',
    count: 'Blocked',
    collection: 'students',
    user: userName,
    executionTime: '—',
  };
  queryHistory = [newHistItem, ...queryHistory.slice(0, 15)];
}

/**
 * GET /queries/history
 */
export async function getHistory() {
  await delay(200);
  return [...queryHistory];
}

/**
 * GET /queries/saved
 */
export async function getSavedQueries() {
  await delay(200);
  return [...savedQueries];
}

/**
 * GET /dashboard/stats — derives stats from live queryHistory
 */
export async function getDashboardStats() {
  await delay(180);
  const total   = queryHistory.length;
  const success = queryHistory.filter((h) => h.status === 'success').length;
  const blocked = queryHistory.filter((h) => h.status === 'blocked').length;
  const rate    = total > 0 ? Math.round((success / total) * 100) : 0;
  const times   = queryHistory.filter((h) => h.executionTime && h.executionTime !== '—').map((h) => parseInt(h.executionTime));
  const avgTime = times.length > 0 ? Math.round(times.reduce((a, b) => a + b, 0) / times.length) : 34;
  return { total, successRate: rate, blocked, avgResponseTime: `${avgTime}ms`, recent: queryHistory.slice(0, 5) };
}

/**
 * GET /connections
 */
export async function getConnections() {
  await delay(250);
  return [...activeConnections];
}

/**
 * POST /connections
 */
export async function addConnection(data) {
  await delay(400);
  const newConn = {
    id: `conn-${Date.now()}`,
    name: data.name || 'New Connection',
    type: 'MongoDB',
    status: 'Connected',
    collectionsCount: 4,
    queriesCount: 0,
    lastSynced: 'Just now',
    host: data.connectionString ? data.connectionString.split('@')[1] || 'mongodb.net' : 'cluster1.mongodb.net',
    database: data.database || 'main_db',
  };
  activeConnections.push(newConn);
  return { success: true, connection: newConn };
}

/**
 * POST /connections/test
 */
export async function testConnection(data) {
  await delay(900);
  if (!data?.connectionString || data.connectionString.toLowerCase().includes('error')) {
    return { success: false, message: 'Could not connect — check your connection string.' };
  }
  return { success: true, message: 'Connection successful — database reachable' };
}

/**
 * DELETE /connections/:id
 */
export async function disconnectConnection(id) {
  await delay(300);
  activeConnections = activeConnections.filter((c) => c.id !== id);
  return { success: true };
}

/**
 * GET /settings
 */
export async function getSettings() {
  await delay(150);
  return { ...sessionSettings };
}

/**
 * PUT /settings
 */
export async function updateSettings(data) {
  await delay(200);
  sessionSettings = { ...sessionSettings, ...data };
  return { success: true, settings: { ...sessionSettings } };
}
