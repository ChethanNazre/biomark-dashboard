import pdfplumber
import re
import json
from datetime import datetime
import os
import glob

def get_patient_json_path(patient_name, date):
    """Generate a unique JSON file path for a patient's report."""
    # Create a safe filename from patient name
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', patient_name.lower())
    # Format date as YYYYMMDD
    date_str = date.strftime("%Y%m%d")
    # Create filename: patient_name_YYYYMMDD.json
    filename = f"{safe_name}_{date_str}.json"
    return filename

def extract_value(line, biomarker_name):
    """Extract numeric value from a line of text."""
    try:
        # Remove any special characters and split
        clean_line = line.replace(',', '').replace('<', '').replace('>', '')
        
        # For HbA1c, look for percentage pattern
        if 'hba1c' in biomarker_name.lower():
            patterns = [
                r'(\d+\.?\d*)\s*%',  # Standard percentage
                r'H\.P\.L\.C\s*(\d+\.?\d*)',  # HPLC format
                r'(\d+\.?\d*)\s*H\.P\.L\.C',  # Value followed by HPLC
                r'(\d+\.?\d*)\s*$'  # Just the number at the end
            ]
            for pattern in patterns:
                match = re.search(pattern, clean_line, re.IGNORECASE)
                if match:
                    return float(match.group(1))
        
        # For other biomarkers, find the numeric value
        words = clean_line.split()
        for word in reversed(words):
            try:
                return float(word)
            except ValueError:
                continue
    except Exception as e:
        print(f"Error extracting {biomarker_name}: {str(e)}")
    return None

def extract_patient_info(text):
    """Extract patient information from text."""
    for line in text.split('\n'):
        if 'NAME' in line:
            # Extract name and age/gender if present
            match = re.search(r'NAME\s*:?\s*([^(]+)(?:\((\d+)Y/([MF])\))?', line)
            if match:
                name = match.group(1).strip()
                age = int(match.group(2)) if match.group(2) else None
                gender = match.group(3) if match.group(3) else None
                return {
                    "name": f"Dr. {name}",
                    "age": age,
                    "gender": gender,
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
    return {
        "name": "Unknown",
        "age": None,
        "gender": None,
        "date": datetime.now().strftime("%Y-%m-%d")
    }

def get_reference_ranges():
    """Return reference ranges for biomarkers."""
    return {
        "Vitamin D": {
            "unit": "ng/mL",
            "reference_range": "30-100",
            "low": 30,
            "high": 100
        },
        "Vitamin B12": {
            "unit": "pg/mL",
            "reference_range": "211-911",
            "low": 211,
            "high": 911
        },
        "Total Cholesterol": {
            "unit": "mg/dL",
            "reference_range": "<200",
            "low": 0,
            "high": 200
        },
        "LDL": {
            "unit": "mg/dL",
            "reference_range": "<100",
            "low": 0,
            "high": 100
        },
        "HDL": {
            "unit": "mg/dL",
            "reference_range": ">40",
            "low": 40,
            "high": 100
        },
        "Triglycerides": {
            "unit": "mg/dL",
            "reference_range": "<150",
            "low": 0,
            "high": 150
        },
        "Creatinine": {
            "unit": "mg/dL",
            "reference_range": "0.7-1.3",
            "low": 0.7,
            "high": 1.3
        },
        "HbA1c": {
            "unit": "%",
            "reference_range": "<5.7",
            "low": 0,
            "high": 5.7
        }
    }

def save_biomarkers_json(data, patient_name, date):
    """Save biomarkers data to a unique JSON file for each patient."""
    try:
        # Create reports directory if it doesn't exist
        os.makedirs("reports", exist_ok=True)
        
        # Generate unique filename
        filename = get_patient_json_path(patient_name, date)
        filepath = os.path.join("reports", filename)
        
        # Ensure the file is not read-only if it exists
        if os.path.exists(filepath):
            os.chmod(filepath, 0o666)
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Successfully saved biomarkers data to {filepath}")
        return True
    except Exception as e:
        print(f"Error saving JSON file: {str(e)}")
        return False

def process_pdf_to_json(pdf_path):
    """Process PDF and save data to JSON."""
    # Define biomarkers with their search patterns
    biomarkers = {
        "Total Cholesterol": {
            "patterns": ["TOTAL CHOLESTEROL", "CHOLESTEROL - TOTAL"],
            "value": None
        },
        "LDL": {
            "patterns": ["LDL CHOLESTEROL", "LDL-C"],
            "value": None
        },
        "HDL": {
            "patterns": ["HDL CHOLESTEROL", "HDL-C"],
            "value": None
        },
        "Triglycerides": {
            "patterns": ["TRIGLYCERIDES", "TRIG"],
            "value": None
        },
        "Creatinine": {
            "patterns": ["CREATININE", "CREATININE - SERUM"],
            "value": None
        },
        "Vitamin D": {
            "patterns": ["VITAMIN D", "25-OH VITAMIN D"],
            "value": None
        },
        "Vitamin B12": {
            "patterns": ["VITAMIN B-12", "VITAMIN B12", "B-12"],
            "value": None
        },
        "HbA1c": {
            "patterns": ["HbA1c", "HbA1c - (HPLC)", "GLYCATED HEMOGLOBIN"],
            "value": None
        }
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            # Extract patient information
            patient_info = extract_patient_info(full_text)
            current_date = datetime.now()

            # Extract biomarkers
            lines = full_text.split('\n')
            for idx, line in enumerate(lines):
                for biomarker, info in biomarkers.items():
                    if info["value"] is None:
                        for pattern in info["patterns"]:
                            if pattern.lower() in line.lower():
                                # Special handling for HbA1c: look at next 2 lines for value
                                if biomarker == "HbA1c":
                                    for offset in range(1, 3):
                                        if idx + offset < len(lines):
                                            val = extract_value(lines[idx + offset], biomarker)
                                            if val is not None:
                                                info["value"] = val
                                                break
                                    if info["value"] is not None:
                                        break
                                else:
                                    value = extract_value(line, biomarker)
                                    if value is not None:
                                        info["value"] = value
                                        break

        # Get reference ranges
        reference_ranges = get_reference_ranges()

        # Create biomarkers dictionary with values and reference ranges
        biomarkers_data = {}
        for biomarker, info in biomarkers.items():
            if info["value"] is not None:
                biomarkers_data[biomarker] = {
                    "value": info["value"],
                    **reference_ranges[biomarker]
                }

        # Create final JSON structure
        json_data = {
            "patient": patient_info,
            "biomarkers": biomarkers_data,
            "report_info": {
                "pdf_filename": os.path.basename(pdf_path),
                "processed_date": current_date.strftime("%Y-%m-%d %H:%M:%S")
            }
        }

        # Save to JSON file
        if save_biomarkers_json(json_data, patient_info["name"], current_date):
            print("\n✅ Data Extraction Summary:")
            print(f"Patient: {patient_info['name']}")
            print(f"Date: {patient_info['date']}")
            print("\nExtracted Values:")
            for biomarker, info in biomarkers.items():
                value = info["value"]
                print(f"{biomarker}: {value if value is not None else 'Not found'}")
            return True
        return False

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return False

def process_directory(directory_path):
    """Process all PDF files in a directory."""
    pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {directory_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    for pdf_file in pdf_files:
        print(f"\nProcessing {pdf_file}...")
        process_pdf_to_json(pdf_file)

if __name__ == "__main__":
    # Process a single PDF file
    pdf_path = "Sample Reports/ReportAccess.aspx.pdf"
    process_pdf_to_json(pdf_path)
    
    # Or process all PDFs in a directory
    # process_directory("Sample Reports")
