import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import docx
import PyPDF2
import re
from pathlib import Path

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def read_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def read_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def load_schema(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def load_prompt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def determine_case_type(parsed_json: dict) -> str:
    """
    Determine if case is child or adult based on child_age.value
    """
    try:
        age_info = parsed_json["examiner_view"]["patient_background"]["age"]

        # handle both dict and plain int
        if isinstance(age_info, dict) and "value" in age_info:
            age = int(age_info["value"])
        elif isinstance(age_info, (int, float)):
            age = int(age_info)
        else:
            raise ValueError("Age format not recognized")

        return "adult" if age >= 18 else "child"
    except Exception as e:
        print("⚠️ Could not determine case type, defaulting to 'child'. Error:", e)
        return "child"


def generate_output_filename(case_type: str, doc_path: str, output_dir: str) -> str:
    """
    case_type: 'child' or 'adult'
    doc_path: input document file path
    output_dir: directory to save output json
    """
    prefix = "01" if case_type == "child" else "02"

    # Extract case name from file name (remove extension)
    case_name = os.path.splitext(os.path.basename(doc_path))[0]

    # Find all existing files matching this prefix
    existing_files = [
        f for f in os.listdir(output_dir)
        if re.match(rf"{prefix}_(\d+)_.*\.json$", f)
    ]

    # Extract sequence numbers
    numbers = []
    for f in existing_files:
        pattern = rf"{prefix}_(\d+)_"
        match = re.match(pattern, f)
        if match:
            numbers.append(int(match.group(1)))

    next_num = max(numbers) + 1 if numbers else 1
    next_num_str = f"{next_num:02d}"  # format as two digits

    return os.path.join(output_dir, f"{prefix}_{next_num_str}_{case_name}.json")

def process_document(doc_path: str, schema_path: str, prompt_path: str, output_dir: str):
    if doc_path.endswith(".docx"):
        doc_text = read_docx(doc_path)
    elif doc_path.endswith(".pdf"):
        doc_text = read_pdf(doc_path)
    else:
        raise ValueError("Unsupported file format (only .docx or .pdf supported)")

    schema = load_schema(schema_path)
    system_prompt = load_prompt(prompt_path)

    # Call GPT
    response = client.chat.completions.create(
        model="gpt-5",
        temperature=1,
        response_format={"type": "json_object"},  # force JSON output
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Schema:{chr(10)}{schema}{chr(10)}{chr(10)}Case text:{chr(10)}{doc_text}"},
        ],
    )

    content = response.choices[0].message.content

    # Validate JSON
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("Model output is not valid JSON:\n" + content)

    # Determine case type automatically
    case_type = determine_case_type(parsed)

    # Generate unique output filename
    output_path = generate_output_filename(case_type, doc_path, output_dir)

    # Save JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON extracted ({case_type} case) and saved to {output_path}")

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent.parent  # points roughly to Backend/src
    schema_file = base / "core" / "config" / "example_schema.json"
    prompt_file = base / "core" / "config" / "extraction_prompt.txt"

    doc_file = r"C:\Users\ACER\Desktop\testAPI\document\iron_def-ข้อสอบ_ฝึก_SP.docx"        
    output_dir = r"C:\Users\ACER\Desktop\testAPI\extracted_data2"

    process_document(doc_file, schema_file, prompt_file, output_dir)
