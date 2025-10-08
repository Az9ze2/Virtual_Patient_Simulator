#!/usr/bin/env python3
"""
Comprehensive Performance Test Suite for Unified Chatbot
Tests all 01 and 02 cases with standardized inputs to verify correct responses
"""

import sys
import os
import json
import time
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import traceback

# Add core to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from chatbot.unified_chatbot import UnifiedChatbotTester
from config.prompt_config import PromptConfig


class PerformanceTestSuite:
    """Comprehensive test suite for chatbot performance across all cases"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Test configurations
        self.models_to_test = ["gpt-4.1-mini"]  # Add "gpt-5" if needed
        self.memory_modes = ["summarize"]  # Can add ["none", "truncate"] for comprehensive testing
        
        # Standardized test inputs for both case types
        self.test_inputs_01 = [
            "สวัสดีครับ",
            "วันนี้มีอาการอะไรหรือเปล่าครับ",
            "อาการเป็นมานานแค่ไหนแล้วครับ",
            "มีอาการอื่นๆ ร่วมด้วยไหมครับ",
            "เคยไปหาหมอมาก่อนไหมครับ", 
            "มีคำถามอะไรเพิ่มเติมไหมครับ",
            "ขอบคุณครับ"
        ]
        
        self.test_inputs_02 = [
            "สวัสดีครับ", 
            "วันนี้มีอาการอะไรครับ",
            "อาการเริ่มเมื่อไหร่ครับ",
            "มีอาการอื่นๆ ด้วยไหมครับ",
            "เคยรักษามาก่อนไหมครับ",
            "มีอะไรอยากถามเพิ่มเติมไหมครับ", 
            "ขอบคุณครับ"
        ]
        
        # Expected response patterns for validation
        self.validation_patterns_01 = {
            "case_type_indicators": ["ค่ะ", "ลูก", "เด็ก", "น้อง"],
            "forbidden_patterns": ["ครับ", "ผม", "กระผม"],
            "medical_advice_forbidden": ["ควรทำ", "แนะนำให้", "ต้องรักษา"]
        }
        
        self.validation_patterns_02 = {
            "case_type_indicators": ["ครับ", "ค่ะ"],
            "forbidden_patterns": [],
            "medical_advice_forbidden": ["ควรทำ", "แนะนำให้", "ต้องรักษา"]
        }
        
        # Results storage
        self.test_results = []
        
    def discover_case_files(self) -> Tuple[List[Path], List[Path]]:
        """Discover all 01 and 02 case files"""
        
        # Try new structure first
        cases_01_dir = Path("data/cases_01")
        cases_02_dir = Path("data/cases_02")
        
        # Find case files
        cases_01 = []
        cases_02 = []
        
        if cases_01_dir.exists():
            cases_01 = list(cases_01_dir.glob("01_*.json"))
            
        if cases_02_dir.exists():
            cases_02 = list(cases_02_dir.glob("02_*.json"))
            
        return sorted(cases_01), sorted(cases_02)
    
    def validate_response(self, response: str, case_type: str, input_text: str) -> Dict[str, Any]:
        """Validate chatbot response against expected patterns"""
        
        validation_result = {
            "is_valid": True,
            "issues": [],
            "case_type_match": False,
            "no_medical_advice": True,
            "appropriate_language": True
        }
        
        patterns = self.validation_patterns_01 if case_type == "01" else self.validation_patterns_02
        
        # Check case type indicators
        case_indicators_found = any(indicator in response for indicator in patterns["case_type_indicators"])
        validation_result["case_type_match"] = case_indicators_found
        
        if not case_indicators_found:
            validation_result["issues"].append(f"No appropriate case type indicators found for type {case_type}")
            validation_result["is_valid"] = False
            
        # Check forbidden patterns
        forbidden_found = [pattern for pattern in patterns["forbidden_patterns"] if pattern in response]
        if forbidden_found:
            validation_result["issues"].append(f"Forbidden patterns found: {forbidden_found}")
            validation_result["is_valid"] = False
            validation_result["appropriate_language"] = False
            
        # Check for medical advice (forbidden)
        medical_advice_found = [pattern for pattern in patterns["medical_advice_forbidden"] if pattern in response]
        if medical_advice_found:
            validation_result["issues"].append(f"Medical advice given: {medical_advice_found}")
            validation_result["is_valid"] = False
            validation_result["no_medical_advice"] = False
            
        # Check response length (should be 2-3 sentences as per prompt)
        sentence_count = len([s for s in response.split('.') if s.strip()])
        if sentence_count > 4:
            validation_result["issues"].append(f"Response too long: {sentence_count} sentences")
            
        # Check for Thai language
        if not any('\u0e00' <= char <= '\u0e7f' for char in response):
            validation_result["issues"].append("Response not in Thai")
            validation_result["appropriate_language"] = False
            validation_result["is_valid"] = False
            
        return validation_result
    
    def test_single_case(self, case_file: Path, model: str, memory_mode: str) -> Dict[str, Any]:
        """Test a single case file with standardized inputs"""
        
        print(f"  Testing: {case_file.name}")
        
        test_result = {
            "case_file": str(case_file),
            "case_name": case_file.name,
            "model": model,
            "memory_mode": memory_mode,
            "timestamp": datetime.now().isoformat(),
            "case_type": PromptConfig.get_case_type_from_filename(case_file.name),
            "total_time": 0.0,
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "conversation": [],
            "validation_summary": {
                "total_responses": 0,
                "valid_responses": 0,
                "validation_rate": 0.0
            },
            "errors": [],
            "status": "unknown"
        }
        
        try:
            # Initialize chatbot
            chatbot = UnifiedChatbotTester(
                memory_mode=memory_mode,
                model_choice=model,
                exam_mode=True  # Use fixed seed for consistency
            )
            
            # Load case data
            case_data = chatbot.load_case_data(str(case_file))
            chatbot.setup_conversation(case_data)
            
            # Select appropriate test inputs
            test_inputs = self.test_inputs_01 if test_result["case_type"] == "01" else self.test_inputs_02
            
            start_time = time.time()
            
            # Run conversation
            for i, input_text in enumerate(test_inputs):
                try:
                    response, response_time = chatbot.chat_turn(input_text)
                    
                    # Validate response
                    validation = self.validate_response(response, test_result["case_type"], input_text)
                    
                    conversation_turn = {
                        "turn": i + 1,
                        "input": input_text,
                        "response": response,
                        "response_time": response_time,
                        "validation": validation
                    }
                    
                    test_result["conversation"].append(conversation_turn)
                    test_result["validation_summary"]["total_responses"] += 1
                    
                    if validation["is_valid"]:
                        test_result["validation_summary"]["valid_responses"] += 1
                        
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    error_msg = f"Error in turn {i+1}: {str(e)}"
                    test_result["errors"].append(error_msg)
                    print(f"    ❌ {error_msg}")
            
            # Calculate final metrics
            test_result["total_time"] = time.time() - start_time
            test_result["total_tokens"] = chatbot.total_tokens
            test_result["input_tokens"] = chatbot.input_tokens  
            test_result["output_tokens"] = chatbot.output_tokens
            
            if test_result["validation_summary"]["total_responses"] > 0:
                test_result["validation_summary"]["validation_rate"] = (
                    test_result["validation_summary"]["valid_responses"] / 
                    test_result["validation_summary"]["total_responses"]
                )
            
            test_result["status"] = "completed"
            
            print(f"    ✅ Completed - Validation Rate: {test_result['validation_summary']['validation_rate']:.1%}")
            
        except Exception as e:
            error_msg = f"Fatal error testing {case_file.name}: {str(e)}"
            test_result["errors"].append(error_msg)
            test_result["status"] = "failed"
            print(f"    ❌ Failed: {error_msg}")
            
        return test_result
    
    def run_comprehensive_test(self) -> str:
        """Run comprehensive test across all cases"""
        
        print("🚀 Starting Comprehensive Performance Test Suite")
        print("=" * 60)
        
        # Discover case files
        cases_01, cases_02 = self.discover_case_files()
        
        print(f"📋 Found {len(cases_01)} case files (01_*) and {len(cases_02)} case files (02_*)")
        
        all_cases = [("01", cases_01), ("02", cases_02)]
        
        # Run tests for each configuration
        for model in self.models_to_test:
            for memory_mode in self.memory_modes:
                
                print(f"\n🧪 Testing Configuration: {model} with {memory_mode} memory")
                print("-" * 50)
                
                for case_type, case_files in all_cases:
                    if not case_files:
                        print(f"  ⚠️ No {case_type} cases found, skipping...")
                        continue
                        
                    print(f"\n  📂 Testing {case_type} cases ({len(case_files)} files):")
                    
                    for case_file in case_files:
                        result = self.test_single_case(case_file, model, memory_mode)
                        self.test_results.append(result)
        
        # Generate comprehensive report
        report_file = self.generate_report()
        
        print(f"\n✅ Comprehensive testing completed!")
        print(f"📊 Report saved to: {report_file}")
        
        return report_file
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"performance_test_report_{timestamp}.json"
        csv_file = self.output_dir / f"performance_test_summary_{timestamp}.csv"
        
        # Create summary statistics
        summary = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_cases_tested": len(self.test_results),
                "models_tested": self.models_to_test,
                "memory_modes_tested": self.memory_modes
            },
            "overall_statistics": self._calculate_overall_stats(),
            "case_type_breakdown": self._calculate_case_type_stats(),
            "detailed_results": self.test_results
        }
        
        # Save JSON report
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Save CSV summary
        self._save_csv_summary(csv_file)
        
        # Print summary to console
        self._print_summary(summary)
        
        return str(report_file)
    
    def _calculate_overall_stats(self) -> Dict[str, Any]:
        """Calculate overall statistics"""
        
        if not self.test_results:
            return {}
            
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["status"] == "completed"])
        total_responses = sum(r["validation_summary"]["total_responses"] for r in self.test_results)
        valid_responses = sum(r["validation_summary"]["valid_responses"] for r in self.test_results)
        total_tokens = sum(r["total_tokens"] for r in self.test_results)
        total_time = sum(r["total_time"] for r in self.test_results)
        
        return {
            "total_cases_tested": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "total_responses": total_responses,
            "valid_responses": valid_responses,
            "overall_validation_rate": valid_responses / total_responses if total_responses > 0 else 0,
            "total_tokens_used": total_tokens,
            "total_test_time_seconds": total_time,
            "average_time_per_case": total_time / total_tests if total_tests > 0 else 0,
            "average_tokens_per_case": total_tokens / total_tests if total_tests > 0 else 0
        }
    
    def _calculate_case_type_stats(self) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics by case type"""
        
        stats = {}
        
        for case_type in ["01", "02"]:
            type_results = [r for r in self.test_results if r["case_type"] == case_type]
            
            if not type_results:
                continue
                
            total_responses = sum(r["validation_summary"]["total_responses"] for r in type_results)
            valid_responses = sum(r["validation_summary"]["valid_responses"] for r in type_results)
            
            stats[case_type] = {
                "total_cases": len(type_results),
                "successful_cases": len([r for r in type_results if r["status"] == "completed"]),
                "total_responses": total_responses,
                "valid_responses": valid_responses,
                "validation_rate": valid_responses / total_responses if total_responses > 0 else 0,
                "average_tokens": sum(r["total_tokens"] for r in type_results) / len(type_results),
                "average_time": sum(r["total_time"] for r in type_results) / len(type_results)
            }
            
        return stats
    
    def _save_csv_summary(self, csv_file: Path):
        """Save summary as CSV"""
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Case File", "Case Type", "Status", "Model", "Memory Mode",
                "Total Tokens", "Test Time (s)", "Total Responses", "Valid Responses",
                "Validation Rate", "Errors"
            ])
            
            # Data rows
            for result in self.test_results:
                writer.writerow([
                    result["case_name"],
                    result["case_type"], 
                    result["status"],
                    result["model"],
                    result["memory_mode"],
                    result["total_tokens"],
                    f"{result['total_time']:.2f}",
                    result["validation_summary"]["total_responses"],
                    result["validation_summary"]["valid_responses"], 
                    f"{result['validation_summary']['validation_rate']:.1%}",
                    "; ".join(result["errors"])
                ])
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print summary to console"""
        
        overall = summary["overall_statistics"]
        breakdown = summary["case_type_breakdown"]
        
        print(f"\n📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Cases Tested: {overall['total_cases_tested']}")
        print(f"Success Rate: {overall['success_rate']:.1%}")
        print(f"Overall Validation Rate: {overall['overall_validation_rate']:.1%}")
        print(f"Total Tokens Used: {overall['total_tokens_used']:,}")
        print(f"Total Test Time: {overall['total_test_time_seconds']:.1f}s")
        
        print(f"\n📋 BREAKDOWN BY CASE TYPE")
        print("-" * 30)
        
        for case_type, stats in breakdown.items():
            case_name = "Mother/Guardian" if case_type == "01" else "Patient"
            print(f"\n{case_type} Cases ({case_name}):")
            print(f"  Cases Tested: {stats['total_cases']}")
            print(f"  Success Rate: {stats['successful_cases']}/{stats['total_cases']}")
            print(f"  Validation Rate: {stats['validation_rate']:.1%}")
            print(f"  Avg Tokens/Case: {stats['average_tokens']:.0f}")
            print(f"  Avg Time/Case: {stats['average_time']:.1f}s")

def main():
    """Main test execution"""
    
    print("🎯 Medical OSCE Chatbot Performance Test Suite")
    print("=" * 60)
    print("\nThis test will:")
    print("📋 Discover all 01_*.json and 02_*.json case files")
    print("🧪 Test each case with standardized medical consultation inputs")
    print("✅ Validate responses for appropriate language and behavior")
    print("📊 Generate comprehensive performance reports")
    print("\n⚠️  Note: This test requires OpenAI API access and will use tokens.")
    
    response = input("\nProceed with testing? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Testing cancelled.")
        return
    
    # Create performance test suite
    test_suite = PerformanceTestSuite()
    
    # Run comprehensive tests
    report_file = test_suite.run_comprehensive_test()
    
    print(f"\n🎉 All tests completed!")
    print(f"📄 Detailed report: {report_file}")
    print(f"📊 CSV summary: {report_file.replace('.json', '.csv').replace('report', 'summary')}")
    print("\n💡 Use the CSV file to analyze performance in Excel/Google Sheets")

if __name__ == "__main__":
    main()
