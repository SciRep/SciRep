from flask import Flask, request, jsonify, send_file, render_template, send_from_directory, abort
from pathlib import Path
import re
import csv
import os

app = Flask(__name__)

PATTERNS = {
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
    't1_aha_segmentation': {"AHA_Segment_T1": ""},
    't2_aha_segmentation': {"AHA_Segment_T2": ""}
}

def extract_values(file_path, extraction_type):
    """Extract values from reports based on extraction type"""
    try:
        with open(file_path, 'r', encoding='utf-16') as file:
            data = file.read()
        
        results = {"File": file_path.name}
        
        if extraction_type in ['t1_aha_segmentation', 't2_aha_segmentation']:
            t_type = "T1" if extraction_type == 't1_aha_segmentation' else "T2"
            
            section_pattern = r'Regional Native T1 \(AHA Segmentation\)([\s\S]*?)(?=\n\n)' if t_type == "T1" else \
                              r'Regional (T2|CA T1) \(AHA [Ss]egmentation\)([\s\S]*?)(?=\n\n)'
            
            section = re.search(section_pattern, data)
            if section:
                section_data = section.group(0) if t_type == "T2" else section.group(1)
                segments = re.findall(r'(\d+)\s+([\d.]+)', section_data)
                
                for segment_num, value in segments:
                    results[f"AHA_Segment_{t_type}_{segment_num}"] = value
        else:
            for key, pattern in PATTERNS[extraction_type].items():
                match = re.search(pattern, data)
                results[key] = match.group(1) if match else None
        
        return results
    except Exception as e:
        app.logger.error(f"Error extracting values from {file_path}: {e}")
        return {"File": file_path.name, "Error": str(e)}

def process_files():
    """Process uploaded files and return results"""
    if 'files[]' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    extraction_type = request.path.split('_', 1)[1]
    
    upload_dir = Path('uploads')
    upload_dir.mkdir(exist_ok=True)
    
    results = []
    
    try:
        for file in files:
            file_path = upload_dir / file.filename
            file.save(file_path)
            
            extracted_data = extract_values(file_path, extraction_type)
            results.append(extracted_data)
            
            file_path.unlink()
        
        output_path = upload_dir / f'extracted_{extraction_type}_values.csv'
        
        if results:
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            
            return send_file(output_path, as_attachment=True)
        else:
            return jsonify({"error": "No data extracted from files"}), 400
            
    except Exception as e:
        app.logger.error(f"Error processing files: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/support')
def support():
    """Render the support page"""
    return render_template('support_page.html')

@app.route('/format/<extraction_type>')
def show_format(extraction_type):
    """Show format examples for extraction types"""
    title = extraction_type.replace('_', ' ').title()
    title = title.replace('Aha', 'AHA').replace('Sax', 'SAX').replace('Lax', 'LAX')
    
    formats = []
    
    for i in range(1, 3):
        format_path = Path(f'static/format_{extraction_type}_{i}.txt')
        if format_path.exists():
            try:
                with open(format_path, 'r', encoding='utf-16') as file:
                    formats.append(file.read())
            except Exception as e:
                app.logger.error(f"Error reading format file {format_path}: {e}")
    
    if not formats:
        abort(404, description="No format files found")
    
    return render_template('format_template.html', title=title, formats=formats)

for extraction_type in PATTERNS.keys():
    app.add_url_rule(
        f'/upload_{extraction_type}',
        f'upload_{extraction_type}',
        process_files,
        methods=['POST']
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
