import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart3, Database, Activity, BookOpen, Users, FileText, Download, Play, Edit, Search, Filter, ExternalLink, Loader, Home } from 'lucide-react';
import apiService from '../services/apiService';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [activePage, setActivePage] = useState('dashboard');
  const [sqlQuery, setSqlQuery] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [monitoringTab, setMonitoringTab] = useState('audit');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [users, setUsers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [cases, setCases] = useState([]);
  const [adminUser, setAdminUser] = useState(null);
  const [usernameInput, setUsernameInput] = useState('');
  const [showUsernameModal, setShowUsernameModal] = useState(false);
  const [pendingQuery, setPendingQuery] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showInsertModal, setShowInsertModal] = useState(false);
  const [deleteTableName, setDeleteTableName] = useState('');
  const [deleteCondition, setDeleteCondition] = useState('');
  const [insertTableName, setInsertTableName] = useState('');
  const [insertColumns, setInsertColumns] = useState('');
  const [insertValues, setInsertValues] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [queryName, setQueryName] = useState('');

  // Helpers: consistent TH timezone + clean cell rendering
  const DATE_TIME_REGEX = /^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$/;
  const toIsoCandidate = (v) => (typeof v === 'string' ? v.replace(' ', 'T') : v);
  const formatDateTH = (value) => {
    if (!value) return 'N/A';
    try {
      const str = String(value);
      if (!DATE_TIME_REGEX.test(str) && isNaN(Date.parse(str))) return str;
      const d = new Date(toIsoCandidate(str));
      if (isNaN(d)) return str;
      return new Intl.DateTimeFormat('th-TH', {
        timeZone: 'Asia/Bangkok',
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: false
      }).format(d);
    } catch {
      return String(value);
    }
  };

  const formatQueryCell = (cell) => {
    if (cell === null || cell === undefined) return '';
    if (typeof cell === 'number') {
      return cell.toLocaleString(undefined, { maximumFractionDigits: 3 });
    }
    const str = String(cell);
    if (DATE_TIME_REGEX.test(str) || str.includes('T')) {
      const formatted = formatDateTH(str);
      return formatted;
    }
    return str;
  };

  // Authentication check - must be logged in AND must be admin
  useEffect(() => {
    const storedUser = localStorage.getItem('adminUser');
    if (!storedUser) {
      // Not logged in at all - redirect to home
      navigate('/');
      return;
    }

    try {
      const user = JSON.parse(storedUser);
      if (!user.isAdmin) {
        // Logged in but not admin - redirect to home
        alert('Access Denied: Admin privileges required');
        navigate('/');
        return;
      }
      setAdminUser(user);
    } catch (e) {
      console.error('Failed to parse user data:', e);
      navigate('/');
    }
  }, [navigate]);

  useEffect(() => {
    if (adminUser && activePage === 'dashboard') {
      loadDashboardData();
    } else if (adminUser && activePage === 'monitoring') {
      loadMonitoringData();
    }
  }, [adminUser, activePage, monitoringTab]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsData, auditData] = await Promise.all([
        apiService.getAdminStats(),
        apiService.getAuditLogs(8)
      ]);
      setStats(statsData.data);
      setAuditLogs(auditData.data || []);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActionBadgeColor = (actionType) => {
    const action = actionType.toLowerCase();
    if (action.includes('login')) return 'blue';
    if (action.includes('logout')) return 'gray';
    if (action.includes('session_start') || action.includes('start')) return 'orange';
    if (action.includes('session_end') || action.includes('end')) return 'orange';
    if (action.includes('delete') || action.includes('remove')) return 'red';
    if (action.includes('update') || action.includes('edit')) return 'purple';
    if (action.includes('download')) return 'teal';
    if (action.includes('upload')) return 'indigo';
    if (action.includes('admin')) return 'pink';
    return 'blue'; // default
  };

  // Extract mode from details string (format: "mode=exam | ..." or "mode=practice | ...")
  const extractModeFromDetails = (details) => {
    if (!details) return null;
    const match = details.match(/mode=(exam|practice)/i);
    return match ? match[1].toLowerCase() : null;
  };

  // Get stripe color based on mode
  const getModeStripeColor = (mode) => {
    if (mode === 'exam') return '#f87171'; // light red
    if (mode === 'practice') return '#86efac'; // light green
    return 'transparent';
  };

  const loadMonitoringData = async () => {
    try {
      setLoading(true);
      if (monitoringTab === 'audit') {
        const response = await apiService.getAuditLogs(50);
        setAuditLogs(response.data || []);
      } else if (monitoringTab === 'sessions') {
        const response = await apiService.getAdminSessions(50);
        setSessions(response.data || []);
      } else if (monitoringTab === 'users') {
        const response = await apiService.getAdminUsers(50);
        setUsers(response.data || []);
      } else if (monitoringTab === 'messages') {
        const response = await apiService.getAdminMessages(50);
        setMessages(response.data || []);
      } else if (monitoringTab === 'cases') {
        const response = await apiService.getAdminCases(100);
        setCases(response.data || []);
      }
    } catch (error) {
      console.error('Failed to load monitoring data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunQuery = async (password = null) => {
    if (!sqlQuery.trim()) {
      setQueryResult({
        success: false,
        message: 'Please enter a query',
        rows: 0,
        columns: [],
        data: []
      });
      return;
    }

    try {
      setLoading(true);
      
      // Get admin ID from session storage or local storage
      const adminData = JSON.parse(sessionStorage.getItem('adminUser') || localStorage.getItem('adminUser') || '{}');
      const adminId = adminData.adminId;
      
      if (!adminId) {
        setQueryResult({
          success: false,
          message: 'Admin authentication required. Please log in again.',
          rows: 0,
          columns: [],
          data: []
        });
        return;
      }

      const result = await apiService.executeQuery(sqlQuery, adminId, password, queryName || null);
      setQueryResult(result);
      // Clear query name after execution
      setQueryName('');
    } catch (error) {
      console.error('Query execution failed:', error);
      setQueryResult({
        success: false,
        message: error.message || 'Query execution failed',
        rows: 0,
        columns: [],
        data: []
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = (sessionId) => {
    apiService.downloadReport(sessionId)
      .then(() => {
        alert('Download started');
      })
      .catch(error => {
        alert('Download failed: ' + error.message);
      });
  };

  const renderNavigation = () => (
    <div className="admin-nav">
      <div className="admin-nav-header">
        <h1 className="admin-nav-title">Admin Panel</h1>
        <p className="admin-nav-subtitle">Database Management</p>
      </div>
      
      <nav className="admin-nav-menu">
        <button
          onClick={() => navigate('/')}
          className="admin-nav-item home-btn"
        >
          <Home size={16} />
          <span>Back to Home</span>
        </button>
        
        <div className="admin-nav-divider"></div>
        <button
          onClick={() => setActivePage('dashboard')}
          className={`admin-nav-item ${activePage === 'dashboard' ? 'active' : ''}`}
        >
          <BarChart3 size={16} />
          <span>Dashboard</span>
        </button>
        
        <button
          onClick={() => setActivePage('query')}
          className={`admin-nav-item ${activePage === 'query' ? 'active' : ''}`}
        >
          <Database size={16} />
          <span>Query Editor</span>
        </button>
        
        <button
          onClick={() => setActivePage('monitoring')}
          className={`admin-nav-item ${activePage === 'monitoring' ? 'active' : ''}`}
        >
          <Activity size={16} />
          <span>Data Monitoring</span>
        </button>
        
        <button
          onClick={() => setActivePage('api')}
          className={`admin-nav-item ${activePage === 'api' ? 'active' : ''}`}
        >
          <BookOpen size={16} />
          <span>API Docs</span>
        </button>
      </nav>
      
      <div className="admin-nav-footer">
        <p className="admin-nav-footer-label">Logged in as</p>
        <p className="admin-nav-footer-user">{adminUser?.name || 'Admin'}</p>
      </div>
    </div>
  );

  const renderDashboard = () => (
    <div className="admin-page-content">
      <h2 className="admin-page-title">Dashboard Overview</h2>
      
      {loading ? (
        <div className="admin-loading">
          <Loader className="spinning" size={32} />
          <p>Loading dashboard...</p>
        </div>
      ) : stats ? (
        <>
          {/* Category Cards Grid */}
          <div className="dashboard-categories-grid">
            {/* User & Sessions Card */}
            <div className="category-card">
              <h3 className="category-card-title">User & Sessions</h3>
              <div className="category-stats-list">
                <div className="category-stat-item">
                  <span className="category-stat-label">Total Users</span>
                  <span className="category-stat-value">{stats.total_users}</span>
                </div>
                <div className="category-stat-item">
                  <span className="category-stat-label">Active Sessions</span>
                  <span className="category-stat-value">{stats.active_sessions}</span>
                </div>
                <div className="category-stat-item">
                  <span className="category-stat-label">Completed</span>
                  <span className="category-stat-value">{stats.completed_sessions}</span>
                </div>
                <div className="category-stat-item">
                  <span className="category-stat-label">Downloads</span>
                  <span className="category-stat-value">{stats.downloads}</span>
                </div>
              </div>
            </div>

            {/* Session Types Card */}
            <div className="category-card">
              <h3 className="category-card-title">Session Types</h3>
              <div className="category-stats-list">
                <div className="category-stat-item">
                  <span className="category-stat-label">Exam Mode</span>
                  <span className="category-stat-value">{stats.exam_mode_sessions}</span>
                </div>
                <div className="category-stat-item">
                  <span className="category-stat-label">Practice Mode</span>
                  <span className="category-stat-value">{stats.practice_mode_sessions}</span>
                </div>
              </div>
            </div>

            {/* Duration Metrics Card */}
            <div className="category-card">
              <h3 className="category-card-title">Duration Metrics</h3>
              <div className="category-stats-list">
                <div className="category-stat-item">
                  <span className="category-stat-label">Average</span>
                  <span className="category-stat-value">{stats.avg_duration_minutes}m</span>
                </div>
                <div className="category-stat-item">
                  <span className="category-stat-label">Maximum</span>
                  <span className="category-stat-value">{stats.max_duration_minutes}m</span>
                </div>
                <div className="category-stat-item">
                  <span className="category-stat-label">Minimum</span>
                  <span className="category-stat-value">{stats.min_duration_minutes}m</span>
                </div>
              </div>
            </div>

            {/* Token Usage Card */}
            <div className="category-card">
              <h3 className="category-card-title">Token Usage</h3>
              <div className="category-stats-list">
                <div className="category-stat-item">
                  <span className="category-stat-label">Messages</span>
                  <span className="category-stat-value">{stats.total_messages}</span>
                </div>
                <div className="category-stat-item">
                  <span className="category-stat-label">Input Tokens</span>
                  <span className="category-stat-value">{stats.total_input_tokens?.toLocaleString() || 0}</span>
                </div>
                <div className="category-stat-item">
                  <span className="category-stat-label">Output Tokens</span>
                  <span className="category-stat-value">{stats.total_output_tokens?.toLocaleString() || 0}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="admin-dashboard-grid">
            <div className="admin-card">
              <h3 className="admin-card-title">Recent Activity</h3>
              <div className="admin-activity-list">
                {auditLogs.map(log => (
                  <div key={log.audit_id} className="admin-activity-item">
                    <div className="admin-activity-icon">
                      <Activity size={12} />
                    </div>
                    <div className="admin-activity-content">
                      <p className="admin-activity-desc">{log.action_type}</p>
<p className="admin-activity-meta">{log.user_name || 'System'} • {formatDateTH(log.created_at)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="admin-card">
              <h3 className="admin-card-title">Session Statistics</h3>
              <div className="admin-session-stats">
                <div className="admin-session-stat green">
                  <span className="admin-session-stat-label">Completed Sessions</span>
                  <span className="admin-session-stat-value">
                    {stats.total_sessions > 0 
                      ? Math.round((stats.completed_sessions / stats.total_sessions) * 100)
                      : 0}%
                  </span>
                </div>
                <div className="admin-session-stat blue">
                  <span className="admin-session-stat-label">Active Now</span>
                  <span className="admin-session-stat-value">{stats.active_sessions}</span>
                </div>
                <div className="admin-session-stat purple">
                  <span className="admin-session-stat-label">Avg Messages/Session</span>
                  <span className="admin-session-stat-value">{stats.avg_messages_per_session}</span>
                </div>
                <div className="admin-session-stat orange">
                  <span className="admin-session-stat-label">Total Sessions</span>
                  <span className="admin-session-stat-value">{stats.total_sessions}</span>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : (
        <p>No data available</p>
      )}
    </div>
  );

  const presetQueries = [
    {
      name: 'Active Sessions',
      query: "SELECT session_id, user_id, case_id, status, started_at, duration_seconds FROM sessions WHERE status = 'active' ORDER BY started_at DESC LIMIT 20;"
    },
    {
      name: 'User Data',
      query: "SELECT 'User Info' as category, u.name, u.student_id, u.email, u.created_at, u.last_login, NULL as action_type, NULL as ip_address, NULL as action_time, NULL as session_count FROM users u WHERE u.name ILIKE '%USERNAME%' UNION ALL SELECT 'Login History' as category, u.name, u.student_id, NULL as email, NULL as created_at, NULL as last_login, a.action_type, a.ip_address, a.performed_at as action_time, NULL as session_count FROM users u LEFT JOIN audit_log a ON u.user_id = a.user_id WHERE u.name ILIKE '%USERNAME%' AND a.action_type IN ('user_login', 'admin_login', 'user_logout', 'admin_logout') UNION ALL SELECT 'Session Stats' as category, u.name, u.student_id, NULL as email, NULL as created_at, NULL as last_login, NULL as action_type, NULL as ip_address, NULL as action_time, COUNT(s.session_id)::TEXT as session_count FROM users u LEFT JOIN sessions s ON u.user_id = s.user_id WHERE u.name ILIKE '%USERNAME%' GROUP BY u.user_id, u.name, u.student_id ORDER BY category, action_time DESC NULLS LAST;"
    },
    {
      name: 'Session Summary',
      query: "SELECT s.session_id, u.name as user_name, s.status, COUNT(m.message_id) as message_count, s.started_at, s.duration_seconds FROM sessions s LEFT JOIN users u ON s.user_id = u.user_id LEFT JOIN chat_messages m ON s.session_id = m.session_id GROUP BY s.session_id, u.name, s.status, s.started_at, s.duration_seconds ORDER BY s.started_at DESC LIMIT 20;"
    },
    {
      name: 'Token Usage',
      query: "SELECT u.name, COUNT(m.message_id) as total_messages, SUM(CASE WHEN m.role = 'user' THEN m.tokens_used ELSE 0 END) as input_tokens, SUM(CASE WHEN m.role IN ('chatbot', 'assistant') THEN m.tokens_used ELSE 0 END) as output_tokens FROM users u LEFT JOIN sessions s ON u.user_id = s.user_id LEFT JOIN chat_messages m ON s.session_id = m.session_id GROUP BY u.user_id, u.name ORDER BY total_messages DESC LIMIT 20;"
    },
    {
      name: 'Completed Sessions',
      query: "SELECT s.session_id, u.name as user_name, s.duration_seconds, s.started_at, s.ended_at FROM sessions s LEFT JOIN users u ON s.user_id = u.user_id WHERE s.status = 'complete' ORDER BY s.ended_at DESC LIMIT 20;"
    },
    {
      name: 'Recent Audit Logs',
      query: "SELECT a.log_id, u.name as user_name, a.action_type, a.performed_at FROM audit_log a LEFT JOIN users u ON a.user_id = u.user_id ORDER BY a.performed_at DESC LIMIT 30;"
    },
    {
      name: 'Cases Overview',
      query: "SELECT case_id, case_name, case_type, import_at FROM cases ORDER BY import_at DESC;"
    },
    {
      name: 'Top Active Users',
      query: "SELECT u.name, u.student_id, COUNT(DISTINCT s.session_id) as session_count, ROUND(AVG(s.duration_seconds), 0) as avg_duration_seconds FROM users u LEFT JOIN sessions s ON u.user_id = s.user_id WHERE s.session_id IS NOT NULL GROUP BY u.user_id, u.name, u.student_id ORDER BY session_count DESC LIMIT 15;"
    }
  ];

  const handlePresetQuery = (query, presetName) => {
    // Track query name for audit logging
    setQueryName(presetName);
    // If it's User Data query, show modal for username input
    if (presetName === 'User Data') {
      setPendingQuery(query);
      setShowUsernameModal(true);
    } else {
      setSqlQuery(query);
    }
  };

  const handleUsernameSubmit = () => {
    if (usernameInput.trim() && pendingQuery) {
      const updatedQuery = pendingQuery.replaceAll('USERNAME', usernameInput.trim());
      setSqlQuery(updatedQuery);
      setShowUsernameModal(false);
      setUsernameInput('');
      setPendingQuery(null);
    }
  };

  const handleDeleteData = () => {
    setQueryName('Delete Data');
    setShowDeleteModal(true);
  };

  const handleDeleteSubmit = async () => {
    if (!deleteTableName.trim()) {
      alert('Please enter a table name');
      return;
    }
    if (!deleteCondition.trim()) {
      alert('WHERE condition is required. This ensures only specific rows are deleted, not the entire table.');
      return;
    }
    if (!adminPassword.trim()) {
      alert('Please enter admin password');
      return;
    }

    // Build query with required WHERE clause (only deletes rows, never entire table)
    const query = `DELETE FROM ${deleteTableName.trim()} WHERE ${deleteCondition.trim()};`;

    setSqlQuery(query);
    setShowDeleteModal(false);
    
    // Execute query with password
    try {
      setLoading(true);
      const adminData = JSON.parse(sessionStorage.getItem('adminUser') || localStorage.getItem('adminUser') || '{}');
      const adminId = adminData.adminId;
      
      if (!adminId) {
        setQueryResult({
          success: false,
          message: 'Admin authentication required. Please log in again.',
          rows: 0,
          columns: [],
          data: []
        });
        return;
      }

      const result = await apiService.executeQuery(query, adminId, adminPassword.trim());
      setQueryResult(result);
      
      // Clear form fields on success
      setDeleteTableName('');
      setDeleteCondition('');
      setAdminPassword('');
    } catch (error) {
      console.error('Query execution failed:', error);
      setQueryResult({
        success: false,
        message: error.message || 'Query execution failed',
        rows: 0,
        columns: [],
        data: []
      });
    } finally {
      setLoading(false);
    }
  };

  const handleInsertData = () => {
    setQueryName('Insert Data');
    setShowInsertModal(true);
  };

  const handleInsertSubmit = async () => {
    if (!insertTableName.trim()) {
      alert('Please enter a table name');
      return;
    }
    if (!insertColumns.trim()) {
      alert('Please enter column names');
      return;
    }
    if (!insertValues.trim()) {
      alert('Please enter values');
      return;
    }
    if (!adminPassword.trim()) {
      alert('Please enter admin password');
      return;
    }

    const query = `INSERT INTO ${insertTableName.trim()} (${insertColumns.trim()}) VALUES (${insertValues.trim()});`;

    setSqlQuery(query);
    setShowInsertModal(false);
    
    // Execute query with password
    try {
      setLoading(true);
      const adminData = JSON.parse(sessionStorage.getItem('adminUser') || localStorage.getItem('adminUser') || '{}');
      const adminId = adminData.adminId;
      
      if (!adminId) {
        setQueryResult({
          success: false,
          message: 'Admin authentication required. Please log in again.',
          rows: 0,
          columns: [],
          data: []
        });
        return;
      }

      const result = await apiService.executeQuery(query, adminId, adminPassword.trim());
      setQueryResult(result);
      
      // Clear form fields on success
      setInsertTableName('');
      setInsertColumns('');
      setInsertValues('');
      setAdminPassword('');
    } catch (error) {
      console.error('Query execution failed:', error);
      setQueryResult({
        success: false,
        message: error.message || 'Query execution failed',
        rows: 0,
        columns: [],
        data: []
      });
    } finally {
      setLoading(false);
    }
  };

  const renderQueryEditor = () => (
    <div className="admin-page-content">
      <h2 className="admin-page-title">Query Editor</h2>
      
      <div className="admin-query-container">
        <div className="admin-query-panel">
          <div className="admin-query-header">
            <h3 className="admin-query-title">SQL Query</h3>
            <div className="admin-query-actions">
              <button onClick={() => handleRunQuery()} className="admin-btn primary">
                <Play size={12} />
                Run
              </button>
              <button onClick={() => setSqlQuery('')} className="admin-btn secondary">
                Clear
              </button>
            </div>
          </div>

          {/* Preset Queries */}
          <div className="preset-queries">
            <label className="preset-queries-label">Quick Queries:</label>
            <div className="preset-queries-grid">
              {presetQueries.map((preset, idx) => (
                <button
                  key={idx}
                  onClick={() => handlePresetQuery(preset.query, preset.name)}
                  className="preset-query-btn"
                  title={preset.query}
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>
          
          {/* Dangerous Operations */}
          <div className="preset-queries" style={{ marginTop: '10px', borderTop: '1px solid #e0e0e0', paddingTop: '10px' }}>
            <label className="preset-queries-label" style={{ color: '#64748b' }}>Dangerous Operations (Password Required):</label>
            <div className="preset-queries-grid">
              <button
                onClick={handleDeleteData}
                className="preset-query-btn"
                style={{ backgroundColor: '#64748b', color: 'white', border: '1px solid #475569' }}
              >
                Delete Data
              </button>
              <button
                onClick={handleInsertData}
                className="preset-query-btn"
                style={{ backgroundColor: '#64748b', color: 'white', border: '1px solid #475569' }}
              >
                Insert Data
              </button>
            </div>
          </div>
          
          <textarea
            value={sqlQuery}
            onChange={(e) => setSqlQuery(e.target.value)}
            placeholder="Enter your SQL query here or select a preset query above..."
            className="admin-query-textarea"
          />
        </div>

        {queryResult && (
          <div className="admin-query-result">
            <div className={`admin-query-message ${queryResult.success ? 'success' : 'error'}`}>
              <p>
                {queryResult.message}
                {queryResult.success && ` • ${queryResult.rows} rows`}
              </p>
            </div>

            {queryResult.success && queryResult.data && queryResult.data.length > 0 && (
              <div className="admin-table-wrapper">
                <table className="admin-table">
                  <thead>
                    <tr>
                      {queryResult.columns.map((col, idx) => (
                        <th key={idx}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {queryResult.data.map((row, idx) => (
                      <tr key={idx}>
{row.map((cell, cellIdx) => (
                          <td key={cellIdx}>{formatQueryCell(cell)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Username Input Modal */}
      {showUsernameModal && (
        <div className="modal-overlay" onClick={() => setShowUsernameModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">Enter Username</h3>
            <p className="modal-subtitle">Search for user data by name</p>
            <input
              type="text"
              placeholder="Enter username (e.g., John or Admin)..."
              value={usernameInput}
              onChange={(e) => setUsernameInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleUsernameSubmit()}
              className="modal-input"
              autoFocus
            />
            <div className="modal-actions">
              <button onClick={() => setShowUsernameModal(false)} className="admin-btn secondary">
                Cancel
              </button>
              <button onClick={handleUsernameSubmit} className="admin-btn primary" disabled={!usernameInput.trim()}>
                Load Query
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Data Modal */}
      {showDeleteModal && (
        <div className="modal-overlay" onClick={() => setShowDeleteModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title" style={{ color: '#1e293b' }}>Delete Data</h3>
            <p className="modal-subtitle">Warning: This will permanently delete rows from the table</p>
            
            <div style={{ marginBottom: '12px' }}>
              <label className="modal-label">Table Name *</label>
              <input
                type="text"
                placeholder=""
                value={deleteTableName}
                onChange={(e) => setDeleteTableName(e.target.value)}
                className="modal-input"
                autoFocus
              />
            </div>
            
            <div style={{ marginBottom: '12px' }}>
              <label className="modal-label">WHERE Condition (required)</label>
              <input
                type="text"
                placeholder=""
                value={deleteCondition}
                onChange={(e) => setDeleteCondition(e.target.value)}
                className="modal-input"
              />
              <p style={{ fontSize: '0.75rem', color: '#d32f2f', marginTop: '4px', fontWeight: '500' }}>
                WHERE condition is required. Only rows matching the condition will be deleted.
              </p>
            </div>
            
            <div style={{ marginBottom: '12px' }}>
              <label className="modal-label">Admin Password *</label>
              <input
                type="password"
                placeholder="Enter admin password"
                value={adminPassword}
                onChange={(e) => setAdminPassword(e.target.value)}
                className="modal-input"
              />
            </div>
            
            <div className="modal-actions">
              <button onClick={() => {
                setShowDeleteModal(false);
                setDeleteTableName('');
                setDeleteCondition('');
                setAdminPassword('');
              }} className="admin-btn secondary">
                Cancel
              </button>
              <button 
                onClick={handleDeleteSubmit} 
                className="admin-btn" 
                style={{ backgroundColor: '#64748b', color: 'white' }}
                disabled={!deleteTableName.trim() || !deleteCondition.trim() || !adminPassword.trim()}
              >
                Execute Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Insert Data Modal */}
      {showInsertModal && (
        <div className="modal-overlay" onClick={() => setShowInsertModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title" style={{ color: '#1e293b' }}>Insert Data</h3>
            <p className="modal-subtitle">Add new row(s) to a table</p>
            
            <div style={{ marginBottom: '12px' }}>
              <label className="modal-label">Table Name *</label>
              <input
                type="text"
                placeholder=""
                value={insertTableName}
                onChange={(e) => setInsertTableName(e.target.value)}
                className="modal-input"
                autoFocus
              />
            </div>
            
            <div style={{ marginBottom: '12px' }}>
              <label className="modal-label">Column Names *</label>
              <input
                type="text"
                placeholder=""
                value={insertColumns}
                onChange={(e) => setInsertColumns(e.target.value)}
                className="modal-input"
              />
              <p style={{ fontSize: '0.75rem', color: '#666', marginTop: '4px' }}>
                Comma-separated column names without quotes
              </p>
            </div>
            
            <div style={{ marginBottom: '12px' }}>
              <label className="modal-label">Values *</label>
              <input
                type="text"
                placeholder=""
                value={insertValues}
                onChange={(e) => setInsertValues(e.target.value)}
                className="modal-input"
              />
              <p style={{ fontSize: '0.75rem', color: '#666', marginTop: '4px' }}>
                Values in same order as columns. Use quotes for text values.
              </p>
            </div>
            
            <div style={{ marginBottom: '12px' }}>
              <label className="modal-label">Admin Password *</label>
              <input
                type="password"
                placeholder="Enter admin password"
                value={adminPassword}
                onChange={(e) => setAdminPassword(e.target.value)}
                className="modal-input"
              />
            </div>
            
            <div className="modal-actions">
              <button onClick={() => {
                setShowInsertModal(false);
                setInsertTableName('');
                setInsertColumns('');
                setInsertValues('');
                setAdminPassword('');
              }} className="admin-btn secondary">
                Cancel
              </button>
              <button 
                onClick={handleInsertSubmit} 
                className="admin-btn primary"
                disabled={!insertTableName.trim() || !insertColumns.trim() || !insertValues.trim() || !adminPassword.trim()}
              >
                Execute Insert
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderMonitoring = () => (
    <div className="admin-page-content">
      <h2 className="admin-page-title">Data Monitoring</h2>
      
      <div className="admin-tabs">
        <button 
          onClick={() => setMonitoringTab('audit')}
          className={`admin-tab ${monitoringTab === 'audit' ? 'active' : ''}`}
        >
          Audit Logs
        </button>
        <button 
          onClick={() => setMonitoringTab('sessions')}
          className={`admin-tab ${monitoringTab === 'sessions' ? 'active' : ''}`}
        >
          Sessions
        </button>
        <button 
          onClick={() => setMonitoringTab('users')}
          className={`admin-tab ${monitoringTab === 'users' ? 'active' : ''}`}
        >
          Users
        </button>
        <button 
          onClick={() => setMonitoringTab('messages')}
          className={`admin-tab ${monitoringTab === 'messages' ? 'active' : ''}`}
        >
          Messages
        </button>
        <button 
          onClick={() => setMonitoringTab('cases')}
          className={`admin-tab ${monitoringTab === 'cases' ? 'active' : ''}`}
        >
          Cases
        </button>
      </div>

      <div className="admin-monitoring-card">
        <div className="admin-monitoring-header">
          <h3 className="admin-monitoring-title">
            {monitoringTab === 'audit' ? 'Audit Logs' : 
             monitoringTab === 'sessions' ? 'Sessions' :
             monitoringTab === 'users' ? 'Users' :
             monitoringTab === 'messages' ? 'Messages' : 'Cases'}
          </h3>
          <div className="admin-monitoring-tools">
            <div className="admin-search">
              <Search size={12} />
              <input type="text" placeholder="Search..." />
            </div>
            <button className="admin-btn-icon">
              <Filter size={12} />
              Filter
            </button>
          </div>
        </div>
        
        {loading ? (
          <div className="admin-loading">
            <Loader className="spinning" size={24} />
            <p>Loading...</p>
          </div>
        ) : (
          <div className="admin-table-wrapper">
            {monitoringTab === 'audit' && (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>IP Address</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map(log => {
                    const isSessionAction = log.action_type === 'session_start' || log.action_type === 'session_end';
                    const mode = isSessionAction ? extractModeFromDetails(log.details) : null;
                    const stripeColor = mode ? getModeStripeColor(mode) : 'transparent';
                    
                    return (
                      <tr key={log.audit_id}>
                        <td>{formatDateTH(log.created_at)}</td>
                        <td>{log.user_name || 'N/A'}</td>
                        <td>
                          <span 
                            className={`admin-badge ${getActionBadgeColor(log.action_type)}`}
                            style={isSessionAction ? {
                              borderLeft: `4px solid ${stripeColor}`,
                              paddingLeft: '0.5rem'
                            } : {}}
                          >
                            {log.action_type}
                          </span>
                        </td>
                        <td className="admin-mono">{log.ip_address || 'N/A'}</td>
                        <td>
                          {isSessionAction && mode ? (
                            log.details ? log.details.replace(/mode=(exam|practice)\s*\|\s*/i, '') : 'N/A'
                          ) : (
                            log.details || 'N/A'
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}

            {monitoringTab === 'sessions' && (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Session ID</th>
                    <th>User</th>
                    <th>Status</th>
                    <th>Mode</th>
                    <th>Messages</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map(session => (
                    <tr key={session.session_id}>
                      <td className="admin-mono">{session.session_id}</td>
                      <td>{session.user_name}</td>
                      <td>
                        <span className={`admin-badge ${
                          session.status === 'completed' ? 'green' :
                          session.status === 'active' ? 'blue' : 'gray'
                        }`}>
                          {session.status}
                        </span>
                      </td>
                      <td>
                        <span className={`admin-badge ${
                          session.mode === 'exam' ? 'red' : 'teal'
                        }`}>
                          {session.mode}
                        </span>
                      </td>
                      <td>{session.message_count || 0}</td>
<td>{formatDateTH(session.created_at)}</td>
                      <td>
                        {session.has_summary ? (
                          <button
                            onClick={() => handleDownloadPDF(session.session_id)}
                            className="admin-btn-small primary"
                          >
                            <Download size={10} />
                            PDF
                          </button>
                        ) : (
                          <span className="admin-text-muted">No summary</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {monitoringTab === 'users' && (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>User ID</th>
                    <th>Name</th>
                    <th>Student ID</th>
                    <th>Email</th>
                    <th>Sessions</th>
                    <th>Last Login</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user.user_id}>
                      <td className="admin-mono">{user.user_id}</td>
                      <td>{user.name}</td>
                      <td>{user.student_id}</td>
                      <td>{user.email || 'N/A'}</td>
                      <td>{user.session_count || 0}</td>
<td>{user.last_login ? formatDateTH(user.last_login) : 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {monitoringTab === 'messages' && (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Message ID</th>
                    <th>Session ID</th>
                    <th>Role</th>
                    <th>Content</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {messages.map(msg => (
                    <tr key={msg.message_id}>
                      <td className="admin-mono">{msg.message_id}</td>
                      <td className="admin-mono">{msg.session_id}</td>
                      <td>
                        <span className={`admin-badge ${
                          msg.role === 'user' ? 'blue' : 'green'
                        }`}>
                          {msg.role}
                        </span>
                      </td>
                      <td className="admin-truncate">{msg.content}</td>
<td>{formatDateTH(msg.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {monitoringTab === 'cases' && (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Case ID</th>
                    <th>Case Title</th>
                    <th>Case Type</th>
                    <th>Medical Specialty</th>
                    <th>Duration (min)</th>
                    <th>Imported At</th>
                  </tr>
                </thead>
                <tbody>
                  {cases.map(caseItem => (
                    <tr key={caseItem.case_id}>
                      <td className="admin-mono">{caseItem.case_id}</td>
                      <td>{caseItem.case_title || caseItem.case_name}</td>
                      <td>
                        <span className={`admin-badge ${
                          caseItem.case_type === '01' ? 'blue' : 'purple'
                        }`}>
                          {caseItem.case_type === '01' ? 'Child/Parent' : 'Adult'}
                        </span>
                      </td>
                      <td>{caseItem.medical_specialty || 'N/A'}</td>
                      <td>{caseItem.duration_minutes || 'N/A'}</td>
<td>{caseItem.import_at ? formatDateTH(caseItem.import_at) : 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );

  const renderAPIDocs = () => {
    // Get API base URL from environment or use default
    const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const docsUrl = `${apiBaseUrl}/docs`;
    
    return (
      <div className="admin-page-content admin-center">
        <div className="admin-docs-panel">
          <BookOpen size={64} className="admin-docs-icon" />
          <h2 className="admin-docs-title">API Documentation</h2>
          <p className="admin-docs-desc">Access complete API reference and developer guides</p>
          <a
            href={docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="admin-btn-large primary"
          >
            Open API Documentation
            <ExternalLink size={18} />
          </a>
        </div>
      </div>
    );
  };

  // Show loading screen while checking authentication
  if (!adminUser) {
    return (
      <div className="admin-dashboard">
        <div className="admin-loading" style={{ width: '100vw', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Loader className="spinning" size={48} />
          <p>Verifying admin access...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      {renderNavigation()}
      <div className="admin-main">
        {activePage === 'dashboard' && renderDashboard()}
        {activePage === 'query' && renderQueryEditor()}
        {activePage === 'monitoring' && renderMonitoring()}
        {activePage === 'api' && renderAPIDocs()}
      </div>
    </div>
  );
};

export default AdminDashboard;
