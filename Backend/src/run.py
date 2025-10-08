#!/usr/bin/env python3
"""
Launcher script for Virtual Patient Simulator
Convenient way to run tests and chatbot
"""

import sys
import os
import argparse

# Add core directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

def main():
    parser = argparse.ArgumentParser(description="Virtual Patient Simulator Launcher")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Chatbot command
    chatbot_parser = subparsers.add_parser('chatbot', help='Run unified chatbot')
    chatbot_parser.add_argument('case_file', help='Path to JSON case file')
    chatbot_parser.add_argument('--mode', choices=['practice', 'exam'], default='practice')
    chatbot_parser.add_argument('--model', choices=['gpt-4.1-mini', 'gpt-5'], default='gpt-4.1-mini')
    chatbot_parser.add_argument('--memory', choices=['none', 'truncate', 'summarize'], default='summarize')

    # Test commands
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_subparsers = test_parser.add_subparsers(dest='test_type', help='Test types')
    
    test_subparsers.add_parser('unit', help='Run unit tests')
    test_subparsers.add_parser('performance', help='Run performance tests')
    test_subparsers.add_parser('all', help='Run all tests')

    args = parser.parse_args()

    if args.command == 'chatbot':
        # Run chatbot
        from chatbot.unified_chatbot import main as chatbot_main
        # Override sys.argv for the chatbot
        sys.argv = [
            'unified_chatbot.py',
            args.case_file,
            '--mode', args.mode,
            '--model', args.model,
            '--memory', args.memory
        ]
        chatbot_main()
        
    elif args.command == 'test':
        if args.test_type == 'unit':
            print("🧪 Running unit tests...")
            os.system("python tests/unit/test_prompt_config.py")
            
        elif args.test_type == 'performance':
            print("⚡ Running performance tests...")
            os.system("python tests/performance/performance_test_suite.py")
            
        elif args.test_type == 'all':
            print("🧪 Running all tests...")
            print("\n1️⃣ Unit Tests:")
            os.system("python tests/unit/test_prompt_config.py")
            print("\n2️⃣ Performance Tests:")
            os.system("python tests/performance/performance_test_suite.py")
        else:
            test_parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
