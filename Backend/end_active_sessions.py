#!/usr/bin/env python3
"""
Script to properly end all currently active sessions in the database
"""
import sys
import os
from datetime import datetime

# Add the current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from api.db.pool import get_conn
from api.db.time_utils import now_th
import api.db.repository as repo

def end_active_sessions():
    """End all active sessions in the database"""
    
    print("=" * 60)
    print("ENDING ACTIVE SESSIONS")
    print("=" * 60)
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Get all active sessions
            cur.execute("""
                SELECT s.session_id, s.user_id, s.started_at, u.name, u.student_id
                FROM sessions s
                LEFT JOIN users u ON s.user_id = u.user_id
                WHERE s.status = 'active'
                ORDER BY s.started_at
            """)
            
            active_sessions = cur.fetchall()
            
            if not active_sessions:
                print("\n✓ No active sessions found")
                return
            
            print(f"\n📊 Found {len(active_sessions)} active session(s):\n")
            
            for i, session in enumerate(active_sessions, 1):
                session_id = session['session_id']
                user_name = session['name'] or 'Unknown'
                student_id = session['student_id'] or 'Unknown'
                started_at = session['started_at']
                
                # Calculate duration
                if started_at:
                    duration = (datetime.now() - started_at).total_seconds()
                    duration_minutes = duration / 60.0
                else:
                    duration = 0
                    duration_minutes = 0
                
                print(f"{i}. Session: {session_id[:8]}...")
                print(f"   User: {user_name} ({student_id})")
                print(f"   Started: {started_at}")
                print(f"   Duration: {duration_minutes:.1f} minutes")
            
            # Ask for confirmation
            print("\n" + "=" * 60)
            confirm = input(f"End all {len(active_sessions)} session(s)? (yes/no): ").strip().lower()
            
            if confirm != 'yes':
                print("\n✓ Cancelled - no sessions ended")
                return
            
            # End each session
            print(f"\n🔄 Ending {len(active_sessions)} session(s)...\n")
            ended_count = 0
            
            for session in active_sessions:
                session_id = session['session_id']
                user_name = session['name'] or 'Unknown'
                started_at = session['started_at']
                
                try:
                    # Calculate duration
                    if started_at:
                        duration_seconds = int((datetime.now() - started_at).total_seconds())
                    else:
                        duration_seconds = 0
                    
                    # Mark as complete
                    repo.complete_session(
                        session_id=session_id,
                        total_tokens=0,  # Unknown - session was abandoned
                        ended_at=now_th().replace(tzinfo=None),
                        duration_seconds=duration_seconds
                    )
                    
                    # Add audit log
                    repo.add_audit_log(
                        user_id=session['user_id'],
                        session_id=session_id,
                        action_type="session_forced_end",
                        details=f"reason=admin_cleanup | user={user_name} | duration={duration_seconds}s",
                        performed_at=now_th().replace(tzinfo=None),
                        ip_address="system"
                    )
                    
                    ended_count += 1
                    print(f"   ✓ Ended: {session_id[:8]}... ({user_name})")
                    
                except Exception as e:
                    print(f"   ✗ Failed to end {session_id[:8]}...: {e}")
            
            print(f"\n✓ Successfully ended {ended_count}/{len(active_sessions)} session(s)")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    end_active_sessions()
