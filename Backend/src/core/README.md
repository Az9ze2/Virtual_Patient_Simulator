# Unified Medical OSCE Chatbot System

This unified chatbot system handles both 01 (mother/guardian) and 02 (patient) case types automatically using a component-based architecture.

## Files Overview

### `unified_chatbot.py`
The main unified chatbot script that automatically detects case types and uses appropriate prompts.

**Usage:**
```bash
python unified_chatbot.py <case_file> [options]

# Examples:
python unified_chatbot.py data/01_01_breast_feeding_problems.json
python unified_chatbot.py data/02_01_blood_in_stool.json --mode exam --model gpt-5
```

**Arguments:**
- `case_file`: Path to JSON case file (01_*.json or 02_*.json)
- `--mode`: `practice` (default) or `exam` mode
- `--model`: `gpt-4.1-mini` (default) or `gpt-5`
- `--memory`: Memory management strategy (`summarize`, `truncate`, `none`)

### `prompt_config.py`
Configuration component containing exact original prompt templates and data extraction logic.

**Features:**
- Automatic case type detection from filename patterns
- Preserves exact original prompts from both chatbot versions
- Handles all data extraction logic for both case types
- Provides appropriate display names and summary prompts

### `test_prompt_config.py`
Test script to verify prompt configuration functionality.

**Run tests:**
```bash
python test_prompt_config.py
```

## Case Type Detection

The system automatically detects case types based on filename patterns:

- **01_*.json**: Mother/Guardian cases
  - Uses prompts for mother speaking about child patient
  - Display name: "👩‍⚕️ มารดา"

- **02_*.json**: Patient cases  
  - Uses prompts for patient speaking directly
  - Display name: "👩‍⚕️ ผู้ป่วยจำลอง"

## Architecture Benefits

### 🎯 **Single Entry Point**
- One script handles both case types
- No need to remember which script to use for which file

### ⚡ **Zero Code Duplication**
- All common functionality is shared
- Prompts are centralized in configuration component

### 🔧 **Maintainability**
- Easy to update prompts - only need to edit `prompt_config.py`
- Changes apply to both case types automatically
- Clear separation of concerns

### 🧪 **Testability**
- Comprehensive test suite for all functionality
- Easy to verify prompt generation and case detection

### 🏗️ **Extensibility**
- Easy to add new case types (03, 04, etc.)
- Component-based design allows for easy modifications

## Migration from Original Scripts

The unified system replaces:
- `chatbot_test_script.py` (for 01_*.json files)  
- `chatbot_test_script02.py` (for 02_*.json files)

### Key Advantages Over Original Scripts:

1. **Automatic Detection**: No need to choose which script to run
2. **Consistent Interface**: Same command-line arguments for both types
3. **Preserved Logic**: Exact original prompts and data extraction preserved
4. **Better Error Handling**: Clearer error messages and fallback behavior
5. **Unified Token Tracking**: Consistent reporting across case types

## Configuration Details

### Prompt Templates
Both prompt templates preserve the exact original structure:

**01 Template Features:**
- Mother-specific response rules
- Child patient context extraction
- Mother profile and emotional state
- Original dialogue examples

**02 Template Features:**  
- Adult/child patient response rules
- Patient profile and medical history
- Illness timeline and symptoms
- Original dialogue examples

### Data Extraction
Maintains exact original data extraction paths:
- Handles both dictionary and string age formats
- Preserves original field mappings
- Maintains original null/missing data handling

## Testing

Run the test suite to verify functionality:

```bash
# Test prompt configuration
python test_prompt_config.py

# Test with actual case files
python unified_chatbot.py data/01_01_breast_feeding_problems.json
python unified_chatbot.py data/02_01_blood_in_stool.json
```

## Troubleshooting

### Common Issues:

1. **"Unknown case type" warning**: 
   - Ensure filename starts with "01_" or "02_"
   - System will default to "01" type if pattern not recognized

2. **Missing case file**:
   - Verify the JSON file path is correct
   - Ensure the file exists and is readable

3. **API key issues**:
   - Ensure OPENAI_API_KEY is set in your .env file
   - Check that the API key is valid and has sufficient credits

## Future Enhancements

The component-based architecture makes it easy to add:
- New case types (03_*, 04_*, etc.)
- Additional prompt variations
- New data extraction patterns
- Enhanced question tracking systems
