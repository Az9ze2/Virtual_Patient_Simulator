"""
Cases Router - Handle case listing and selection
"""

import os
import json
import sys
from typing import List
from fastapi import APIRouter, HTTPException

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.models.schemas import CaseInfo, CaseType, APIResponse

# Optional DB import
try:
    from api.db import repository as repo
except Exception:
    repo = None

router = APIRouter()

# Base path to cases
CASES_BASE_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'src', 'data'
)

@router.get("/list", response_model=APIResponse)
async def list_cases():
    """
    List available cases. Prefer DB if available; fallback to local files.
    """
    try:
        cases = []

        # Try DB first
        used_db = False
        if repo:
            try:
                rows = repo.list_cases()
                if rows:
                    used_db = True
                    for r in rows:
                        try:
                            cases.append(CaseInfo(
                                filename=r['case_id'],  # pass case_id; backend can load from DB by id
                                case_id=r['case_id'],
                                case_title=r['case_name'],
                                case_type=CaseType(r['case_type']),
                                medical_specialty="",
                                exam_duration_minutes=0,
                            ))
                        except Exception:
                            continue
            except Exception:
                used_db = False

        if not used_db:
            # Fallback to files
            cases_01_path = os.path.join(CASES_BASE_PATH, "cases_01")
            if os.path.exists(cases_01_path):
                for filename in os.listdir(cases_01_path):
                    if filename.endswith('.json'):
                        case_info = _load_case_info(cases_01_path, filename, CaseType.CHILD)
                        if case_info:
                            cases.append(case_info)
            cases_02_path = os.path.join(CASES_BASE_PATH, "cases_02")
            if os.path.exists(cases_02_path):
                for filename in os.listdir(cases_02_path):
                    if filename.endswith('.json'):
                        case_info = _load_case_info(cases_02_path, filename, CaseType.ADULT)
                        if case_info:
                            cases.append(case_info)
        
        cases.sort(key=lambda x: x.case_id)
        
        return APIResponse(
            success=True,
            message=f"Found {len(cases)} cases",
            data={"cases": cases}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list cases: {str(e)}"
        )

@router.get("/get/{filename}")
async def get_case_data(filename: str):
    """
    Get full case data for a specific case file
    """
    try:
        # Determine which folder to look in based on filename prefix
        if filename.startswith("01_"):
            cases_path = os.path.join(CASES_BASE_PATH, "cases_01")
        elif filename.startswith("02_"):
            cases_path = os.path.join(CASES_BASE_PATH, "cases_02")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid case filename format: {filename}"
            )
        
        case_file_path = os.path.join(cases_path, filename)
        
        if not os.path.exists(case_file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Case file not found: {filename}"
            )
        
        with open(case_file_path, 'r', encoding='utf-8') as f:
            case_data = json.load(f)
        
        return APIResponse(
            success=True,
            message="Case data retrieved successfully",
            data={"case_data": case_data, "filename": filename}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load case data: {str(e)}"
        )

@router.get("/categories")
async def get_case_categories():
    """
    Get case categories and counts
    """
    try:
        cases_01_path = os.path.join(CASES_BASE_PATH, "cases_01")
        cases_02_path = os.path.join(CASES_BASE_PATH, "cases_02")
        
        child_cases = 0
        adult_cases = 0
        
        if os.path.exists(cases_01_path):
            child_cases = len([f for f in os.listdir(cases_01_path) if f.endswith('.json')])
        
        if os.path.exists(cases_02_path):
            adult_cases = len([f for f in os.listdir(cases_02_path) if f.endswith('.json')])
        
        categories = [
            {
                "type": "child",
                "name": "Child/Parent Cases",
                "description": "Cases involving children with parent/guardian interaction",
                "count": child_cases,
                "folder": "cases_01"
            },
            {
                "type": "adult", 
                "name": "Adult Patient Cases",
                "description": "Cases with direct adult patient interaction",
                "count": adult_cases,
                "folder": "cases_02"
            }
        ]
        
        return APIResponse(
            success=True,
            message="Case categories retrieved successfully",
            data={"categories": categories}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get case categories: {str(e)}"
        )

def _load_case_info(cases_path: str, filename: str, case_type: CaseType) -> CaseInfo:
    """
    Load case information from JSON file
    """
    try:
        file_path = os.path.join(cases_path, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            case_data = json.load(f)
        
        case_metadata = case_data.get('case_metadata', {})
        
        return CaseInfo(
            filename=filename,
            case_id=case_data.get('case_id', ''),
            case_title=case_metadata.get('case_title', ''),
            case_type=case_type,
            medical_specialty=case_metadata.get('medical_specialty', ''),
            exam_duration_minutes=case_metadata.get('exam_duration_minutes', 0)
        )
        
    except Exception as e:
        print(f"Warning: Failed to load case info for {filename}: {e}")
        return None
