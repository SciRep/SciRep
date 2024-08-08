import azure.functions as func
import logging
import json
from pathlib import Path
import re
import csv
import tempfile

app = func.FunctionApp()

def extract_values(file_path, patterns):
    try:
        with open(file_path, 'r', encoding='utf-16') as file:
            data = file.read()
        
        results = {}
        for key, pattern in patterns.items():
            if key.startswith('AHA_Segment_'):
                if 'T1' in key:
                    aha_section = re.search(r'Regional Native T1 \(AHA Segmentation\)([\s\S]*?)(?=\n\n)', data)
                elif 'T2' in key:
                    # Look for both T2 and CA T1 patterns
                    aha_section = re.search(r'Regional (T2|CA T1) \(AHA [Ss]egmentation\)([\s\S]*?)(?=\n\n)', data)
                
                if aha_section:
                    aha_data = aha_section.group(0) if 'T2' in key else aha_section.group(1)
                    segments = re.findall(r'(\d+)\s+([\d.]+)', aha_data)
                    results.update({f"{key}_{seg}": value for seg, value in segments})
            else:
                match = re.search(pattern, data)
                results[key] = match.group(1) if match else None
        
        return results
    except Exception as e:
        app.logger.error(f"Error extracting values: {e}")
        return {}

patterns = {
    'SAX_function': {
        "LV EDV": r"Clinical Results LV[\s\S]*?EDV\s+([\d.]+)\s+ml",
        "LV ESV": r"Clinical Results LV[\s\S]*?ESV\s+([\d.]+)\s+ml",
        "LV EF": r"Clinical Results LV[\s\S]*?EF\s+([\d.]+)\s+%",
        "RV EDV": r"Clinical Results RV[\s\S]*?EDV\s+([\d.]+)\s+ml",
        "RV ESV": r"Clinical Results RV[\s\S]*?ESV\s+([\d.]+)\s+ml",
        "RV EF": r"Clinical Results RV[\s\S]*?EF\s+([\d.]+)\s+%"
    },
    'LAX_function': {
        "LV EDV": r"Biplanar 2CV / 4CV[\s\S]*?EDV\s+([\d.]+)\s+ml",
        "LV ESV": r"Biplanar 2CV / 4CV[\s\S]*?ESV\s+([\d.]+)\s+ml",
        "LV SV": r"Biplanar 2CV / 4CV[\s\S]*?SV\s+([\d.]+)\s+ml",
        "LV EF": r"Biplanar 2CV / 4CV[\s\S]*?EF\s+([\d.]+)\s+%",
        "CO": r"Biplanar 2CV / 4CV[\s\S]*?CO\s+([\d.]+)\s+l/min",
        "HR": r"Biplanar 2CV / 4CV[\s\S]*?HR\s+([\d.]+)\s+1/min"
    },
    'atrial_volume': {
        "Min LA Vol": r"Min LA Vol\s+([\d.]+)\s+ml",
        "Min LA Area": r"Min LA Area\s+([\d.]+)\s+cm ²",
        "Phase Min LA Vol": r"Phase Min LA Vol\s+(\d+)",
        "Max LA Vol": r"Max LA Vol\s+([\d.]+)\s+ml",
        "Max LA Area": r"Max LA Area\s+([\d.]+)\s+cm ²",
        "Phase Max LA Vol": r"Phase Max LA Vol\s+(\d+)",
        "Min LA Vol/H": r"Min LA Vol/H\s+([\d.]+)\s+ml/m",
        "Min LA Vol/BSA": r"Min LA Vol/BSA\s+([\d.]+)\s+ml/m²",
        "Max LA Vol/H": r"Max LA Vol/H\s+([\d.]+)\s+ml/m",
        "Max LA Vol/BSA": r"Max LA Vol/BSA\s+([\d.]+)\s+ml/m²",
        "LA EF": r"LA EF\s+([\d.]+|\-\-)\s+%",
        "Min RA Vol": r"Min RA Vol\s+([\d.]+)\s+ml",
        "Min RA Area": r"Min RA Area\s+([\d.]+)\s+cm ²",
        "Phase Min RA Vol": r"Phase Min RA Vol\s+(\d+)",
        "Max RA Vol": r"Max RA Vol\s+([\d.]+)\s+ml",
        "Max RA Area": r"Max RA Area\s+([\d.]+)\s+cm ²",
        "Phase Max RA Vol": r"Phase Max RA Vol\s+(\d+)",
        "Min RA Vol/H": r"Min RA Vol/H\s+([\d.]+)\s+ml/m",
        "Min RA Vol/BSA": r"Min RA Vol/BSA\s+([\d.]+)\s+ml/m²",
        "Max RA Vol/H": r"Max RA Vol/H\s+([\d.]+)\s+ml/m",
        "Max RA Vol/BSA": r"Max RA Vol/BSA\s+([\d.]+)\s+ml/m²",
        "RA EF": r"RA EF\s+([\d.]+|\-\-)\s+%"
    },
    'mapping': {
        "Native Mean Global T1": r"Native T1[\s\S]*?Global Myo T1 Across Slices\s+(\d+\.?\d*)",
        "Native Mean Basal T1": r"Regional Native T1 Slice 1[\s\S]*?Myo\s+(\d+\.?\d*)",
        "Native Mean Mid T1": r"Regional Native T1 Slice 2[\s\S]*?Myo\s+(\d+\.?\d*)",
        "CA Mean Global T2": r"CA T1[\s\S]*?Global Myo T1 Across Slices\s+(\d+\.?\d*)",
        "CA Mean Basal T2": r"Regional CA T1 Slice 1[\s\S]*?Myo\s+(\d+\.?\d*)",
        "CA Mean Mid T2": r"Regional CA T1 Slice 2[\s\S]*?Myo\s+(\d+\.?\d*)"
    },
    't1_aha_segmentation': {
        "AHA_Segment_T1": ""
    },
    't2_aha_segmentation': {
        "AHA_Segment_T2": ""
    }
}

def process_reports(folder_path, extract_function):
    results = []
    for report_file in sorted(Path(folder_path).glob('*.txt')):
        values = extract_function(report_file)
        results.append({"File": report_file.name, **values})
        report_file.unlink()
    return results

@app.route(route="upload/{extraction_type}")
def handle_upload(req: func.HttpRequest, extraction_type: str) -> func.HttpResponse:
    logging.info(f'Python HTTP trigger function processed a request for {extraction_type}.')

    try:
        # Get the uploaded file
        file = req.files['file']
        
        # Create a temporary file to save the uploaded content
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
        
        # Extract values
        extract_function = lambda file_path: extract_values(file_path, patterns[extraction_type])
        results = [{"File": file.filename, **extract_function(temp_file.name)}]

        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', newline='', delete=False) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        # Read the CSV file and return its content
        with open(csvfile.name, 'r') as f:
            csv_content = f.read()

        # Clean up temporary files
        Path(temp_file.name).unlink()
        Path(csvfile.name).unlink()

        return func.HttpResponse(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=extracted_{extraction_type}_values.csv"
            }
        )
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=400
        )

@app.route(route="format/{extraction_type}")
def show_format(req: func.HttpRequest, extraction_type: str) -> func.HttpResponse:
    logging.info(f'Python HTTP trigger function processed a request for format {extraction_type}.')

    title = f"{extraction_type.replace('_', ' ').title()}"
    title = title.replace('Aha', 'AHA').replace('Sax', 'SAX').replace('Lax', 'LAX')
    
    # Define paths for format files
    format1_path = Path(f'static/format_{extraction_type}_1.txt')
    format2_path = Path(f'static/format_{extraction_type}_2.txt')
    
    formats = []
    
    # Try to read format 1
    if format1_path.exists():
        with open(format1_path, 'r', encoding='utf-16') as file:
            formats.append(file.read())
    
    # Try to read format 2 if it exists
    if format2_path.exists():
        with open(format2_path, 'r', encoding='utf-16') as file:
            formats.append(file.read())
    
    # If no formats were found, return a 404 error
    if not formats:
        return func.HttpResponse(
            "No format files found",
            status_code=404
        )
    
    # Return the formats as JSON
    return func.HttpResponse(
        json.dumps({"title": title, "formats": formats}),
        mimetype="application/json"
    )
