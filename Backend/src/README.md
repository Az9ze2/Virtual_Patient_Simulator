# Virtual Patient Simulator - Medical OSCE Chatbot

A professional, unified chatbot system for medical OSCE (Objective Structured Clinical Examination) simulations.

## 📁 Project Structure

```
├── core/                          # Main source code
│   ├── __init__.py
│   ├── chatbot/                   # Core chatbot functionality
│   │   ├── __init__.py
│   │   └── unified_chatbot.py     # Main unified chatbot
│   ├── config/                    # Configuration files
│   │   ├── __init__.py
│   │   └── prompt_config.py       # Prompt templates and configuration
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       ├── data_extraction.py     # Data extraction utilities
│       ├── json_data_validator.py # JSON validation
│       └── model_performance_tester.py # Performance testing
├── data/                          # Case data files
│   ├── cases_01/                  # Mother/Guardian cases (01_*.json)
│   └── cases_02/                  # Patient cases (02_*.json)
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── unit/                      # Unit tests
│   │   ├── __init__.py
│   │   └── test_prompt_config.py  # Prompt configuration tests
│   ├── integration/               # Integration tests
│   │   ├── __init__.py
│   │   └── (various test files)
│   └── performance/               # Performance tests
│       ├── __init__.py
│       └── performance_test_suite.py # Comprehensive performance testing
├── archive/                       # Archived versions
├── docs/                         # Documentation
├── debug/                        # Debug scripts
├── logs/                         # Log files
└── output/                       # Output files and results
```

## 🚀 Quick Start

### Easy Launcher (Recommended)
```bash
# Run chatbot with launcher
python run.py chatbot data/cases_01/01_01_breast_feeding_problems.json
python run.py chatbot data/cases_02/02_01_blood_in_stool.json --mode exam

# Run tests with launcher
python run.py test unit           # Unit tests
python run.py test performance    # Performance tests
python run.py test all            # All tests

# Get help
python run.py --help
python run.py chatbot --help
```

### Direct Commands
```bash
# Run chatbot directly
python core/chatbot/unified_chatbot.py data/cases_01/01_01_breast_feeding_problems.json
python core/chatbot/unified_chatbot.py data/cases_02/02_01_blood_in_stool.json --mode exam

# Run tests directly
python tests/unit/test_prompt_config.py
python tests/performance/performance_test_suite.py
```

## 📋 Case Types

- **01_*.json**: Mother/Guardian cases 
  - Simulates mother speaking with doctor about child patient
  - Uses "ค่ะ" polite particles and motherly language
  - Display name: "👩‍⚕️ มารดา"

- **02_*.json**: Patient cases
  - Simulates patient speaking directly with doctor
  - Uses "ครับ/ค่ะ" based on patient gender
  - Display name: "👩‍⚕️ ผู้ป่วยจำลอง"

## 🧪 Performance Test Results

Latest performance test results:
- **17 cases tested** (14 × 01 cases + 3 × 02 cases)
- **100% success rate** (all cases completed)
- **99.2% validation rate** (responses appropriate and correct)
- **83,032 tokens used** (efficient usage)
- **244.9 seconds** total test time (~4 minutes)

## 🎯 Key Features

### Unified System
- **Single Entry Point**: One script handles both case types automatically
- **Automatic Detection**: Determines case type from filename patterns
- **Consistent Interface**: Same command-line arguments for all cases

### Quality Assurance
- **Exact Original Prompts**: Preserves tested prompt structures
- **Comprehensive Validation**: Checks language, behavior, and response quality
- **Performance Monitoring**: Detailed metrics and reporting

### Professional Architecture
- **Component-Based Design**: Clean separation of concerns
- **Zero Code Duplication**: Shared logic across case types
- **Extensible Structure**: Easy to add new case types and features

## 🛠️ Development

### Requirements
- Python 3.8+
- OpenAI API key (set in `.env` file)
- Required packages: `openai`, `langchain-core`, `python-dotenv`

### Environment Setup
```bash
# Set your OpenAI API key
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

## 🎉 Success Metrics

The unified system has achieved:
- **100% compatibility** with original functionality
- **99.2% response quality** across all test cases
- **Professional code organization** with clear structure
- **Comprehensive test coverage** for quality assurance
- **Efficient resource usage** with optimized token consumption

---

**Built with ❤️ for medical education and OSCE simulation**
