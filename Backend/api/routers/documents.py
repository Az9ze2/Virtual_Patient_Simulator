"""
Documents Router - Handle document upload and data extraction
"""

import os
import sys
import tempfile
import time
import json
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import io

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.utils.data_extraction import process_document
from api.models.schemas import (
    APIResponse, DocumentUploadResponse, ExtractedDataResponse, 
    DataVerification, CaseType
)

router = APIRouter()

# Paths for extraction process
SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'src', 'core', 'config', 'example_schema.json'
)
PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'src', 'core', 'config', 'extraction_prompt.txt'
)
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'src', 'data'
)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document file for processing
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="Only PDF and DOCX files are supported"
            )
        
        # Read file content
        content = await file.read()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            suffix=os.path.splitext(file.filename)[1],
            delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process document with data extraction
            start_time = time.time()
            
            # Determine output directory based on case type (will be determined after extraction)
            temp_output_dir = tempfile.mkdtemp()
            
            # Process the document
            process_document(
                doc_path=temp_file_path,
                schema_path=SCHEMA_PATH,
                prompt_path=PROMPT_PATH,
                output_dir=temp_output_dir
            )
            
            processing_time = time.time() - start_time
            
            # Find the generated file
            output_files = [f for f in os.listdir(temp_output_dir) if f.endswith('.json')]
            if not output_files:
                raise HTTPException(
                    status_code=500,
                    detail="No output file generated during processing"
                )
            
            output_file = output_files[0]
            output_file_path = os.path.join(temp_output_dir, output_file)
            
            # Read extracted data
            with open(output_file_path, 'r', encoding='utf-8') as f:
                extracted_data = json.load(f)
            
            # Determine case type based on patient age
            case_type = _determine_case_type(extracted_data)
            
            # Clean up temporary files
            os.unlink(temp_file_path)
            
            return APIResponse(
                success=True,
                message="Document processed successfully",
                data={
                    "filename": file.filename,
                    "extracted_data": extracted_data,
                    "case_type": case_type,
                    "processing_time": processing_time,
                    "suggested_filename": output_file,
                    "temp_output_path": output_file_path  # For verification endpoint
                }
            )
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.post("/verify-and-save")
async def verify_and_save_data(
    extracted_data: Dict[str, Any],
    verified: bool = Form(...),
    corrections: Dict[str, Any] = Form(None)
):
    """
    Verify extracted data and save to appropriate case folder
    """
    try:
        # Apply corrections if provided
        final_data = extracted_data.copy()
        if corrections and verified:
            final_data.update(corrections)
        
        if not verified:
            return APIResponse(
                success=False,
                message="Data verification failed - please make corrections",
                data={"requires_correction": True}
            )
        
        # Determine case type and target folder
        case_type = _determine_case_type(final_data)
        
        if case_type == CaseType.CHILD:
            target_folder = os.path.join(OUTPUT_DIR, "cases_01")
        else:
            target_folder = os.path.join(OUTPUT_DIR, "cases_02")
        
        # Ensure target folder exists
        os.makedirs(target_folder, exist_ok=True)
        
        # Generate unique filename
        case_title = final_data.get('case_metadata', {}).get('case_title', 'unknown_case')
        case_title_clean = "".join(c for c in case_title if c.isalnum() or c in (' ', '_')).rstrip()
        case_title_clean = case_title_clean.replace(' ', '_').lower()
        
        # Find next available number
        prefix = "01" if case_type == CaseType.CHILD else "02"
        existing_files = [
            f for f in os.listdir(target_folder) 
            if f.startswith(f"{prefix}_") and f.endswith('.json')
        ]
        
        next_num = 1
        if existing_files:
            numbers = []
            for f in existing_files:
                try:
                    num_part = f.split('_')[1]
                    numbers.append(int(num_part))
                except:
                    continue
            if numbers:
                next_num = max(numbers) + 1
        
        filename = f"{prefix}_{next_num:02d}_{case_title_clean}.json"
        output_path = os.path.join(target_folder, filename)
        
        # Save the verified data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        return APIResponse(
            success=True,
            message="Data verified and saved successfully",
            data={
                "saved_filename": filename,
                "case_type": case_type,
                "case_id": final_data.get('case_id', ''),
                "case_title": final_data.get('case_metadata', {}).get('case_title', ''),
                "output_path": output_path
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify and save data: {str(e)}"
        )

@router.get("/schema")
async def get_extraction_schema():
    """
    Get the JSON schema used for data extraction
    """
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        return APIResponse(
            success=True,
            message="Schema retrieved successfully",
            data={"schema": schema}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get schema: {str(e)}"
        )

@router.get("/extraction-prompt")
async def get_extraction_prompt():
    """
    Get the prompt used for data extraction
    """
    try:
        with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
            prompt = f.read()
        
        return APIResponse(
            success=True,
            message="Extraction prompt retrieved successfully",
            data={"prompt": prompt}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get extraction prompt: {str(e)}"
        )

@router.get("/download-template")
async def download_case_template():
    """
    Download a template JSON file showing the expected case structure
    """
    try:
        # Create a minimal template based on the schema
        template = {
            "case_id": "TEMPLATE-CASE-ID",
            "case_metadata": {
                "case_title": "Template Case Title",
                "medical_specialty": "Medical Specialty",
                "exam_type": "Exam Type",
                "exam_duration_minutes": 10
            },
            "examiner_view": {
                "patient_background": {
                    "name": "Patient Name",
                    "age": {"value": 25, "unit": "years"},
                    "sex": "Male/Female",
                    "occupation": "Patient Occupation",
                    "chief_complaint": "Main reason for visit"
                },
                "physical_examination": {
                    "general_appearance": "Patient appearance description",
                    "vital_signs": {
                        "body_temperature_in_celsius": 37.0,
                        "heart_rate_in_beats_per_minute": 80,
                        "respiratory_rate_in_breaths_per_minute": 18,
                        "blood_pressure_in_mmHg": "120/80"
                    }
                }
            },
            "simulation_view": {
                "simulator_profile": {
                    "name": "Simulator Name",
                    "age": 30,
                    "role": "Patient or Parent/Guardian"
                },
                "simulation_instructions": {
                    "scenario": "Brief scenario description",
                    "fallback_question": {
                        "question_limit_type": "single",
                        "questions": [
                            {
                                "text": "Sample fallback question",
                                "asked": False
                            }
                        ]
                    },
                    "sample_dialogue": [
                        {
                            "topic": "Sample Topic",
                            "dialogue": [
                                {
                                    "type": "question",
                                    "role": "examiner", 
                                    "text": "Sample question"
                                },
                                {
                                    "type": "answer",
                                    "role": "patient",
                                    "text": "Sample answer"
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        template_json = json.dumps(template, ensure_ascii=False, indent=2)
        
        return StreamingResponse(
            io.BytesIO(template_json.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=case_template.json"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download template: {str(e)}"
        )

def _determine_case_type(extracted_data: Dict[str, Any]) -> CaseType:
    """
    Determine if case is child or adult based on patient age
    """
    try:
        age_info = extracted_data["examiner_view"]["patient_background"]["age"]
        
        # Handle both dict and plain int
        if isinstance(age_info, dict) and "value" in age_info:
            age = int(age_info["value"])
        elif isinstance(age_info, (int, float)):
            age = int(age_info)
        else:
            # Default to child if age format not recognized
            return CaseType.CHILD
        
        return CaseType.ADULT if age >= 18 else CaseType.CHILD
        
    except Exception:
        # Default to child case on error
        return CaseType.CHILD
