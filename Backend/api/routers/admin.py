"""
Admin Router - Handle admin authentication and dashboard data
"""

import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
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

class AdminLogoutRequest(BaseModel):
    user_id: str
    is_admin: bool

class ExecuteQueryRequest(BaseModel):
    query: str
    admin_id: str  # Required to verify admin access
    admin_password: Optional[str] = None  # Required for DELETE/INSERT operations
    query_name: Optional[str] = None  # Optional preset query name for better audit logging

# ============================================
# Helper Functions
# ============================================

def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request, checking proxy headers first.
    Works with proxies, load balancers (Railway, Nginx, Cloudflare, etc.)
    """
    # Check X-Forwarded-For header (most common for proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # The first one is the original client
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header (used by some proxies)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Check CF-Connecting-IP (Cloudflare)
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    
    # Fallback to direct client connection
    if request.client and request.client.host:
        return request.client.host
    
    # Last resort
    return "Unknown"

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
async def admin_login(request: AdminLoginRequest, fastapi_request: Request):
    """
    Admin login endpoint - validates credentials and logs to audit table with IP address
    """
    try:
        if not (repo and now_th and get_conn):
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get client IP address with proxy support
        ip_address = get_client_ip(fastapi_request)
        
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
        
        # Add audit log with IP address
        action_type = "admin_login" if is_admin else "user_login"
        repo.add_audit_log(
            user_id=user_id,
            session_id=None,
            action_type=action_type,
            details=f"user_id={user_id} | name={request.name} | email={request.email or '-'}",
            performed_at=now_th().replace(tzinfo=None),
            ip_address=ip_address
        )
        
        return AdminLoginResponse(
            success=True,
            is_admin=is_admin,
            user_id=user_id,
            message="Login successful"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/logout")
async def admin_logout(request: AdminLogoutRequest, fastapi_request: Request):
    """
    Logout endpoint - logs user/admin logout to audit table with IP address
    """
    try:
        if not (repo and now_th):
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get client IP address with proxy support
        ip_address = get_client_ip(fastapi_request)
        
        # Add audit log
        action_type = "admin_logout" if request.is_admin else "user_logout"
        # Fetch user info for details
        user_name = None
        email = None
        student_id = None
        try:
            if get_conn:
                with get_conn() as conn, conn.cursor() as cur:
                    cur.execute("SELECT name, email, student_id FROM users WHERE user_id = %s LIMIT 1", (request.user_id,))
                    row = cur.fetchone()
                    if row:
                        user_name = row.get("name")
                        email = row.get("email")
                        student_id = row.get("student_id")
        except Exception:
            pass
        details = f"user_id={request.user_id} | name={user_name or '-'} | email={email or '-'} | student_id={student_id or '-'}"
        repo.add_audit_log(
            user_id=request.user_id,
            session_id=None,
            action_type=action_type,
            details=details,
            performed_at=now_th().replace(tzinfo=None),
            ip_address=ip_address
        )
        
        return {
            "success": True,
            "message": "Logout recorded"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")


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
                    a.details,
                    a.ip_address,
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


@router.get("/cases")
async def get_admin_cases(limit: int = 100):
    """
    Get all cases for admin panel
    """
    try:
        if not get_conn:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    case_id,
                    case_name,
                    case_type,
                    (case_data->'case_metadata'->>'case_title') as case_title,
                    (case_data->'case_metadata'->>'medical_specialty') as medical_specialty,
                    NULLIF((case_data->'case_metadata'->>'exam_duration_minutes'), '')::INT as duration_minutes,
                    import_at
                FROM cases
                ORDER BY case_id
                LIMIT %s
            """, (limit,))
            
            cases = cur.fetchall()
            
            return {
                "success": True,
                "data": cases
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cases: {str(e)}")


@router.get("/home-stats")
async def get_home_stats():
    """
    Get statistics for homepage display
    """
    try:
        if not get_conn:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        with get_conn() as conn, conn.cursor() as cur:
            # Active sessions count
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM sessions 
                WHERE status = 'active'
            """)
            active_sessions = cur.fetchone()["count"]
            
            # Average duration in minutes
            cur.execute("""
                SELECT COALESCE(AVG(duration_seconds) / 60, 0) as avg_minutes
                FROM sessions
                WHERE duration_seconds IS NOT NULL AND duration_seconds > 0
            """)
            avg_duration = round(cur.fetchone()["avg_minutes"], 0)
            
            # Total cases
            cur.execute("SELECT COUNT(*) as count FROM cases")
            total_cases = cur.fetchone()["count"]
            
            return {
                "success": True,
                "data": {
                    "active_sessions": active_sessions,
                    "avg_duration_minutes": int(avg_duration),
                    "total_cases": total_cases
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch home stats: {str(e)}")


@router.post("/execute-query")
async def execute_query(request: ExecuteQueryRequest, fastapi_request: Request):
    """
    Execute a SQL query (admin only)
    Supports: SELECT (no password), DELETE/INSERT (requires password)
    All queries are logged to backend and audit_log table
    """
    admin_user_id = None
    admin_name = None
    ip_address = None
    
    try:
        if not get_conn:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        # Get client IP address with proxy support
        ip_address = get_client_ip(fastapi_request)
        
        # Verify this is an admin request by checking admin_id
        admin_id_env = os.getenv("ADMIN_ID", "")
        admin_name_env = os.getenv("ADMIN_NAME", "")
        
        if not admin_id_env or request.admin_id.strip() != admin_id_env.strip():
            print(f"[QUERY EDITOR] ❌ Unauthorized access attempt from IP: {ip_address}")
            raise HTTPException(status_code=403, detail="Unauthorized: Admin access required")
        
        # Get admin user_id from database
        admin_name = admin_name_env
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE student_id = %s LIMIT 1", (request.admin_id,))
            result = cur.fetchone()
            if result:
                admin_user_id = result["user_id"]
        
        query = request.query.strip()
        
        # Security checks
        if not query:
            print(f"[QUERY EDITOR] ⚠️ Empty query from admin {admin_name} (ID: {request.admin_id}, IP: {ip_address})")
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        print(f"[QUERY EDITOR] 📝 Query received from admin {admin_name} (ID: {request.admin_id}, IP: {ip_address})")
        print(f"[QUERY EDITOR] 📄 Query: {query}")
        
        import re
        query_upper = query.upper()
        
        # Block these operations ALWAYS (even with password)
        forbidden_keywords = ['DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE', 'EXEC']
        for keyword in forbidden_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query_upper):
                print(f"[QUERY EDITOR] 🚫 BLOCKED: {keyword} operation attempted by {admin_name} (IP: {ip_address})")
                print(f"[QUERY EDITOR] 🚫 Blocked query: {query}")
                
                # Log to audit_log
                if admin_user_id and repo and now_th:
                    query_function = request.query_name if request.query_name else "Custom Query"
                    repo.add_audit_log(
                        user_id=admin_user_id,
                        session_id=None,
                        action_type="query_editor_blocked",
                        details=f"query={query_function} | op={keyword} | status=blocked | input={query[:100]}",
                        performed_at=now_th().replace(tzinfo=None),
                        ip_address=ip_address
                    )
                
                raise HTTPException(
                    status_code=403, 
                    detail=f"Query rejected: {keyword} operations are not allowed."
                )
        
        # Check for DELETE or INSERT or UPDATE (requires password)
        requires_password = False
        operation_type = "SELECT"
        dangerous_operations = ['DELETE', 'INSERT', 'UPDATE']
        for operation in dangerous_operations:
            pattern = r'\b' + re.escape(operation) + r'\b'
            if re.search(pattern, query_upper):
                requires_password = True
                operation_type = operation
                break
        
        # If dangerous operation, verify password
        if requires_password:
            print(f"[QUERY EDITOR] ⚠️  {operation_type} operation detected - password verification required")
            
            # Additional security: DELETE operations MUST have WHERE clause
            if operation_type == 'DELETE':
                # Check if query has WHERE clause
                if not re.search(r'\bWHERE\b', query_upper):
                    print(f"[QUERY EDITOR] 🚫 BLOCKED: DELETE without WHERE clause by {admin_name} (IP: {ip_address})")
                    print(f"[QUERY EDITOR] 🚫 Blocked query: {query}")
                    
                    # Log to audit_log
                    if admin_user_id and repo and now_th:
                        repo.add_audit_log(
                            user_id=admin_user_id,
                            session_id=None,
                            action_type="query_editor_blocked",
                            details=f"BLOCKED DELETE without WHERE: {query[:200]}",
                            performed_at=now_th().replace(tzinfo=None),
                            ip_address=ip_address
                        )
                    
                    raise HTTPException(
                        status_code=403,
                        detail="DELETE operations must include a WHERE clause to prevent accidental deletion of all rows."
                    )
            
            admin_password_env = os.getenv("ADMIN_PASSWORD", "")
            if not admin_password_env:
                print(f"[QUERY EDITOR] ❌ Admin password not configured on server")
                raise HTTPException(
                    status_code=500,
                    detail="Admin password not configured on server"
                )
            
            if not request.admin_password or request.admin_password.strip() != admin_password_env.strip():
                print(f"[QUERY EDITOR] ❌ Incorrect password for {operation_type} operation by {admin_name} (IP: {ip_address})")
                
                # Log failed password attempt
                if admin_user_id and repo and now_th:
                    query_function = request.query_name if request.query_name else "Custom Query"
                    repo.add_audit_log(
                        user_id=admin_user_id,
                        session_id=None,
                        action_type="query_editor_password_failed",
                        details=f"query={query_function} | op={operation_type} | status=password_failed | input={query[:100]}",
                        performed_at=now_th().replace(tzinfo=None),
                        ip_address=ip_address
                    )
                
                raise HTTPException(
                    status_code=403,
                    detail="Incorrect password. DELETE/INSERT/UPDATE operations require password verification."
                )
            
            print(f"[QUERY EDITOR] ✅ Password verified for {operation_type} operation")
        
        # Execute query with timeout
        print(f"[QUERY EDITOR] ⏳ Executing query...")
        
        with get_conn() as conn, conn.cursor() as cur:
            # Set statement timeout to 30 seconds
            cur.execute("SET statement_timeout = 30000")
            
            # Execute the query
            cur.execute(query)
            
            # For INSERT/UPDATE/DELETE, commit and return affected rows
            if requires_password:
                conn.commit()
                affected_rows = cur.rowcount
                
                print(f"[QUERY EDITOR] ✅ {operation_type} operation completed successfully")
                print(f"[QUERY EDITOR] 📊 Rows affected: {affected_rows}")
                
                # Log to audit_log
                if admin_user_id and repo and now_th:
                    query_function = request.query_name if request.query_name else "Custom Query"
                    repo.add_audit_log(
                        user_id=admin_user_id,
                        session_id=None,
                        action_type=f"query_editor_{operation_type.lower()}",
                        details=f"query={query_function} | op={operation_type} | affected_rows={affected_rows}",
                        performed_at=now_th().replace(tzinfo=None),
                        ip_address=ip_address
                    )
                
                return {
                    "success": True,
                    "message": f"Query executed successfully. {affected_rows} row(s) affected.",
                    "rows": affected_rows,
                    "columns": [],
                    "data": []
                }
            
            # For SELECT queries, fetch and return results
            rows = cur.fetchall()
            
            # Get column names
            columns = [desc[0] for desc in cur.description] if cur.description else []
            
            # Convert rows to list of lists for frontend
            data = []
            for row in rows:
                data.append([row[col] for col in columns])
            
            print(f"[QUERY EDITOR] ✅ SELECT query completed successfully")
            print(f"[QUERY EDITOR] 📊 Rows returned: {len(data)}")
            print(f"[QUERY EDITOR] 📋 Columns: {', '.join(columns)}")
            
            # Log to audit_log
            if admin_user_id and repo and now_th:
                query_function = request.query_name if request.query_name else "Custom Query"
                repo.add_audit_log(
                    user_id=admin_user_id,
                    session_id=None,
                    action_type="query_editor_select",
                    details=f"query={query_function} | op=SELECT | rows={len(data)}",
                    performed_at=now_th().replace(tzinfo=None),
                    ip_address=ip_address
                )
            
            return {
                "success": True,
                "message": "Query executed successfully",
                "rows": len(data),
                "columns": columns,
                "data": data
            }
            
    except HTTPException as http_err:
        # Log HTTP exceptions (security blocks, auth failures, etc.)
        print(f"[QUERY EDITOR] ⚠️ HTTP Exception: {http_err.detail}")
        raise
    except Exception as e:
        error_message = str(e)
        
        print(f"[QUERY EDITOR] ❌ Query execution error: {error_message}")
        print(f"[QUERY EDITOR] ❌ Failed query: {query if 'query' in locals() else 'N/A'}")
        
        # Log error to audit_log
        if admin_user_id and repo and now_th and 'query' in locals():
            query_function = request.query_name if hasattr(request, 'query_name') and request.query_name else "Custom Query"
            repo.add_audit_log(
                user_id=admin_user_id,
                session_id=None,
                action_type="query_editor_error",
                details=f"query={query_function} | status=error | message={error_message[:100]}",
                performed_at=now_th().replace(tzinfo=None),
                ip_address=ip_address if ip_address else "Unknown"
            )
        
        # Provide more helpful error messages
        if "syntax error" in error_message.lower():
            raise HTTPException(status_code=400, detail=f"SQL syntax error: {error_message}")
        elif "does not exist" in error_message.lower():
            raise HTTPException(status_code=400, detail=f"Table or column not found: {error_message}")
        else:
            raise HTTPException(status_code=500, detail=f"Query execution failed: {error_message}")
