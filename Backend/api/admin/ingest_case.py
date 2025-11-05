import os
import json
import argparse
from typing import Optional
from api.db.repository import upsert_case, next_case_id


def ingest_case_file(file_path: str):
    """Read a single JSON case and insert/update into DB.

    Args:
        file_path: Absolute or relative path to JSON file containing a case.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Determine prefix from filename first (more reliable than JSON), fallback to JSON
    base = os.path.basename(file_path)
    prefix = base.split('_', 1)[0]
    if prefix not in ("01", "02"):
        # fallback to JSON case_id
        json_case_id = data.get('case_id', '')
        if '_' in json_case_id:
            prefix = json_case_id.split('_', 1)[0][:2]
        if prefix not in ("01", "02"):
            raise ValueError("Cannot determine case type prefix ('01' or '02') from filename or JSON")

    meta = data.get('case_metadata', {})
    case_name = meta.get('case_title', os.path.basename(file_path))

    # Compute next sequential case_id for this prefix
    case_id = next_case_id(prefix)

    upsert_case(case_id=case_id, case_name=case_name, case_type=prefix, case_data=data)
    return {"case_id": case_id, "case_name": case_name, "case_type": prefix}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest a single case JSON into the database")
    parser.add_argument("--file", required=True, help="Path to the case JSON file")
    args = parser.parse_args()
    info = ingest_case_file(args.file)
    print(json.dumps({"status": "ok", "inserted": info}, ensure_ascii=False))
