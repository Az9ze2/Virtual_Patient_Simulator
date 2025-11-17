#!/usr/bin/env python3
"""
Test script to view and cleanup active sessions
"""
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from api.utils.session_manager import session_manager

def main():
    print("=" * 60)
    print("SESSION CLEANUP TEST")
    print("=" * 60)
    
    # Get active sessions
    sessions = session_manager.get_active_sessions_details()
    
    print(f"\n📊 Total Active Sessions: {len(sessions)}")
    print("-" * 60)
    
    if sessions:
        for i, s in enumerate(sessions, 1):
            print(f"\n{i}. Session ID: {s['session_id'][:8]}...")
            print(f"   User: {s['user_name']} ({s['student_id']})")
            print(f"   Case: {s['case_title']} ({s['case_id']})")
            print(f"   Created: {s['created_at']}")
            print(f"   Last Activity: {s['last_activity']}")
            print(f"   Inactive: {s['inactive_minutes']} minutes")
            print(f"   Messages: {s['total_messages']}")
            print(f"   Mode: {'Exam' if s['exam_mode'] else 'Practice'}")
    else:
        print("\n✓ No active sessions found")
    
    # Ask if user wants to cleanup
    print("\n" + "=" * 60)
    print("CLEANUP OPTIONS")
    print("=" * 60)
    print(f"Default timeout: {session_manager.SESSION_TIMEOUT_MINUTES} minutes")
    print("\n1. Cleanup sessions inactive > 60 minutes (default)")
    print("2. Cleanup sessions inactive > 30 minutes")
    print("3. Cleanup sessions inactive > 10 minutes")
    print("4. Cleanup all sessions (0 minutes)")
    print("5. Exit without cleanup")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    timeout_map = {
        "1": 60,
        "2": 30,
        "3": 10,
        "4": 0
    }
    
    if choice in timeout_map:
        timeout = timeout_map[choice]
        print(f"\n🧹 Running cleanup with timeout: {timeout} minutes...")
        cleaned = session_manager.cleanup_inactive_sessions(timeout)
        
        if cleaned:
            print(f"\n✓ Cleaned up {len(cleaned)} session(s):")
            for session_id, info in cleaned:
                print(f"   - {info['user_name']} ({info['student_id']}): {info['case_title']}")
                print(f"     Inactive: {info['inactive_minutes']} minutes")
        else:
            print("\n✓ No sessions to cleanup")
    else:
        print("\n✓ Exiting without cleanup")
    
    # Show remaining sessions
    remaining = session_manager.get_active_sessions_details()
    print(f"\n📊 Remaining Active Sessions: {len(remaining)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
