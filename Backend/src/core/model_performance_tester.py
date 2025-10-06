#!/usr/bin/env python3
"""
Model Performance Tester for Virtual Patient Simulator
Tests chatbot performance on cases 01_01 through 01_05 with comprehensive evaluation metrics.
"""

import json
import os
import sys
import time
import statistics
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import argparse

# Import the existing chatbot tester using importlib due to dots in filename
try:
    import importlib.util
    chatbot_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatbot_test_script.py")
    spec = importlib.util.spec_from_file_location("chatbot_module", chatbot_file)
    chatbot_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chatbot_module)
    SimpleChatbotTester = chatbot_module.SimpleChatbotTester
    print("✓ Successfully imported SimpleChatbotTester")
except Exception as e:
    print(f"❌ Could not import SimpleChatbotTester: {e}")
    print("Please ensure chatbot_test_script.py is in the same directory.")
    sys.exit(1)


@dataclass
class TestScenario:
    """Test scenario with predefined questions"""
    name: str
    questions: List[str]
    expected_topics: List[str]
    description: str


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single test"""
    case_id: str
    case_title: str
    total_questions: int
    total_response_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    total_tokens: int
    input_tokens: int
    output_tokens: int
    fallback_questions_addressed: int
    fallback_questions_total: int
    successful_responses: int
    error_count: int
    conversation_length: int
    test_scenario: str


class ModelPerformanceTester:
    """Comprehensive performance tester for the virtual patient simulator"""
    
    def __init__(self, model_choice: str = "gpt-4.1-mini", memory_mode: str = "summarize"):
        """
        Initialize the performance tester.
        
        Args:
            model_choice: Model to test ("gpt-4.1-mini" or "gpt-5")
            memory_mode: Memory management mode ("none", "truncate", "summarize")
        """
        self.model_choice = model_choice
        self.memory_mode = memory_mode
        self.test_results = []
        self.data_directory = Path("C:/Users/acer/Desktop/IRPC_Internship/Virtual_Patient_Simulator/Backend/Extracted_Data_json")
        
        # Get all JSON files in the extracted data folder
        self.test_cases = self.discover_test_cases()
        
        # Define standardized test scenarios
        self.test_scenarios = {
            "basic_history": TestScenario(
                name="Basic History Taking",
                questions=[
                    "สวัสดีครับ วันนี้มีเรื่องอะไรให้ช่วยครับ",
                    "น้องชื่ออะไรครับ อายุเท่าไหร่",
                    "อาการเป็นมาตั้งแต่เมื่อไหร่ครับ",
                    "มีอาการอื่นร่วมด้วยไหมครับ",
                    "เคยไปหาหมอมาก่อนไหมครับ"
                ],
                expected_topics=["chief_complaint", "patient_info", "symptom_onset", "associated_symptoms", "medical_history"],
                description="Basic medical history taking questions"
            ),
            "detailed_inquiry": TestScenario(
                name="Detailed Medical Inquiry", 
                questions=[
                    "สวัสดีครับ วันนี้พาน้องมาด้วยอาการอะไรครับ",
                    "อาการนี้เริ่มเมื่อไหร่ครับ",
                    "ปกติน้องกินข้าวเป็นอย่างไรครับ",
                    "น้องนอนหลับเป็นอย่างไรครับ",
                    "มีไข้หรือเปล่าครับ",
                    "ถ่ายอุจจาระเป็นอย่างไรครับ",
                    "มีคำถามอะไรเพิ่มเติมไหมครับ"
                ],
                expected_topics=["chief_complaint", "symptom_timeline", "feeding", "sleep", "fever", "bowel_habits", "questions"],
                description="Detailed medical inquiry with specific questions"
            ),
            "comprehensive_assessment": TestScenario(
                name="Comprehensive Assessment",
                questions=[
                    "สวัสดีครับ",
                    "วันนี้มาด้วยเรื่องอะไรครับ",
                    "เล่าให้ฟังหน่อยครับว่าเป็นอย่างไร",
                    "อาการนี้เริ่มเมื่อไหร่ครับ",
                    "มีอะไรทำให้ดีขึ้นหรือแย่ลงไหมครับ",
                    "ครอบครวมีใครเป็นโรคนี้บ้างไหมครับ",
                    "ตอนนี้กินยาอะไรอยู่บ้างครับ",
                    "มีอาการข้างเคียงจากยาไหมครับ",
                    "มีคำถามอะไรอยากถามหมอไหมครับ",
                    "ขอบคุณครับ"
                ],
                expected_topics=["chief_complaint", "symptom_details", "timeline", "aggravating_factors", "family_history", "medications", "side_effects", "patient_questions"],
                description="Comprehensive medical assessment with follow-up questions"
            )
        }
    
    def discover_test_cases(self) -> List[str]:
        """Discover all JSON files in the extracted data directory"""
        try:
            json_files = list(self.data_directory.glob("*.json"))
            case_files = [f.name for f in json_files if f.is_file()]
            case_files.sort()  # Sort for consistent ordering
            print(f"📂 Discovered {len(case_files)} JSON files in extracted data folder")
            return case_files
        except Exception as e:
            print(f"❌ Error discovering test cases: {e}")
            return []
    
    def normalize_case_data(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize case data to handle field naming variations"""
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
                
                # Fix fallback_question field if it's incorrectly formatted
                if "simulation_instructions" in sim_view and isinstance(sim_view["simulation_instructions"], dict):
                    instructions = sim_view["simulation_instructions"]
                    if "fallback_question" in instructions:
                        fallback = instructions["fallback_question"]
                        # If fallback_question is a string like "none", convert to None
                        if isinstance(fallback, str) and fallback.lower() in ["none", "null", ""]:
                            instructions["fallback_question"] = None
                            print(f"               🔧 Normalized fallback_question from '{fallback}' to None")
                
                return normalized
            
        except Exception as e:
            print(f"               ⚠️ Normalization error: {e}")
            return case_data  # Return original data if normalization fails
    
    def validate_essential_fields(self, case_data: Dict[str, Any], case_filename: str) -> bool:
        """Validate that case data has essential fields for testing"""
        try:
            # Check for essential top-level structure
            if "case_metadata" not in case_data:
                print(f"               ⚠️ Missing case_metadata in {case_filename}")
                return False
                
            if "simulation_view" not in case_data:
                print(f"               ⚠️ Missing simulation_view in {case_filename}")
                return False
                
            if "simulation_instructions" not in case_data["simulation_view"]:
                print(f"               ⚠️ Missing simulation_instructions in {case_filename}")
                return False
                
            if "simulator_profile" not in case_data["simulation_view"]:
                print(f"               ⚠️ Missing simulator_profile in {case_filename}")
                return False
                
            return True
            
        except Exception as e:
            print(f"               ⚠️ Validation error for {case_filename}: {e}")
            return False
    
    def load_case_file(self, case_filename: str) -> Dict[str, Any]:
        """Load a specific case file and normalize field variations"""
        case_path = self.data_directory / case_filename
        if not case_path.exists():
            raise FileNotFoundError(f"Case file not found: {case_path}")
        
        with open(case_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Normalize field naming variations
        normalized_data = self.normalize_case_data(raw_data)
        return normalized_data
    
    def run_scenario_test(self, case_data: Dict[str, Any], scenario: TestScenario, exam_mode: bool = True) -> PerformanceMetrics:
        """
        Run a test scenario on a specific case.
        
        Args:
            case_data: Loaded case data
            scenario: Test scenario to run
            exam_mode: Whether to use exam mode (fixed seed for reproducibility)
            
        Returns:
            PerformanceMetrics object with test results
        """
        print(f"\n🧪 Testing case: {case_data['case_id']}")
        print(f"📋 Scenario: {scenario.name}")
        print(f"📝 {scenario.description}")
        
        # Initialize chatbot with exam mode for consistent testing
        bot = SimpleChatbotTester(
            memory_mode=self.memory_mode, 
            model_choice=self.model_choice,
            exam_mode=exam_mode
        )
        
        # Setup conversation
        bot.load_case_data = lambda x: case_data  # Mock the load function
        system_prompt = bot.setup_conversation(case_data)
        
        # Track metrics
        response_times = []
        successful_responses = 0
        error_count = 0
        conversation_log = []
        
        print("\n💬 Starting conversation:")
        print("-" * 50)
        
        # Run through the scenario questions
        for i, question in enumerate(scenario.questions, 1):
            print(f"\n[{i:2d}/{len(scenario.questions):2d}] 🧑‍⚕️ {question}")
            
            try:
                response, response_time = bot.chat_turn(question)
                response_times.append(response_time)
                successful_responses += 1
                
                print(f"            👩‍⚕️ {response}")
                print(f"            ⏱️  {response_time:.3f}s")
                
                conversation_log.append({
                    "question": question,
                    "response": response,
                    "response_time": response_time,
                    "success": True
                })
                
            except Exception as e:
                error_count += 1
                print(f"            ❌ Error: {str(e)}")
                
                conversation_log.append({
                    "question": question,
                    "response": f"ERROR: {str(e)}",
                    "response_time": 0.0,
                    "success": False
                })
        
        print("-" * 50)
        
        # Count addressed fallback questions
        fallback_questions_addressed = sum(1 for q in bot.questions_to_ask if q.get('asked', False))
        fallback_questions_total = len(bot.questions_to_ask)
        
        # Create performance metrics
        metrics = PerformanceMetrics(
            case_id=case_data['case_id'],
            case_title=case_data['case_metadata']['case_title'],
            total_questions=len(scenario.questions),
            total_response_time=sum(response_times) if response_times else 0.0,
            avg_response_time=statistics.mean(response_times) if response_times else 0.0,
            min_response_time=min(response_times) if response_times else 0.0,
            max_response_time=max(response_times) if response_times else 0.0,
            total_tokens=bot.total_tokens,
            input_tokens=bot.input_tokens,
            output_tokens=bot.output_tokens,
            fallback_questions_addressed=fallback_questions_addressed,
            fallback_questions_total=fallback_questions_total,
            successful_responses=successful_responses,
            error_count=error_count,
            conversation_length=len(conversation_log),
            test_scenario=scenario.name
        )
        
        # Show immediate summary
        print(f"\n📊 Test Summary:")
        print(f"   ✅ Successful responses: {successful_responses}/{len(scenario.questions)}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Avg response time: {metrics.avg_response_time:.3f}s")
        print(f"   🎯 Fallback questions addressed: {fallback_questions_addressed}/{fallback_questions_total}")
        print(f"   📄 Total tokens used: {bot.total_tokens}")
        
        return metrics, conversation_log
    
    def run_comprehensive_test(self, exam_mode: bool = True) -> List[Tuple[PerformanceMetrics, List[Dict]]]:
        """
        Run comprehensive testing on all cases with all scenarios.
        
        Args:
            exam_mode: Whether to use exam mode for consistency
            
        Returns:
            List of (PerformanceMetrics, conversation_log) tuples
        """
        print(f"🚀 Starting comprehensive performance test")
        print(f"🤖 Model: {self.model_choice}")
        print(f"🧠 Memory mode: {self.memory_mode}")
        print(f"📋 Mode: {'Exam (deterministic)' if exam_mode else 'Practice (variable)'}")
        print(f"📁 Test cases: {', '.join(self.test_cases)}")
        print("=" * 80)
        
        all_results = []
        
        for i, case_file in enumerate(self.test_cases, 1):
            try:
                print(f"\n[{i:2d}/{len(self.test_cases):2d}] 📄 Processing: {case_file}")
                
                # Load case data
                case_data = self.load_case_file(case_file)
                
                # Validate essential fields
                if not self.validate_essential_fields(case_data, case_file):
                    continue
                
                case_title = case_data.get('case_metadata', {}).get('case_title', 'No title available')
                print(f"               📋 Title: {case_title[:80]}{'...' if len(case_title) > 80 else ''}")
                
                # Test with the basic history scenario
                scenario = self.test_scenarios["basic_history"]
                metrics, conversation_log = self.run_scenario_test(case_data, scenario, exam_mode)
                
                all_results.append((metrics, conversation_log))
                
            except Exception as e:
                print(f"               ❌ Failed to test {case_file}: {str(e)}")
                # Create a failed metrics entry for reporting
                failed_metrics = PerformanceMetrics(
                    case_id=case_file,
                    case_title=f"FAILED: {case_file}",
                    total_questions=0,
                    total_response_time=0.0,
                    avg_response_time=0.0,
                    min_response_time=0.0,
                    max_response_time=0.0,
                    total_tokens=0,
                    input_tokens=0,
                    output_tokens=0,
                    fallback_questions_addressed=0,
                    fallback_questions_total=0,
                    successful_responses=0,
                    error_count=1,
                    conversation_length=0,
                    test_scenario="Failed to load"
                )
                all_results.append((failed_metrics, [{"error": str(e)}]))
                continue
        
        return all_results
    
    def generate_performance_report(self, results: List[Tuple[PerformanceMetrics, List[Dict]]]) -> str:
        """Generate a comprehensive performance report"""
        if not results:
            return "No test results available."
        
        metrics_list = [result[0] for result in results]
        
        # Calculate aggregate statistics
        total_questions = sum(m.total_questions for m in metrics_list)
        total_successful = sum(m.successful_responses for m in metrics_list)
        total_errors = sum(m.error_count for m in metrics_list)
        total_tokens = sum(m.total_tokens for m in metrics_list)
        
        avg_response_times = [m.avg_response_time for m in metrics_list if m.avg_response_time > 0]
        overall_avg_response_time = statistics.mean(avg_response_times) if avg_response_times else 0.0
        
        total_fallback_addressed = sum(m.fallback_questions_addressed for m in metrics_list)
        total_fallback_available = sum(m.fallback_questions_total for m in metrics_list)
        
        # Generate report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("MODEL PERFORMANCE TEST REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Model: {self.model_choice}")
        report_lines.append(f"Memory Mode: {self.memory_mode}")
        report_lines.append(f"Test Cases: {len(metrics_list)}")
        report_lines.append("")
        
        # Overall Statistics
        report_lines.append("OVERALL PERFORMANCE:")
        report_lines.append(f"  Total Questions Asked: {total_questions}")
        report_lines.append(f"  Successful Responses: {total_successful} ({(total_successful/total_questions)*100:.1f}%)")
        report_lines.append(f"  Errors: {total_errors} ({(total_errors/total_questions)*100:.1f}%)")
        report_lines.append(f"  Average Response Time: {overall_avg_response_time:.3f}s")
        report_lines.append(f"  Total Tokens Used: {total_tokens:,}")
        report_lines.append(f"  Fallback Questions Addressed: {total_fallback_addressed}/{total_fallback_available} ({(total_fallback_addressed/max(total_fallback_available,1))*100:.1f}%)")
        report_lines.append("")
        
        # Per-case breakdown
        report_lines.append("PER-CASE BREAKDOWN:")
        for i, metrics in enumerate(metrics_list, 1):
            success_rate = (metrics.successful_responses / metrics.total_questions) * 100
            fallback_rate = (metrics.fallback_questions_addressed / max(metrics.fallback_questions_total, 1)) * 100
            
            report_lines.append(f"  {i}. {metrics.case_id}")
            report_lines.append(f"     Title: {metrics.case_title[:60]}...")
            report_lines.append(f"     Success Rate: {success_rate:.1f}% ({metrics.successful_responses}/{metrics.total_questions})")
            report_lines.append(f"     Avg Response Time: {metrics.avg_response_time:.3f}s")
            report_lines.append(f"     Tokens Used: {metrics.total_tokens}")
            report_lines.append(f"     Fallback Coverage: {fallback_rate:.1f}% ({metrics.fallback_questions_addressed}/{metrics.fallback_questions_total})")
            report_lines.append("")
        
        # Performance insights
        report_lines.append("PERFORMANCE INSIGHTS:")
        
        # Response time analysis
        fastest_case = min(metrics_list, key=lambda m: m.avg_response_time)
        slowest_case = max(metrics_list, key=lambda m: m.avg_response_time)
        
        report_lines.append(f"  Fastest Response: {fastest_case.case_id} ({fastest_case.avg_response_time:.3f}s)")
        report_lines.append(f"  Slowest Response: {slowest_case.case_id} ({slowest_case.avg_response_time:.3f}s)")
        
        # Token efficiency (avoid division by zero)
        valid_metrics = [m for m in metrics_list if m.total_questions > 0]
        if valid_metrics:
            most_efficient = min(valid_metrics, key=lambda m: m.total_tokens / m.total_questions)
            least_efficient = max(valid_metrics, key=lambda m: m.total_tokens / m.total_questions)
        else:
            most_efficient = least_efficient = None
        
        if most_efficient and least_efficient:
            report_lines.append(f"  Most Token Efficient: {most_efficient.case_id} ({most_efficient.total_tokens/most_efficient.total_questions:.1f} tokens/question)")
            report_lines.append(f"  Least Token Efficient: {least_efficient.case_id} ({least_efficient.total_tokens/least_efficient.total_questions:.1f} tokens/question)")
        else:
            report_lines.append("  Token Efficiency: No valid data")
        
        # Best fallback coverage (only if there are cases with fallback questions)
        cases_with_fallback = [m for m in metrics_list if m.fallback_questions_total > 0]
        if cases_with_fallback:
            best_fallback = max(cases_with_fallback, key=lambda m: m.fallback_questions_addressed / m.fallback_questions_total)
            coverage = (best_fallback.fallback_questions_addressed / best_fallback.fallback_questions_total) * 100
            report_lines.append(f"  Best Fallback Coverage: {best_fallback.case_id} ({coverage:.1f}%)")
        else:
            report_lines.append("  Best Fallback Coverage: No cases with fallback questions")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_detailed_results(self, results: List[Tuple[PerformanceMetrics, List[Dict]]], output_file: str = None) -> str:
        """Save detailed test results to JSON file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"model_performance_results_{self.model_choice}_{timestamp}.json"
        
        detailed_results = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "model": self.model_choice,
                "memory_mode": self.memory_mode,
                "total_cases": len(results)
            },
            "results": []
        }
        
        for metrics, conversation_log in results:
            case_result = {
                "case_id": metrics.case_id,
                "case_title": metrics.case_title,
                "metrics": {
                    "total_questions": metrics.total_questions,
                    "successful_responses": metrics.successful_responses,
                    "error_count": metrics.error_count,
                    "total_response_time": metrics.total_response_time,
                    "avg_response_time": metrics.avg_response_time,
                    "min_response_time": metrics.min_response_time,
                    "max_response_time": metrics.max_response_time,
                    "total_tokens": metrics.total_tokens,
                    "input_tokens": metrics.input_tokens,
                    "output_tokens": metrics.output_tokens,
                    "fallback_questions_addressed": metrics.fallback_questions_addressed,
                    "fallback_questions_total": metrics.fallback_questions_total,
                    "test_scenario": metrics.test_scenario
                },
                "conversation_log": conversation_log
            }
            detailed_results["results"].append(case_result)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, ensure_ascii=False, indent=2)
        
        return output_file


def main():
    """Main function to run the performance test"""
    parser = argparse.ArgumentParser(description="Model Performance Tester for Virtual Patient Simulator")
    parser.add_argument("--model", choices=["gpt-4.1-mini", "gpt-5"], default="gpt-4.1-mini",
                        help="Choose which model to test")
    parser.add_argument("--memory", choices=["none", "truncate", "summarize"], default="summarize",
                        help="Choose memory management strategy")
    parser.add_argument("--mode", choices=["exam", "practice"], default="exam",
                        help="Choose exam (deterministic) or practice (variable) mode")
    parser.add_argument("--output", type=str, help="Output file prefix for results")
    
    args = parser.parse_args()
    
    exam_mode = (args.mode == "exam")
    
    print("🧪 Model Performance Tester for Virtual Patient Simulator")
    print("=" * 70)
    
    # Initialize tester
    tester = ModelPerformanceTester(
        model_choice=args.model,
        memory_mode=args.memory
    )
    
    # Run comprehensive test
    try:
        results = tester.run_comprehensive_test(exam_mode=exam_mode)
        
        if results:
            print("\n" + "=" * 80)
            print("TESTING COMPLETED")
            print("=" * 80)
            
            # Generate and display report
            report = tester.generate_performance_report(results)
            print(report)
            
            # Save detailed results
            if args.output:
                json_file = f"{args.output}_{args.model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                report_file = f"{args.output}_{args.model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            else:
                json_file = None
                report_file = f"performance_report_{args.model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            json_output = tester.save_detailed_results(results, json_file)
            
            # Save text report
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"\n📄 Detailed results saved to: {json_output}")
            print(f"📄 Text report saved to: {report_file}")
            
            # Final summary
            metrics_list = [r[0] for r in results]
            total_success = sum(m.successful_responses for m in metrics_list)
            total_questions = sum(m.total_questions for m in metrics_list)
            success_rate = (total_success / total_questions) * 100 if total_questions > 0 else 0
            
            if success_rate >= 95:
                print(f"🎉 Excellent performance: {success_rate:.1f}% success rate!")
            elif success_rate >= 85:
                print(f"✅ Good performance: {success_rate:.1f}% success rate")
            elif success_rate >= 70:
                print(f"⚠️  Fair performance: {success_rate:.1f}% success rate - room for improvement")
            else:
                print(f"❌ Poor performance: {success_rate:.1f}% success rate - needs investigation")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Testing interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
