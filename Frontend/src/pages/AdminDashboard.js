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

  useEffect(() => {
    if (activePage === 'dashboard') {
      loadDashboardData();
    } else if (activePage === 'monitoring') {
      loadMonitoringData();
    }
  }, [activePage, monitoringTab]);

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
    if (action.includes('session_start') || action.includes('start')) return 'green';
    if (action.includes('session_end') || action.includes('end')) return 'orange';
    if (action.includes('delete') || action.includes('remove')) return 'red';
    if (action.includes('update') || action.includes('edit')) return 'purple';
    if (action.includes('download')) return 'teal';
    if (action.includes('upload')) return 'indigo';
    if (action.includes('admin')) return 'pink';
    return 'blue'; // default
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
      }
    } catch (error) {
      console.error('Failed to load monitoring data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunQuery = async () => {
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

      const result = await apiService.executeQuery(sqlQuery, adminId);
      setQueryResult(result);
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
        <p className="admin-nav-footer-user">Admin</p>
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
          <div className="admin-stats-grid">
            {[
              { label: 'Total Users', value: stats.total_users, icon: Users, color: 'blue' },
              { label: 'Active Sessions', value: stats.active_sessions, icon: Activity, color: 'green' },
              { label: 'Completed', value: stats.completed_sessions, icon: FileText, color: 'purple' },
              { label: 'Downloads', value: stats.downloads, icon: Download, color: 'orange' },
              { label: 'Exam Mode', value: stats.exam_mode_sessions, icon: Edit, color: 'red' },
              { label: 'Practice Mode', value: stats.practice_mode_sessions, icon: Play, color: 'teal' },
              { label: 'Avg Duration', value: `${stats.avg_duration_minutes}m`, icon: Activity, color: 'indigo' },
              { label: 'Max Duration', value: `${stats.max_duration_minutes}m`, icon: Activity, color: 'pink' },
              { label: 'Min Duration', value: `${stats.min_duration_minutes}m`, icon: Activity, color: 'cyan' },
              { label: 'Total Messages', value: stats.total_messages, icon: FileText, color: 'violet' },
              { label: 'Input Tokens', value: stats.total_input_tokens, icon: FileText, color: 'amber' },
              { label: 'Output Tokens', value: stats.total_output_tokens, icon: FileText, color: 'lime' }
            ].map((stat, idx) => {
              const Icon = stat.icon;
              return (
                <div key={idx} className="admin-stat-card">
                  <div className="admin-stat-header">
                    <div className={`admin-stat-icon ${stat.color}`}>
                      <Icon size={14} />
                    </div>
                    <span className="admin-stat-value">{stat.value}</span>
                  </div>
                  <p className="admin-stat-label">{stat.label}</p>
                </div>
              );
            })}
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
                      <p className="admin-activity-meta">{log.user_name || 'System'} • {new Date(log.created_at).toLocaleString()}</p>
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

  const renderQueryEditor = () => (
    <div className="admin-page-content">
      <h2 className="admin-page-title">Query Editor</h2>
      
      <div className="admin-query-container">
        <div className="admin-query-panel">
          <div className="admin-query-header">
            <h3 className="admin-query-title">SQL Query</h3>
            <div className="admin-query-actions">
              <button onClick={handleRunQuery} className="admin-btn primary">
                <Play size={12} />
                Run
              </button>
              <button onClick={() => setSqlQuery('')} className="admin-btn secondary">
                Clear
              </button>
            </div>
          </div>
          
          <textarea
            value={sqlQuery}
            onChange={(e) => setSqlQuery(e.target.value)}
            placeholder="Enter your SQL query here..."
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
                          <td key={cellIdx}>{cell}</td>
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
      </div>

      <div className="admin-monitoring-card">
        <div className="admin-monitoring-header">
          <h3 className="admin-monitoring-title">
            {monitoringTab === 'audit' ? 'Audit Logs' : 
             monitoringTab === 'sessions' ? 'Sessions' :
             monitoringTab === 'users' ? 'Users' : 'Messages'}
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
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map(log => (
                    <tr key={log.audit_id}>
                      <td>{new Date(log.created_at).toLocaleString()}</td>
                      <td>{log.user_name || 'N/A'}</td>
                      <td>
                        <span className={`admin-badge ${getActionBadgeColor(log.action_type)}`}>
                          {log.action_type}
                        </span>
                      </td>
                      <td>{log.details || 'N/A'}</td>
                    </tr>
                  ))}
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
                      <td>{new Date(session.created_at).toLocaleString()}</td>
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
                      <td>{user.last_login ? new Date(user.last_login).toLocaleString() : 'N/A'}</td>
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
                      <td>{new Date(msg.created_at).toLocaleString()}</td>
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
