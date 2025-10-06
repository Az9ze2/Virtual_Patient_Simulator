# Virtual Patient Simulator - Backend

A sophisticated chatbot system that simulates standardized patients for medical education and OSCE (Objective Structured Clinical Examination) training.

## 🏗️ Project Structure

```
src/
├── core/                    # Core application modules
│   ├── chatbot_test_script.py      # Main chatbot implementation (latest version)
│   ├── patient_chatbot.py          # Original patient chatbot implementation
│   ├── document_extractor.py       # Document processing utilities
│   ├── json_data_validator.py      # JSON data validation tools
│   └── model_performance_tester.py # Performance testing and benchmarking
│
├── tests/                   # Test suites and verification scripts
│   ├── test_all_cases_fix.py            # Comprehensive test across all cases
│   ├── test_fallback_functionality.py  # Fallback question system tests
│   ├── test_specific_fallbacks.py      # Targeted fallback tests
│   ├── test_improved_analysis.py       # GPT analysis improvement tests
│   ├── verify_fix.py                   # False positive fix verification
│   ├── verify_legitimate_matches.py    # Legitimate match preservation tests
│   └── show_complete_conversation.py   # Full conversation flow demonstration
│
├── debug/                   # Debugging and analysis tools
│   ├── debug_gpt_analysis.py      # GPT analysis debugging
│   ├── debug_system_prompt.py     # System prompt debugging
│   ├── debug_case_06.py           # Specific case debugging
│   └── analyze_fallback_questions.py # Fallback question analysis
│
├── data/                    # Case data and test files
│   ├── 01_01_breast_feeding_problems.json    # Case files (01-14)
│   ├── 01_02_CHC_9_months.json
│   ├── ... (other case files)
│   └── json_validation_report_*.txt          # Validation reports
│
├── docs/                    # Documentation and reports
│   ├── all_conversations_log.md         # Complete conversation logs
│   └── dataset_test_summary.md          # Test result summaries
│
├── archive/                 # Legacy versions and backups
│   ├── chatbot_test_script_v0.py        # Version history
│   ├── chatbot_test_script_v0_1.py
│   └── ... (other versions)
│
├── .env                     # Environment configuration (API keys)
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Required packages: `openai`, `langchain-core`

### Setup
1. **Configure API Key**:
   ```bash
   # Create .env file with your OpenAI API key
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

2. **Run Main Chatbot**:
   ```bash
   python core/chatbot_test_script.py
   ```

3. **Run Comprehensive Tests**:
   ```bash
   python tests/test_all_cases_fix.py
   ```

## 🔧 Key Features

### ✅ **Fixed Issues (Latest Version)**
- **False Positive Prevention**: Basic history questions no longer incorrectly trigger fallback questions
- **Semantic Understanding**: Legitimate medical questions correctly trigger appropriate fallback responses
- **"No More Questions" Response**: Proper handling when all fallback questions are addressed

### 🧪 **Testing Suite**
- **Comprehensive Coverage**: Tests across all 14 available case files
- **False Positive Detection**: Ensures basic questions don't trigger unrelated fallbacks
- **Legitimate Match Verification**: Confirms appropriate questions still work correctly
- **Full Conversation Flow**: Complete dialogue demonstrations

### 🔍 **Debugging Tools**
- **GPT Analysis Debugging**: Understand how the AI interprets questions
- **System Prompt Analysis**: Visualize prompt updates and changes
- **Case-Specific Debugging**: Targeted troubleshooting for specific scenarios

## 📋 Case Files Available

The system includes 14 medical case scenarios:
1. Breast feeding problems (cracked nipple)
2. Child Health Check - 9 months (anemia)
3. Child Health Check - 2 months (phimosis)  
4. Edema (acute glomerulonephritis)
5. Fever with rash
6. Functional constipation
7. Gastroenteritis with secondary lactase deficiency
8. **Gastroenteritis** (1 fallback question)
9. **Hydrocele** (2 fallback questions)
10. **Iron deficiency anemia** (4 fallback questions)
11. Latent TB infection
12. Neonatal jaundice
13. Child health check (EPI vaccination)
14. Blood in stool (intussusception)

## 🎯 Usage Examples

### Basic Conversation
```python
from core.chatbot_test_script import SimpleChatbotTester

# Initialize chatbot
bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
case_data = bot.load_case_data("data/01_08_gastroenteritis.json")
bot.setup_conversation(case_data)

# Start conversation
response, time_taken = bot.chat_turn("สวัสดีครับ วันนี้มีเรื่องอะไรให้ช่วยครับ")
print(f"Mother: {response}")
```

### Running Specific Tests
```bash
# Test fallback functionality
python tests/test_fallback_functionality.py

# Show complete conversation flow
python tests/show_complete_conversation.py

# Verify false positive fix
python tests/verify_fix.py
```

### Debugging
```bash
# Debug GPT analysis behavior
python debug/debug_gpt_analysis.py

# Debug system prompt updates  
python debug/debug_system_prompt.py
```

## 📊 Test Results

**Latest Test Results (Fixed Version)**:
- ✅ **0 false positives** across all 14 case files
- ✅ **100% success rate** for legitimate question matching  
- ✅ **Perfect "no more questions"** response handling
- ✅ **All fallback functionality** working correctly

## 🔄 Version History

- **v0.6 (Current)**: Fixed false positive issue, improved "no more questions" response
- **v0.5**: Added memory management and conversation summarization
- **v0.4**: Enhanced fallback question system
- **v0.3**: Basic GPT analysis implementation
- **v0.2**: Improved system prompts
- **v0.1**: Initial implementation
- **v0**: Original prototype

## 🛠️ Development

### Adding New Test Cases
1. Place JSON case file in `data/` directory
2. Add test configuration in relevant test files
3. Run validation: `python core/json_data_validator.py`

### Debugging Issues
1. Use `debug/debug_system_prompt.py` to examine prompt behavior
2. Use `debug/debug_gpt_analysis.py` to understand AI interpretation
3. Check conversation logs in `docs/` for detailed analysis

## 📝 License

This project is part of the IRPC Internship program for medical education technology development.

## 🤝 Contributing

This is an educational project. For issues or improvements, please document findings in the appropriate debug or test files.

---
*Last Updated: October 1, 2025*
*Version: 0.6 (Stable)*
