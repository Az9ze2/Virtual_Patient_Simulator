#!/usr/bin/env python3
"""
Debug script to check what's wrong with specific cases
"""

import json
import sys
from pathlib import Path

def debug_case(case_filename):
    """Debug a specific case file"""
    data_dir = Path("C:/Users/acer/Desktop/IRPC_Internship/Virtual_Patient_Simulator/Backend/Extracted_Data_json")
    case_path = data_dir / case_filename
    
    print(f"🔍 Debugging: {case_filename}")
    print(f"📁 File path: {case_path}")
    print(f"📄 File exists: {case_path.exists()}")
    
    if not case_path.exists():
        print("❌ File does not exist!")
        return
    
    try:
        with open(case_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ JSON loads successfully")
        print(f"📊 Top-level keys: {list(data.keys())}")
        
        # Check case_metadata
        if "case_metadata" in data:
            print(f"📋 case_metadata keys: {list(data['case_metadata'].keys())}")
            print(f"📝 case_title type: {type(data['case_metadata'].get('case_title'))}")
        else:
            print("❌ Missing case_metadata")
        
        # Check simulation_view
        if "simulation_view" in data:
            print(f"🎭 simulation_view keys: {list(data['simulation_view'].keys())}")
            
            # Check simulator profiles
            for profile_key in ["simulator_profile", "mother_profile", "caregiver_profile", "patient_profile"]:
                if profile_key in data["simulation_view"]:
                    print(f"👤 Found {profile_key}: {type(data['simulation_view'][profile_key])}")
            
            # Check simulation_instructions
            if "simulation_instructions" in data["simulation_view"]:
                instructions = data["simulation_view"]["simulation_instructions"]
                print(f"📖 simulation_instructions keys: {list(instructions.keys())}")
            else:
                print("❌ Missing simulation_instructions")
        else:
            print("❌ Missing simulation_view")
    
    except Exception as e:
        print(f"❌ Error loading case: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Debug the problematic case
    debug_case("01_06_functional_constipation.json")
