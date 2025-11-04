"""
Admin Router - Handle admin authentication and dashboard data
"""

import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Database integration
try:
    from api.db import repository as repo
    from api.db.pool import get_conn
    from api.db.time_utils import now_th
except Exception as _db_import_err:
    repo = None
    get_conn = None
    now_th = None

router = APIRouter()

# ============================================
# Request/Response Models
# ============================================

class AdminLoginRequest(BaseModel):
    name: str
    admin_id: str
    email: Optional[str] = None

class AdminLoginResponse(BaseModel):
    success: bool
    is_admin: bool
    user_id: Optional[str] = None
    message: Optional[str] = None

class ExecuteQueryRequest(BaseModel):
    query: str
    admin_id: str  # Required to verify admin access

# ============================================
# Helper Functions
# ============================================

def check_admin_credentials(name: str, admin_id: str) -> bool:
    """Check if provided credentials match admin credentials in environment"""
    admin_name = os.getenv("ADMIN_NAME", "")
    admin_id_env = os.getenv("ADMIN_ID", "")
    
    return (
        name.strip().lower() == admin_name.strip().lower() and
        admin_id.strip() == admin_id_env.strip()
    )

# ============================================
# Admin Endpoints
# ============================================

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """
    Admin login endpoint - validates credentials and logs to audit table
    """
    try:
        if not (repo and now_th and get_conn):
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Check if user is admin
        is_admin = check_admin_credentials(request.name, request.admin_id)
        
        # Create or get user (store in database)
        user_id = repo.create_or_get_user(
            student_id=request.admin_id,
            name=request.name,
            email=request.email,
            preferences={"is_admin": is_admin}
        )
        
        # Update last login
        repo.update_user_last_login(user_id)
        
        # Add audit log
        action_type = "admin_login" if is_admin else "user_login"
        repo.add_audit_log(
            user_id=user_id,
            session_id=None,
            action_type=action_type,
            performed_at=now_th().replace(tzinfo=None)
        )
        
        return AdminLoginResponse(
            success=True,
            is_admin=is_admin,
            user_id=user_id,
            message="Login successful"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/stats")
async def get_admin_stats():
    """
    Get dashboard statistics for admin panel
    """
    try:
        if not get_conn:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        with get_conn() as conn, conn.cursor() as cur:
            # Total users
            cur.execute("SELECT COUNT(*) as count FROM users")
            total_users = cur.fetchone()["count"]
            
            # Active sessions
            cur.execute("SELECT COUNT(*) as count FROM sessions WHERE status = 'active'")
            active_sessions = cur.fetchone()["count"]
            
            # Completed sessions
            cur.execute("SELECT COUNT(*) as count FROM sessions WHERE status = 'complete'")
            completed_sessions = cur.fetchone()["count"]
            
            # Downloads (reports generated)
            cur.execute("SELECT COUNT(*) as count FROM session_reports")
            downloads = cur.fetchone()["count"]
            
            # Mode statistics (exam mode requires checking config if stored in sessions)
            # For now, we'll use placeholder logic or pull from session manager if config is stored
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM sessions 
                WHERE status IN ('active', 'complete')
            """)
            total_sessions = cur.fetchone()["count"]
            
            # Assume exam mode and practice mode split (you may need to adjust based on your config storage)
            exam_mode_sessions = total_sessions // 3  # Placeholder
            practice_mode_sessions = total_sessions - exam_mode_sessions
            
            # Duration statistics
            cur.execute("""
                SELECT 
                    COALESCE(AVG(duration_seconds) / 60, 0) as avg_minutes,
                    COALESCE(MAX(duration_seconds) / 60, 0) as max_minutes,
                    COALESCE(MIN(duration_seconds) / 60, 0) as min_minutes
                FROM sessions
                WHERE duration_seconds IS NOT NULL AND duration_seconds > 0
            """)
            duration_stats = cur.fetchone()
            avg_duration = round(duration_stats["avg_minutes"], 1)
            max_duration = round(duration_stats["max_minutes"], 1)
            min_duration = round(duration_stats["min_minutes"], 1)
            
            # Total messages
            cur.execute("SELECT COUNT(*) as count FROM chat_messages")
            total_messages = cur.fetchone()["count"]
            
            # Token usage (sum of tokens_used from chat_messages)
            # User messages contain input tokens, chatbot/assistant messages contain output tokens
            cur.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN role = 'user' THEN tokens_used ELSE 0 END), 0) as input_tokens,
                    COALESCE(SUM(CASE WHEN role IN ('chatbot', 'assistant') THEN tokens_used ELSE 0 END), 0) as output_tokens
                FROM chat_messages
            """)
            token_stats = cur.fetchone()
            total_input_tokens = token_stats["input_tokens"]
            total_output_tokens = token_stats["output_tokens"]
            
            # Average messages per session
            cur.execute("""
                SELECT 
                    COALESCE(AVG(msg_count), 0) as avg_msgs
                FROM (
                    SELECT session_id, COUNT(*) as msg_count 
                    FROM chat_messages 
                    GROUP BY session_id
                ) as session_messages
            """)
            avg_messages_result = cur.fetchone()
            avg_messages_per_session = round(avg_messages_result["avg_msgs"], 1)
            
            return {
                "success": True,
                "data": {
                    "total_users": total_users,
                    "active_sessions": active_sessions,
                    "completed_sessions": completed_sessions,
                    "downloads": downloads,
                    "exam_mode_sessions": exam_mode_sessions,
                    "practice_mode_sessions": practice_mode_sessions,
                    "avg_duration_minutes": avg_duration,
                    "max_duration_minutes": max_duration,
                    "min_duration_minutes": min_duration,
                    "total_messages": total_messages,
                    "total_input_tokens": total_input_tokens,
                    "total_output_tokens": total_output_tokens,
                    "total_sessions": total_sessions,
                    "avg_messages_per_session": avg_messages_per_session
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@router.get("/audit-logs")
async def get_audit_logs(limit: int = 50):
    """
    Get audit log entries
    """
    try:
        if not get_conn:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    a.log_id as audit_id,
                    u.name as user_name,
                    a.action_type,
                    '' as details,
                    a.performed_at as created_at
                FROM audit_log a
                LEFT JOIN users u ON a.user_id = u.user_id
                ORDER BY a.performed_at DESC
                LIMIT %s
            """, (limit,))
            
            logs = cur.fetchall()
            
            return {
                "success": True,
                "data": logs
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit logs: {str(e)}")


@router.get("/sessions")
async def get_admin_sessions(limit: int = 50):
    """
    Get session data for admin panel
    """
    try:
        if not get_conn:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    s.session_id,
                    u.name as user_name,
                    s.status,
                    'practice' as mode,
                    (SELECT COUNT(*) FROM chat_messages WHERE session_id = s.session_id) as message_count,
                    s.started_at as created_at,
                    EXISTS(SELECT 1 FROM session_reports WHERE session_id = s.session_id) as has_summary
                FROM sessions s
                LEFT JOIN users u ON s.user_id = u.user_id
                ORDER BY s.started_at DESC
                LIMIT %s
            """, (limit,))
            
            sessions = cur.fetchall()
            
            return {
                "success": True,
                "data": sessions
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")


@router.get("/users")
async def get_admin_users(limit: int = 50):
    """
    Get user data for admin panel
    """
    try:
        if not get_conn:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    u.user_id,
                    u.name,
                    u.student_id,
                    u.email,
                    (SELECT COUNT(*) FROM sessions WHERE user_id = u.user_id) as session_count,
                    u.last_login
                FROM users u
                ORDER BY u.created_at DESC
                LIMIT %s
            """, (limit,))
            
            users = cur.fetchall()
            
            return {
                "success": True,
                "data": users
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


@router.get("/messages")
async def get_admin_messages(limit: int = 50):
    """
    Get chat messages for admin panel
    """
    try:
        if not get_conn:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    message_id,
                    session_id,
                    role,
                    content,
                    timestamp as created_at
                FROM chat_messages
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
            
            messages = cur.fetchall()
            
            return {
                "success": True,
                "data": messages
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")


@router.post("/execute-query")
async def execute_query(request: ExecuteQueryRequest):
    """
    Execute a SQL query (admin only, read-only)
    """
    try:
        if not get_conn:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Verify this is an admin request by checking admin_id
        admin_id_env = os.getenv("ADMIN_ID", "")
        if not admin_id_env or request.admin_id.strip() != admin_id_env.strip():
            raise HTTPException(status_code=403, detail="Unauthorized: Admin access required")
        
        query = request.query.strip()
        
        # Security checks
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Block dangerous operations (case-insensitive)
        query_upper = query.upper()
        dangerous_keywords = [
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 
            'UPDATE', 'GRANT', 'REVOKE', 'EXECUTE', 'EXEC'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Query rejected: {keyword} operations are not allowed. Only SELECT queries are permitted."
                )
        
        # Ensure it's a SELECT query
        if not query_upper.startswith('SELECT'):
            raise HTTPException(
                status_code=403,
                detail="Only SELECT queries are allowed"
            )
        
        # Execute query with timeout
        with get_conn() as conn, conn.cursor() as cur:
            # Set statement timeout to 30 seconds
            cur.execute("SET statement_timeout = 30000")
            
            # Execute the query
            cur.execute(query)
            
            # Fetch results
            rows = cur.fetchall()
            
            # Get column names
            columns = [desc[0] for desc in cur.description] if cur.description else []
            
            # Convert rows to list of lists for frontend
            data = []
            for row in rows:
                data.append([row[col] for col in columns])
            
            return {
                "success": True,
                "message": "Query executed successfully",
                "rows": len(data),
                "columns": columns,
                "data": data
            }
            
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        # Provide more helpful error messages
        if "syntax error" in error_message.lower():
            raise HTTPException(status_code=400, detail=f"SQL syntax error: {error_message}")
        elif "does not exist" in error_message.lower():
            raise HTTPException(status_code=400, detail=f"Table or column not found: {error_message}")
        else:
            raise HTTPException(status_code=500, detail=f"Query execution failed: {error_message}")
