#!/usr/bin/env python3
"""
Debug script specifically for case 06 - functional_constipation.json
To identify the exact cause of the "'str' object has no attribute 'get'" error
"""

import json
import os
import sys
import traceback
from pathlib import Path

# Import the existing chatbot tester using the same method as performance tester
try:
    import importlib.util
    chatbot_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatbot_test_script_v0.6.py")
    spec = importlib.util.spec_from_file_location("chatbot_module", chatbot_file)
    chatbot_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chatbot_module)
    SimpleChatbotTester = chatbot_module.SimpleChatbotTester
    print("✓ Successfully imported SimpleChatbotTester")
except Exception as e:
    print(f"❌ Could not import SimpleChatbotTester: {e}")
    sys.exit(1)

def debug_case_06():
    """Debug case 06 step by step"""
    
    case_file = "01_06_functional_constipation.json"
    data_dir = Path("C:/Users/acer/Desktop/IRPC_Internship/Virtual_Patient_Simulator/Backend/Extracted_Data_json")
    case_path = data_dir / case_file
    
    print(f"🔍 Debugging: {case_file}")
    print("=" * 60)
    
    # Step 1: Check file existence
    print(f"📁 File path: {case_path}")
    print(f"📄 File exists: {case_path.exists()}")
    
    if not case_path.exists():
        print("❌ File does not exist!")
        return
    
    # Step 2: Load and parse JSON
    try:
        with open(case_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        print("✅ JSON loads successfully")
    except Exception as e:
        print(f"❌ JSON loading error: {e}")
        return
    
    # Step 3: Examine data structure
    print(f"\n📊 Top-level keys: {list(raw_data.keys())}")
    
    # Step 4: Check case_id structure
    case_id = raw_data.get('case_id')
    print(f"🆔 case_id: {repr(case_id)}")
    print(f"🔤 case_id type: {type(case_id)}")
    
    # Step 5: Check simulation_view structure
    if 'simulation_view' in raw_data:
        sim_view = raw_data['simulation_view']
        print(f"🎭 simulation_view type: {type(sim_view)}")
        print(f"🎭 simulation_view keys: {list(sim_view.keys())}")
        
        # Check simulator_profile specifically
        for profile_key in ['simulator_profile', 'mother_profile', 'caregiver_profile', 'patient_profile']:
            if profile_key in sim_view:
                profile = sim_view[profile_key]
                print(f"👤 Found {profile_key}: {type(profile)}")
                if isinstance(profile, dict):
                    print(f"👤 {profile_key} keys: {list(profile.keys())}")
                else:
                    print(f"👤 {profile_key} content: {repr(profile)}")
        
        # Check simulation_instructions
        if 'simulation_instructions' in sim_view:
            instructions = sim_view['simulation_instructions']
            print(f"📖 simulation_instructions type: {type(instructions)}")
            if isinstance(instructions, dict):
                print(f"📖 simulation_instructions keys: {list(instructions.keys())}")
            else:
                print(f"📖 simulation_instructions content: {repr(instructions)}")
    
    # Step 6: Try to recreate the normalization process
    print(f"\n🔄 Testing normalization process:")
    try:
        normalized = normalize_case_data(raw_data)
        print("✅ Normalization successful")
        
        # Check what changed
        changes = []
        if 'simulation_view' in normalized:
            sim_view_norm = normalized['simulation_view']
            if 'simulator_profile' in sim_view_norm and 'simulator_profile' not in raw_data['simulation_view']:
                changes.append("Added simulator_profile")
        
        print(f"🔧 Normalization changes: {changes}")
        
    except Exception as e:
        print(f"❌ Normalization error: {e}")
        traceback.print_exc()
        return
    
    # Step 7: Try to initialize SimpleChatbotTester with this data
    print(f"\n🤖 Testing SimpleChatbotTester initialization:")
    try:
        bot = SimpleChatbotTester(
            memory_mode="summarize", 
            model_choice="gpt-4.1-mini",
            exam_mode=True
        )
        print("✅ SimpleChatbotTester created successfully")
    except Exception as e:
        print(f"❌ SimpleChatbotTester creation error: {e}")
        traceback.print_exc()
        return
    
    # Step 8: Try to setup conversation
    print(f"\n💬 Testing conversation setup:")
    try:
        system_prompt = bot.setup_conversation(normalized)
        print("✅ Conversation setup successful")
        print(f"📝 System prompt length: {len(system_prompt)} characters")
    except Exception as e:
        print(f"❌ Conversation setup error: {e}")
        traceback.print_exc()
        
        # Let's examine what specific part is failing
        print(f"\n🔬 Detailed error analysis:")
        try:
            # Check if it's in the basic access
            mother_profile = normalized['simulation_view']['simulator_profile']
            print(f"👤 simulator_profile access: OK")
            print(f"👤 simulator_profile type: {type(mother_profile)}")
            
            # Check if it's the .get() calls
            if hasattr(mother_profile, 'get'):
                name = mother_profile.get('name')
                print(f"👤 name access: {repr(name)}")
            else:
                print(f"❌ mother_profile does not have .get() method - it's type {type(mother_profile)}")
                print(f"👤 mother_profile content: {repr(mother_profile)}")
                
        except Exception as detail_error:
            print(f"❌ Detailed analysis error: {detail_error}")
            traceback.print_exc()

def normalize_case_data(case_data):
    """Reproduce the normalization logic from performance tester"""
    try:
        normalized = case_data.copy()
        
        # Handle examiner_view -> patient_background field variations
        if "examiner_view" in normalized and "patient_background" in normalized["examiner_view"]:
            bg = normalized["examiner_view"]["patient_background"]
            
            # Ensure bg is a dictionary
            if isinstance(bg, dict):
                # Normalize name field
                if "child_name" in bg and "name" not in bg:
                    bg["name"] = bg["child_name"]
                elif "patient_name" in bg and "name" not in bg:
                    bg["name"] = bg["patient_name"]
                    
                # Normalize age field
                if "child_age" in bg and "age" not in bg:
                    bg["age"] = bg["child_age"]
                elif "patient_age" in bg and "age" not in bg:
                    bg["age"] = bg["patient_age"]
                    
                # Normalize sex field
                if "child_sex" in bg and "sex" not in bg:
                    bg["sex"] = bg["child_sex"]
                elif "patient_sex" in bg and "sex" not in bg:
                    bg["sex"] = bg["patient_sex"]
                elif "gender" in bg and "sex" not in bg:
                    bg["sex"] = bg["gender"]
        
        # Handle simulation_view profile field variations
        if "simulation_view" in normalized and isinstance(normalized["simulation_view"], dict):
            sim_view = normalized["simulation_view"]
            
            # Normalize simulator_profile field
            if "mother_profile" in sim_view and "simulator_profile" not in sim_view:
                sim_view["simulator_profile"] = sim_view["mother_profile"]
            elif "caregiver_profile" in sim_view and "simulator_profile" not in sim_view:
                sim_view["simulator_profile"] = sim_view["caregiver_profile"]
            elif "patient_profile" in sim_view and "simulator_profile" not in sim_view:
                sim_view["simulator_profile"] = sim_view["patient_profile"]
        
        return normalized
        
    except Exception as e:
        print(f"❌ Normalization error: {e}")
        return case_data  # Return original data if normalization fails

if __name__ == "__main__":
    debug_case_06()
