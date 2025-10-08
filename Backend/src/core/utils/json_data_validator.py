#!/usr/bin/env python3
"""
JSON Data Validator for Virtual Patient Simulator
Validates all extracted JSON patient data files for structure and content integrity.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import traceback


class JSONDataValidator:
    """Validates JSON patient data files for structural integrity and required fields."""
    
    def __init__(self, data_directory: str):
        """
        Initialize the validator with the directory containing JSON files.
        
        Args:
            data_directory: Path to the directory containing JSON files to validate
        """
        self.data_directory = Path(data_directory)
        self.validation_results = []
        self.total_files = 0
        self.passed_files = 0
        self.failed_files = 0
        
    def validate_required_structure(self, data: Dict[str, Any], filename: str) -> List[str]:
        """
        Validate that the JSON has the expected structure and required fields.
        
        Args:
            data: Parsed JSON data
            filename: Name of the file being validated
            
        Returns:
            List of validation errors (empty if no errors)
        """
        errors = []
        
        # Top-level required fields
        required_top_level = ["case_id", "case_metadata", "examiner_view", "simulation_view"]
        for field in required_top_level:
            if field not in data:
                errors.append(f"Missing required top-level field: {field}")
        
        # Validate case_metadata structure
        if "case_metadata" in data:
            case_metadata = data["case_metadata"]
            required_metadata = ["case_title", "medical_specialty", "exam_type", "exam_duration_minutes"]
            for field in required_metadata:
                if field not in case_metadata:
                    errors.append(f"Missing required case_metadata field: {field}")
        
        # Validate examiner_view structure
        if "examiner_view" in data:
            examiner_view = data["examiner_view"]
            required_examiner = ["patient_background", "physical_examination"]
            for field in required_examiner:
                if field not in examiner_view:
                    errors.append(f"Missing required examiner_view field: {field}")
            
            # Validate patient_background
            if "patient_background" in examiner_view:
                bg = examiner_view["patient_background"]
                required_bg = ["name", "age", "sex", "chief_complaint"]
                for field in required_bg:
                    if field not in bg:
                        errors.append(f"Missing required patient_background field: {field}")
        
        # Validate simulation_view structure
        if "simulation_view" in data:
            sim_view = data["simulation_view"]
            required_sim = ["simulator_profile", "simulation_instructions"]
            for field in required_sim:
                if field not in sim_view:
                    errors.append(f"Missing required simulation_view field: {field}")
            
            # Validate simulator_profile
            if "simulator_profile" in sim_view:
                profile = sim_view["simulator_profile"]
                required_profile = ["name", "age", "role"]
                for field in required_profile:
                    if field not in profile:
                        errors.append(f"Missing required simulator_profile field: {field}")
            
            # Validate simulation_instructions
            if "simulation_instructions" in sim_view:
                instructions = sim_view["simulation_instructions"]
                required_instructions = ["scenario", "sample_dialogue"]
                for field in required_instructions:
                    if field not in instructions:
                        errors.append(f"Missing required simulation_instructions field: {field}")
        
        return errors
    
    def validate_data_types(self, data: Dict[str, Any], filename: str) -> List[str]:
        """
        Validate data types for critical fields.
        
        Args:
            data: Parsed JSON data
            filename: Name of the file being validated
            
        Returns:
            List of validation errors (empty if no errors)
        """
        errors = []
        
        try:
            # Validate case_id is string
            if "case_id" in data and not isinstance(data["case_id"], str):
                errors.append(f"case_id should be string, got {type(data['case_id'])}")
            
            # Validate exam_duration_minutes is number
            if "case_metadata" in data and "exam_duration_minutes" in data["case_metadata"]:
                duration = data["case_metadata"]["exam_duration_minutes"]
                if not isinstance(duration, (int, float)):
                    errors.append(f"exam_duration_minutes should be number, got {type(duration)}")
            
            # Validate age structure if present
            if ("examiner_view" in data and 
                "patient_background" in data["examiner_view"] and
                "age" in data["examiner_view"]["patient_background"]):
                age = data["examiner_view"]["patient_background"]["age"]
                if isinstance(age, dict):
                    if "value" not in age or "unit" not in age:
                        errors.append("age object missing 'value' or 'unit' field")
                    elif not isinstance(age["value"], (int, float)):
                        errors.append(f"age.value should be number, got {type(age['value'])}")
            
            # Validate sample_dialogue is list
            if ("simulation_view" in data and 
                "simulation_instructions" in data["simulation_view"] and
                "sample_dialogue" in data["simulation_view"]["simulation_instructions"]):
                dialogue = data["simulation_view"]["simulation_instructions"]["sample_dialogue"]
                if not isinstance(dialogue, list):
                    errors.append(f"sample_dialogue should be list, got {type(dialogue)}")
                else:
                    # Validate each dialogue entry
                    for i, entry in enumerate(dialogue):
                        if not isinstance(entry, dict):
                            errors.append(f"sample_dialogue[{i}] should be dict, got {type(entry)}")
                        elif "topic" not in entry or "dialogue" not in entry:
                            errors.append(f"sample_dialogue[{i}] missing 'topic' or 'dialogue' field")
                        elif not isinstance(entry["dialogue"], list):
                            errors.append(f"sample_dialogue[{i}].dialogue should be list")
                        
        except Exception as e:
            errors.append(f"Error during data type validation: {str(e)}")
        
        return errors
    
    def validate_dialogue_structure(self, data: Dict[str, Any], filename: str) -> List[str]:
        """
        Validate the dialogue structure in sample_dialogue.
        
        Args:
            data: Parsed JSON data
            filename: Name of the file being validated
            
        Returns:
            List of validation errors (empty if no errors)
        """
        errors = []
        
        try:
            if ("simulation_view" in data and 
                "simulation_instructions" in data["simulation_view"] and
                "sample_dialogue" in data["simulation_view"]["simulation_instructions"]):
                
                sample_dialogue = data["simulation_view"]["simulation_instructions"]["sample_dialogue"]
                
                for i, topic_entry in enumerate(sample_dialogue):
                    if isinstance(topic_entry, dict) and "dialogue" in topic_entry:
                        dialogues = topic_entry["dialogue"]
                        
                        for j, dialogue_item in enumerate(dialogues):
                            if not isinstance(dialogue_item, dict):
                                errors.append(f"sample_dialogue[{i}].dialogue[{j}] should be dict")
                                continue
                                
                            required_dialogue_fields = ["type", "role", "text"]
                            for field in required_dialogue_fields:
                                if field not in dialogue_item:
                                    errors.append(f"sample_dialogue[{i}].dialogue[{j}] missing field: {field}")
                            
                            # Validate dialogue types and roles
                            if "type" in dialogue_item:
                                valid_types = ["question", "answer"]
                                if dialogue_item["type"] not in valid_types:
                                    errors.append(f"sample_dialogue[{i}].dialogue[{j}].type should be one of {valid_types}")
                            
                            if "role" in dialogue_item:
                                valid_roles = ["examiner", "mother", "patient", "father", "caregiver"]
                                if dialogue_item["role"] not in valid_roles:
                                    errors.append(f"sample_dialogue[{i}].dialogue[{j}].role '{dialogue_item['role']}' not in common roles (warning)")
        
        except Exception as e:
            errors.append(f"Error during dialogue structure validation: {str(e)}")
        
        return errors
    
    def validate_single_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate a single JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing validation results
        """
        result = {
            "filename": file_path.name,
            "full_path": str(file_path),
            "status": "UNKNOWN",
            "errors": [],
            "warnings": [],
            "file_size": 0,
            "validation_time": None
        }
        
        start_time = datetime.now()
        
        try:
            # Check if file exists and get size
            if not file_path.exists():
                result["errors"].append("File does not exist")
                result["status"] = "FAILED"
                return result
            
            result["file_size"] = file_path.stat().st_size
            
            # Try to load and parse JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    result["errors"].append(f"JSON parsing error: {str(e)}")
                    result["status"] = "FAILED"
                    return result
            
            # Validate structure
            structure_errors = self.validate_required_structure(data, file_path.name)
            result["errors"].extend(structure_errors)
            
            # Validate data types
            type_errors = self.validate_data_types(data, file_path.name)
            result["errors"].extend(type_errors)
            
            # Validate dialogue structure
            dialogue_errors = self.validate_dialogue_structure(data, file_path.name)
            result["errors"].extend(dialogue_errors)
            
            # Determine final status
            if len(result["errors"]) == 0:
                result["status"] = "PASSED"
                self.passed_files += 1
            else:
                result["status"] = "FAILED"
                self.failed_files += 1
            
        except Exception as e:
            result["errors"].append(f"Unexpected error: {str(e)}")
            result["status"] = "ERROR"
            self.failed_files += 1
            
        finally:
            end_time = datetime.now()
            result["validation_time"] = (end_time - start_time).total_seconds()
        
        return result
    
    def validate_all_files(self) -> List[Dict[str, Any]]:
        """
        Validate all JSON files in the data directory.
        
        Returns:
            List of validation results for all files
        """
        if not self.data_directory.exists():
            print(f"Error: Directory {self.data_directory} does not exist")
            return []
        
        # Find all JSON files
        json_files = list(self.data_directory.glob("*.json"))
        
        if not json_files:
            print(f"No JSON files found in {self.data_directory}")
            return []
        
        self.total_files = len(json_files)
        print(f"Found {self.total_files} JSON files to validate...")
        print("-" * 80)
        
        # Validate each file
        for i, json_file in enumerate(json_files, 1):
            print(f"[{i:2d}/{self.total_files:2d}] Validating: {json_file.name}")
            
            result = self.validate_single_file(json_file)
            self.validation_results.append(result)
            
            # Print immediate result
            status_symbol = "✓" if result["status"] == "PASSED" else "✗"
            print(f"        {status_symbol} {result['status']} ({result['validation_time']:.3f}s)")
            
            if result["errors"]:
                for error in result["errors"][:3]:  # Show first 3 errors
                    print(f"          - {error}")
                if len(result["errors"]) > 3:
                    print(f"          - ... and {len(result['errors']) - 3} more errors")
        
        return self.validation_results
    
    def generate_summary_report(self) -> str:
        """
        Generate a summary report of the validation results.
        
        Returns:
            String containing the summary report
        """
        if not self.validation_results:
            return "No validation results available."
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("JSON DATA VALIDATION SUMMARY REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Data Directory: {self.data_directory}")
        report_lines.append("")
        
        # Overall statistics
        report_lines.append("OVERALL STATISTICS:")
        report_lines.append(f"  Total Files Processed: {self.total_files}")
        report_lines.append(f"  Files Passed: {self.passed_files}")
        report_lines.append(f"  Files Failed: {self.failed_files}")
        report_lines.append(f"  Success Rate: {(self.passed_files/self.total_files)*100:.1f}%")
        report_lines.append("")
        
        # Failed files details
        if self.failed_files > 0:
            report_lines.append("FAILED FILES:")
            failed_results = [r for r in self.validation_results if r["status"] != "PASSED"]
            
            for result in failed_results:
                report_lines.append(f"  • {result['filename']}")
                report_lines.append(f"    Status: {result['status']}")
                report_lines.append(f"    Errors ({len(result['errors'])}):")
                for error in result["errors"]:
                    report_lines.append(f"      - {error}")
                report_lines.append("")
        
        # File size statistics
        file_sizes = [r["file_size"] for r in self.validation_results]
        if file_sizes:
            avg_size = sum(file_sizes) / len(file_sizes)
            min_size = min(file_sizes)
            max_size = max(file_sizes)
            
            report_lines.append("FILE SIZE STATISTICS:")
            report_lines.append(f"  Average Size: {avg_size/1024:.1f} KB")
            report_lines.append(f"  Smallest File: {min_size/1024:.1f} KB")
            report_lines.append(f"  Largest File: {max_size/1024:.1f} KB")
            report_lines.append("")
        
        # Most common errors
        all_errors = []
        for result in self.validation_results:
            all_errors.extend(result["errors"])
        
        if all_errors:
            from collections import Counter
            error_counts = Counter(all_errors)
            most_common = error_counts.most_common(5)
            
            report_lines.append("MOST COMMON ERRORS:")
            for error, count in most_common:
                report_lines.append(f"  • {error} ({count} occurrences)")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_detailed_report(self, output_file: str = None) -> str:
        """
        Save a detailed validation report to a file.
        
        Args:
            output_file: Path to save the report (optional)
            
        Returns:
            Path to the saved report file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"json_validation_report_{timestamp}.txt"
        
        report_content = self.generate_summary_report()
        
        # Add detailed results
        detailed_lines = []
        detailed_lines.append("\n" + "=" * 80)
        detailed_lines.append("DETAILED VALIDATION RESULTS")
        detailed_lines.append("=" * 80)
        
        for result in self.validation_results:
            detailed_lines.append(f"\nFile: {result['filename']}")
            detailed_lines.append(f"Path: {result['full_path']}")
            detailed_lines.append(f"Status: {result['status']}")
            detailed_lines.append(f"Size: {result['file_size']/1024:.1f} KB")
            detailed_lines.append(f"Validation Time: {result['validation_time']:.3f}s")
            
            if result["errors"]:
                detailed_lines.append(f"Errors ({len(result['errors'])}):")
                for error in result["errors"]:
                    detailed_lines.append(f"  - {error}")
            
            if result["warnings"]:
                detailed_lines.append(f"Warnings ({len(result['warnings'])}):")
                for warning in result["warnings"]:
                    detailed_lines.append(f"  - {warning}")
            
            detailed_lines.append("-" * 40)
        
        full_report = report_content + "\n".join(detailed_lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        return output_file


def main():
    """Main function to run the JSON data validator."""
    
    # Default data directory (can be overridden via command line)
    default_data_dir = r"C:\Users\acer\Desktop\IRPC_Internship\Virtual_Patient_Simulator\Backend\Extracted_Data_json"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
    else:
        data_directory = default_data_dir
    
    print("JSON Data Validator for Virtual Patient Simulator")
    print("=" * 60)
    print(f"Target Directory: {data_directory}")
    print("")
    
    # Initialize validator
    validator = JSONDataValidator(data_directory)
    
    # Run validation
    try:
        results = validator.validate_all_files()
        
        if results:
            print("\n" + "=" * 80)
            print("VALIDATION COMPLETED")
            print("=" * 80)
            
            # Print summary
            summary = validator.generate_summary_report()
            print(summary)
            
            # Save detailed report
            report_file = validator.save_detailed_report()
            print(f"\nDetailed report saved to: {report_file}")
            
            # Return appropriate exit code
            if validator.failed_files == 0:
                print("🎉 All files passed validation!")
                sys.exit(0)
            else:
                print(f"⚠️  {validator.failed_files} file(s) failed validation. Check the report for details.")
                sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error during validation: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
