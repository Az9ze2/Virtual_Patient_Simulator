#!/usr/bin/env python3
"""
Quick test to verify model performance tester functionality
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_performance_tester import ModelPerformanceTester

def quick_test():
    """Run a quick test on just the first case"""
    print("🧪 Running quick functionality test...")
    
    tester = ModelPerformanceTester(
        model_choice="gpt-4.1-mini",
        memory_mode="summarize"
    )
    
    # Test just the first case
    try:
        case_data = tester.load_case_file("01_01_breast_feeding_problems.json")
        print(f"✓ Successfully loaded case: {case_data['case_id']}")
        
        # Test basic scenario with only 2 questions to save time
        scenario = tester.test_scenarios["basic_history"]
        quick_scenario = type(scenario)(
            name="Quick Test",
            questions=scenario.questions[:2],  # Just first 2 questions
            expected_topics=scenario.expected_topics[:2],
            description="Quick test with 2 questions"
        )
        
        print("\n🏃‍♂️ Running quick scenario test...")
        metrics, conversation_log = tester.run_scenario_test(case_data, quick_scenario, exam_mode=True)
        
        print(f"\n✅ Quick test completed successfully!")
        print(f"   Success rate: {metrics.successful_responses}/{metrics.total_questions}")
        print(f"   Avg response time: {metrics.avg_response_time:.3f}s")
        print(f"   Total tokens: {metrics.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
