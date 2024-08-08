import azure.functions as func
import logging
import json
from pathlib import Path
import re
import csv
import tempfile
import traceback

app = func.FunctionApp()



# Your extract_values function here (unchanged)
def extract_values(file_content, patterns):
    try:
        results = {}
        for key, pattern in patterns.items():
            if key.startswith('AHA_Segment_'):
                if 'T1' in key:
                    aha_section = re.search(r'Regional Native T1 \(AHA Segmentation\)([\s\S]*?)(?=\n\n)', file_content)
                elif 'T2' in key:
                    aha_section = re.search(r'Regional (T2|CA T1) \(AHA [Ss]egmentation\)([\s\S]*?)(?=\n\n)', file_content)
                
                if aha_section:
                    aha_data = aha_section.group(0) if 'T2' in key else aha_section.group(1)
                    segments = re.findall(r'(\d+)\s+([\d.]+)', aha_data)
                    results.update({f"{key}_{seg}": value for seg, value in segments})
            else:
                match = re.search(pattern, file_content)
                results[key] = match.group(1) if match else None
        
        return results
    except Exception as e:
        logging.error(f"Error extracting values: {e}")
        return {}


@app.route(route="upload/{extraction_type}", methods=["POST"])
def handle_upload(req: func.HttpRequest, extraction_type: str) -> func.HttpResponse:
    logging.info(f'Python HTTP trigger function processed a request for {extraction_type}.')

    try:
        # Get the uploaded file
        file = req.files.get('file')
        if not file:
            logging.warning("No file uploaded")
            return func.HttpResponse(
                json.dumps({"error": "No file uploaded"}),
                status_code=400,
                mimetype="application/json"
            )
        
        logging.info(f"File received: {file.filename}")
        
        # Read file content
        try:
            file_content = file.read().decode('utf-16')
        except UnicodeDecodeError:
            logging.warning("Failed to decode with utf-16, trying utf-8")
            file.seek(0)  # Reset file pointer
            file_content = file.read().decode('utf-8')
        
        logging.info("File content read successfully")
        
        # Extract values
        results = [{"File": file.filename, **extract_values(file_content, patterns[extraction_type])}]
        logging.info(f"Extracted values: {results}")

        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', newline='', delete=False) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        logging.info(f"CSV file created: {csvfile.name}")

        # Read the CSV file and return its content
        with open(csvfile.name, 'r') as f:
            csv_content = f.read()

        # Clean up temporary file
        Path(csvfile.name).unlink()

        logging.info("Returning CSV content")
        return func.HttpResponse(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=extracted_{extraction_type}_values.csv"
            }
        )
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        logging.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": str(e), "stack_trace": traceback.format_exc()}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="format/{extraction_type}", methods=["GET"])
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
    else:
        logging.warning(f"Format file not found: {format1_path}")
    
    # Try to read format 2 if it exists
    if format2_path.exists():
        with open(format2_path, 'r', encoding='utf-16') as file:
            formats.append(file.read())
    else:
        logging.warning(f"Format file not found: {format2_path}")
    
    # If no formats were found, return a 404 error
    if not formats:
        logging.error("No format files found")
        return func.HttpResponse(
            json.dumps({"error": "No format files found"}),
            status_code=404,
            mimetype="application/json"
        )
    
    # Return the formats as JSON
    logging.info(f"Returning formats for {extraction_type}")
    return func.HttpResponse(
        json.dumps({"title": title, "formats": formats}),
        mimetype="application/json"
    )
