from flask import Flask, request, jsonify, send_file, render_template_string
import os
import re
import csv
from functools import partial

app = Flask(__name__)

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
                    aha_section = re.search(r'Regional T2 \(AHA segmentation\)([\s\S]*?)(?=\n\n)', data)
                
                if aha_section:
                    aha_data = aha_section.group(1)
                    segments = re.findall(r'(\d+)\s+([\d.]+)', aha_data)
                    results.update({f"{key}_{seg}": value for seg, value in segments})
            else:
                match = re.search(pattern, data)
                results[key] = match.group(1) if match else None
        
        return results
    except Exception as e:
        app.logger.error(f"Error extracting values: {e}")
        return {}

extract_t1_t2_values = partial(extract_values, patterns={
    "Native Mean Global T1": r"Native T1[\s\S]*?Global Myo T1 Across Slices\s+(\d+\.?\d*)",
    "Native Mean Basal T1": r"Regional Native T1 Slice 1[\s\S]*?Myo\s+(\d+\.?\d*)",
    "Native Mean Mid T1": r"Regional Native T1 Slice 2[\s\S]*?Myo\s+(\d+\.?\d*)",
    "CA Mean Global T2": r"CA T1[\s\S]*?Global Myo T1 Across Slices\s+(\d+\.?\d*)",
    "CA Mean Basal T2": r"Regional CA T1 Slice 1[\s\S]*?Myo\s+(\d+\.?\d*)",
    "CA Mean Mid T2": r"Regional CA T1 Slice 2[\s\S]*?Myo\s+(\d+\.?\d*)"
})

extract_SAX_function_values = partial(extract_values, patterns={
    "LV EDV": r"Clinical Results LV[\s\S]*?EDV\s+([\d.]+)\s+ml",
    "LV ESV": r"Clinical Results LV[\s\S]*?ESV\s+([\d.]+)\s+ml",
    "LV EF": r"Clinical Results LV[\s\S]*?EF\s+([\d.]+)\s+%",
    "RV EDV": r"Clinical Results RV[\s\S]*?EDV\s+([\d.]+)\s+ml",
    "RV ESV": r"Clinical Results RV[\s\S]*?ESV\s+([\d.]+)\s+ml",
    "RV EF": r"Clinical Results RV[\s\S]*?EF\s+([\d.]+)\s+%"
})

extract_LAX_function_values = partial(extract_values, patterns={
    "LV EDV": r"Biplanar 2CV / 4CV[\s\S]*?EDV\s+([\d.]+)\s+ml",
    "LV ESV": r"Biplanar 2CV / 4CV[\s\S]*?ESV\s+([\d.]+)\s+ml",
    "LV SV": r"Biplanar 2CV / 4CV[\s\S]*?SV\s+([\d.]+)\s+ml",
    "LV EF": r"Biplanar 2CV / 4CV[\s\S]*?EF\s+([\d.]+)\s+%",
    "CO": r"Biplanar 2CV / 4CV[\s\S]*?CO\s+([\d.]+)\s+l/min",
    "HR": r"Biplanar 2CV / 4CV[\s\S]*?HR\s+([\d.]+)\s+1/min"
})

extract_atrial_volume_values = partial(extract_values, patterns={
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
})

extract_t1_aha_segmentation_values = partial(extract_values, patterns={
    "AHA_Segment_T1": ""  # Empty pattern will trigger the T1 AHA segmentation extraction
})

extract_t2_aha_segmentation_values = partial(extract_values, patterns={
    "AHA_Segment_T2": ""  # Empty pattern will trigger the T2 AHA segmentation extraction
})


def process_reports(folder_path, extract_function):
    results = []
    for report_file in sorted(f for f in os.listdir(folder_path) if f.endswith('.txt')):
        file_path = os.path.join(folder_path, report_file)
        values = extract_function(file_path)
        results.append({"File": report_file, **values})
        os.remove(file_path)
    return results

@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SciRep Genie - Cardiology Research Tool</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
        <style>
        :root {
            --primary-color: #0056b3;
            --secondary-color: #f8f9fa;
            --accent-color: #17a2b8;
            --text-color: #333;
            --light-text-color: #6c757d;
        }
        body {
            font-family: 'Roboto', Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }
        .page-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            max-width: 800px;
            width: 100%;
        }
        .container, .extraction-box {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            width: 100%;
        }
        .container {
            display: flex;
            align-items: flex-start;
        }
        .logo-container {
            flex: 0 0 auto;
            margin-right: 30px;
        }
        .instructions-container {
            flex: 1 1 auto;
            text-align: left;
        }
        h2 {
            color: var(--primary-color);
            font-size: 1.8em;
            margin-bottom: 15px;
        }
        h3 {
            color: var(--primary-color);
            #font-size: 1.4em;
            #margin-bottom: 1px;
            #text-align: center;
        }
        
        h4 {
            color: var(--primary-color);
            font-size: 0.8em;
            margin-top: 0;
            #text-align: center;
        }
        h5 {
            color: var(--primary-color);
            font-size: 1.17em;
            margin-bottom: 1px;
            margin-top: 1em;
            margin-bottom: 1px;
            
        }
        input[type="file"] {
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            width: calc(100% - 22px);
            margin-bottom: 15px;
        }
        input[type="submit"] {
            background: var(--primary-color);
            border: none;
            padding: 12px 25px;
            border-radius: 5px;
            color: white;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
            width: 100%;
            margin-bottom: 15px;
        }
        input[type="submit"]:hover {
            background: var(--accent-color);
        }
        .genie-img {
            width: 160px;
            height: auto;
        }
        .step {
            margin-bottom: 15px;
            line-height: 1.6;
        }
        .step-header {
            font-weight: bold;
            color: var(--primary-color);
        }
        .made-with-love {
            font-size: 14px;
            color: var(--light-text-color);
            margin-top: 20px;
            text-align: center;
        }

        .aha-segmentation-container {
            display: flex;
            justify-content: space-between;
        }

        .aha-segmentation-half {
            width: 48%;
        }

        .aha-segmentation-half h5 {
            margin-top: 1em;
        }

        @media (max-width: 768px) {
            .aha-segmentation-container {
            flex-direction: column;
        }
        .aha-segmentation-half {
            width: 100%;
            margin-bottom: 30px;
        }
    }
        </style>
    </head>
    <body>
        <div class="page-container">
            <div class="container">
                <div class="logo-container">
                    <img src="{{ url_for('static', filename='genie.png') }}" alt="SciRep Genie Logo" class="genie-img">
                </div>
                <div class="instructions-container">
                    <h2>How to use SciRep Genie</h2>
                    <div class="step"><span class="step-header">Step 1:</span> Export your work in the "Scientific Report" format.</div>
                    <div class="step"><span class="step-header">Step 2:</span> Select and upload one or multiple scientific reports.</div>
                    <div class="step"><span class="step-header">Step 3:</span> SciRep Genie will filter relevant data into a .csv file for your analysis.</div>
                </div>
            </div>
        
            <div class="extraction-box">
                <h3>SAX Function</h3>
                <form method="POST" action="/upload_SAX_function" enctype="multipart/form-data">
                    <input type="file" name="files[]" multiple>
                    <input type="submit" value="Extract SAX Function">
                </form>
            </div>
            
            <div class="extraction-box">
                <h5>LAX Function</h5>
                <h4>Added 07/20/2024</h4>
                <form method="POST" action="/upload_LAX_function"   enctype="multipart/form-data">
                    <input type="file" name="files[]" multiple>
                    <input type="submit" value="Extract LAX Function">
                </form>
            </div>
        
            <div class="extraction-box">
                <h5>Atrial Volume (LA and RA Functions)</h5>
                <h4>Added 07/23/2024</h4>
                <form method="POST" action="/upload_atrial_volume" enctype="multipart/form-data">
                    <input type="file" name="files[]" multiple>
                    <input type="submit" value="Extract Atrial Volume">
                </form>
            </div>
            
            <div class="extraction-box">
                <h3>T1/T2 Mapping</h3>
                <form method="POST" action="/upload" enctype="multipart/form-data">
                    <input type="file" name="files[]" multiple>
                    <input type="submit" value="Extract Mapping">
                </form>
            </div>
            
            <div class="extraction-box">
                <div class="aha-segmentation-container">
                    <div class="aha-segmentation-half">
                        <h5>T1 AHA Segmentation</h5>
                        <h4>Added 07/26/2024</h4>
                        <form method="POST" action="/upload_t1_aha_segmentation" enctype="multipart/form-data">
                            <input type="file" name="files[]" multiple>
                            <input type="submit" value="Extract T1 AHA Segmentation">
                </form>
            </div>
            <div class="aha-segmentation-half">
                <h5>T2 AHA Segmentation</h5>
                <h4>Added 07/26/2024</h4>
                <form method="POST" action="/upload_t2_aha_segmentation" enctype="multipart/form-data">
                <input type="file" name="files[]" multiple>
                <input type="submit" value="Extract T2 AHA Segmentation">
            </form>
        </div>
    </div>
</div>
            
            <div class="made-with-love">
                Made with ❤️ by Kian Soroush + GPT
            </div>
    </body>
    </html>
    ''')

def handle_upload(extract_function, output_file):
    if 'files[]' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        return jsonify({"error": "No selected file"}), 400

    folder_path = 'uploads'
    os.makedirs(folder_path, exist_ok=True)

    for file in files:
        file.save(os.path.join(folder_path, file.filename))

    results = process_reports(folder_path, extract_function)

    output_path = os.path.join(folder_path, output_file)

    try:
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    except Exception as e:
        app.logger.error(f"Error writing CSV file: {e}")
        return jsonify({"error": "Error writing CSV file"}), 500

    return send_file(output_path, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload_mapping():
    return handle_upload(extract_t1_t2_values, 'extracted_mapping_values.csv')

@app.route('/upload_SAX_function', methods=['POST'])
def upload_SAX_function():
    return handle_upload(extract_SAX_function_values, 'extracted_SAX_function_values.csv')

@app.route('/upload_LAX_function', methods=['POST'])
def upload_LAX_function():
    return handle_upload(extract_LAX_function_values, 'extracted_LAX_function_values.csv')

@app.route('/upload_atrial_volume', methods=['POST'])
def upload_atrial_volume():
    return handle_upload(extract_atrial_volume_values, 'extracted_atrial_volume_values.csv')

@app.route('/upload_t1_aha_segmentation', methods=['POST'])
def upload_t1_aha_segmentation():
    return handle_upload(extract_t1_aha_segmentation_values, 'extracted_t1_aha_segmentation_values.csv')

@app.route('/upload_t2_aha_segmentation', methods=['POST'])
def upload_t2_aha_segmentation():
    return handle_upload(extract_t2_aha_segmentation_values, 'extracted_t2_aha_segmentation_values.csv')

if __name__ == '__main__':
    app.run(debug=True)
