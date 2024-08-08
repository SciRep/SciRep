import azure.functions as func
import logging
import json
import re
import csv
import io

# Your patterns dictionary
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
    # Add other pattern types here
}

def extract_values(file_content, extraction_type):
    if extraction_type not in patterns:
        raise ValueError(f"Unknown extraction type: {extraction_type}")
    
    results = {}
    for key, pattern in patterns[extraction_type].items():
        match = re.search(pattern, file_content)
        results[key] = match.group(1) if match else None
    return results

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Get the extraction type from query parameters
        extraction_type = req.params.get('extraction_type')
        if not extraction_type:
            raise ValueError("extraction_type is required")

        # Get the uploaded file
        file = req.files.get('file')
        if not file:
            raise ValueError("No file uploaded")

        # Read file content
        file_content = file.read().decode('utf-8')  # or 'utf-16' if that's what you're using

        # Extract values
        results = extract_values(file_content, extraction_type)

        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['Metric', 'Value'])
        writer.writeheader()
        for key, value in results.items():
            writer.writerow({'Metric': key, 'Value': value})

        # Prepare the response
        csv_content = output.getvalue()
        
        return func.HttpResponse(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=extracted_{extraction_type}_values.csv"
            }
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=400,
            mimetype="application/json"
        )

def format(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Format function processed a request.')

    try:
        extraction_type = req.params.get('extraction_type')
        if not extraction_type:
            raise ValueError("extraction_type is required")

        if extraction_type not in patterns:
            raise ValueError(f"Unknown extraction type: {extraction_type}")

        format_info = {
            "title": extraction_type.replace('_', ' ').title(),
            "fields": list(patterns[extraction_type].keys())
        }

        return func.HttpResponse(
            json.dumps(format_info),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=400,
            mimetype="application/json"
        )
