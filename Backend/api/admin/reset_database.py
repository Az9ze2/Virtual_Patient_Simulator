import os
import json
import argparse
import getpass
from typing import Optional
from api.db.pool import get_conn
from api.db.schema_sql import SCHEMA_SQL, DROP_SCHEMA_SQL

# Accept both new and legacy env var names
ADMIN_SECRET_ENV_KEYS = ["ADMIN_OPS_KEY", "ADMIN_OPS_SECRET"]  # preferred, legacy


def reset_database(confirm: Optional[str] = None):
    # Look up secret from any accepted env var
    secret = None
    for key in ADMIN_SECRET_ENV_KEYS:
        val = os.getenv(key)
        if val:
            secret = val
            break
    if not secret:
        names = ", ".join(ADMIN_SECRET_ENV_KEYS)
        raise RuntimeError(f"Admin secret not set. Define one of [{names}] in environment to enable reset.")
    if confirm != secret:
        raise PermissionError("Invalid admin confirmation token for reset.")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
        return {
            "status": "ok",
            "message": "Database schema dropped and recreated",
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dangerous: Drop and recreate database schema")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--confirm", help="Admin secret to confirm reset (compared to env ADMIN_OPS_KEY/ADMIN_OPS_SECRET)")
    group.add_argument("--prompt", action="store_true", help="Prompt for admin secret instead of passing via CLI")
    parser.add_argument("--drop-only", action="store_true", help="Only drop all tables; do not recreate schema")
    args = parser.parse_args()

    if args.prompt and not args.confirm:
        confirm_value = getpass.getpass("Enter admin secret: ")
    else:
        confirm_value = args.confirm

    try:
        # Verify secret
        _ = reset_database(confirm_value)
        # If only dropping is requested, run DROP only
        if args.drop_only:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(DROP_SCHEMA_SQL)
            print(json.dumps({"status": "ok", "message": "All tables dropped (not recreated)"}))
        else:
            # reset_database already performed drop+create
            print(json.dumps({"status": "ok", "message": "Schema dropped and recreated"}))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        raise
        