from flask import Flask, request, jsonify, send_file, render_template_string
import os
import re
import csv

app = Flask(__name__)

def extract_t1_t2_values(file_path):
    try:
        with open(file_path, 'r', encoding='utf-16') as file:
            data = file.read()
        
        native_t1_global_pattern = r"Native T1[\s\S]*?Global Myo T1 Across Slices\s+(\d+\.?\d*)"
        native_t1_slice1_pattern = r"Regional Native T1 Slice 1[\s\S]*?Myo\s+(\d+\.?\d*)"
        native_t1_slice2_pattern = r"Regional Native T1 Slice 2[\s\S]*?Myo\s+(\d+\.?\d*)"
        
        ca_t1_global_pattern = r"CA T1[\s\S]*?Global Myo T1 Across Slices\s+(\d+\.?\d*)"
        ca_t1_slice1_pattern = r"Regional CA T1 Slice 1[\s\S]*?Myo\s+(\d+\.?\d*)"
        ca_t1_slice2_pattern = r"Regional CA T1 Slice 2[\s\S]*?Myo\s+(\d+\.?\d*)"
        
        native_t1_global = re.search(native_t1_global_pattern, data)
        native_t1_slice1 = re.search(native_t1_slice1_pattern, data)
        native_t1_slice2 = re.search(native_t1_slice2_pattern, data)
        
        ca_t1_global = re.search(ca_t1_global_pattern, data)
        ca_t1_slice1 = re.search(ca_t1_slice1_pattern, data)
        ca_t1_slice2 = re.search(ca_t1_slice2_pattern, data)
        
        native_t1_global_value = native_t1_global.group(1) if native_t1_global else None
        native_t1_slice1_value = native_t1_slice1.group(1) if native_t1_slice1 else None
        native_t1_slice2_value = native_t1_slice2.group(1) if native_t1_slice2 else None
        
        ca_t1_global_value = ca_t1_global.group(1) if ca_t1_global else None
        ca_t1_slice1_value = ca_t1_slice1.group(1) if ca_t1_slice1 else None
        ca_t1_slice2_value = ca_t1_slice2.group(1) if ca_t1_slice2 else None
        
        return {
            "Native Mean Global T1": native_t1_global_value,
            "Native Mean Basal T1": native_t1_slice1_value,
            "Native Mean Mid T1": native_t1_slice2_value,
            "CA Mean Global T2": ca_t1_global_value,
            "CA Mean Basal T2": ca_t1_slice1_value,
            "CA Mean Mid T2": ca_t1_slice2_value
        }
    except Exception as e:
        app.logger.error(f"Error extracting T1/T2 values: {e}")
        return {}

def extract_function_values(file_path):
    try:
        with open(file_path, 'r', encoding='utf-16') as file:
            data = file.read()
        
        # Updated regex patterns to match the document structure
        lv_esv_pattern = r"ESV\s+([\d.]+)\s+ml"
        lv_edv_pattern = r"EDV\s+([\d.]+)\s+ml"
        lv_myomass_pattern = r"MyoMass_syst\s+([\d.]+)\s+g"
        
        rv_esv_pattern = r"ESV\s+([\d.]+)\s+ml"  # Assuming RV follows the same pattern
        rv_edv_pattern = r"EDV\s+([\d.]+)\s+ml"  # Assuming RV follows the same pattern
        
        lv_esv = re.search(lv_esv_pattern, data)
        lv_edv = re.search(lv_edv_pattern, data)
        lv_myomass = re.search(lv_myomass_pattern, data)
        
        rv_esv = re.search(rv_esv_pattern, data)
        rv_edv = re.search(rv_edv_pattern, data)
        
        lv_esv_value = lv_esv.group(1) if lv_esv else None
        lv_edv_value = lv_edv.group(1) if lv_edv else None
        lv_myomass_value = lv_myomass.group(1) if lv_myomass else None
        
        rv_esv_value = rv_esv.group(1) if rv_esv else None
        rv_edv_value = rv_edv.group(1) if rv_edv else None
        
        return {
            "LV ESV": lv_esv_value,
            "LV EDV": lv_edv_value,
            "LV MyoMass_syst": lv_myomass_value,
            "RV ESV": rv_esv_value,
            "RV EDV": rv_edv_value
        }
    except Exception as e:
        app.logger.error(f"Error extracting function values: {e}")
        return {}

def process_reports(folder_path, extract_function=False):
    try:
        report_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
        results = []

        for report_file in report_files:
            file_path = os.path.join(folder_path, report_file)
            if extract_function:
                values = extract_function_values(file_path)
                results.append({
                    "File": report_file,
                    "LV ESV": values.get("LV ESV"),
                    "LV EDV": values.get("LV EDV"),
                    "LV MyoMass_syst": values.get("LV MyoMass_syst"),
                    "RV ESV": values.get("RV ESV"),
                    "RV EDV": values.get("RV EDV")
                })
            else:
                values = extract_t1_t2_values(file_path)
                results.append({
                    "File": report_file,
                    "Native Mean Global T1": values.get("Native Mean Global T1"),
                    "Native Mean Basal T1": values.get("Native Mean Basal T1"),
                    "Native Mean Mid T1": values.get("Native Mean Mid T1"),
                    "CA Mean Global T2": values.get("CA Mean Global T2"),
                    "CA Mean Basal T2": values.get("CA Mean Basal T2"),
                    "CA Mean Mid T2": values.get("CA Mean Mid T2")
                })
            os.remove(file_path)  # Delete the file after processing

        return results
    except Exception as e:
        app.logger.error(f"Error processing reports: {e}")
        return []

@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Extractor</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                flex-direction: column; /* Adjust layout to column */
                position: relative; /* Add relative positioning */
            }
            /* Add styles for the made with ❤️ message */
            .made-with-love {
                position: absolute;
                bottom: 10px; /* Adjust as needed */
                right: 10px; /* Adjust as needed */
                font-size: 12px;
                color: #555;
            }
            .container {
                background: white;
                padding: 18px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                text-align: center;
                margin-bottom: 20px;
                width: 369px;

            }
            .instructions-box {
                font-size: 14px;
                background: white;
                padding: 20px;
                border-radius: 17px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                text-align: center;
                width: 369px;


            }
            h1 {
                margin-bottom: 20px;
                color: #333;
            }
            input[type="file"], input[type="submit"] {
                margin-bottom: 10px;
            }
            input[type="submit"] {
                background: #fda085;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                color: white;
                cursor: pointer;
            }
            input[type="submit"]:hover {
                background: #f6d365;
            }
            .genie-img {
                width: 100px;
                height: auto;
            }
            .instructions-box {
                text-align: left;
            }
            .step {
                margin-bottom: 10px;
            }
            .step-header {
                font-weight: bold;
                color: #333;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <img src="{{ url_for('static', filename='genie.png') }}" alt="Genie" class="genie-img">
            <h1>SciRep Genie</h1>
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <input type="file" name="files[]" multiple>
                <input type="submit" value="Extract Mapping">
            </form>
            <br>
            <form method="POST" action="/upload_function" enctype="multipart/form-data">
                <input type="file" name="files[]" multiple>
                <input type="submit" value="Extract Function">
            </form>
        </div>
        <!-- Separate Instructions Box -->      
        <div class="instructions-box">
            <h2>Instructions</h2>
            <div class="step"><span class="step-header">Step 1:</span> Export your work in the "Scientific Report" format.</div>
            <div class="step"><span class="step-header">Step 2:</span> Select and upload one or multiple scientific reports.</div>
            <div class="step"><span class="step-header">Step 3:</span> SciRep Genie will filter relevant data into a .csv file.</div>
        </div>
        <!-- Made with ❤️ message -->
        <div class="made-with-love">
            Made with ❤️ by Kian Soroush + GPT
        </div>
    </body>
    </html>
    ''')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return "No file part", 400
    files = request.files.getlist('files[]')
    if not files:
        return "No files selected", 400

    upload_folder = 'uploads'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    results = []
    try:
        for file in files:
            if file.filename == '':
                continue
            file_path = os.path.join(upload_folder, file.filename)
            file.save(file_path)
            results.extend(process_reports(upload_folder))
        
        csv_file_path = os.path.join(upload_folder, 'extracted_t1_t2_values.csv')
        with open(csv_file_path, 'w', newline='') as csvfile:
            fieldnames = [
                'File',
                'Native Mean Global T1', 'Native Mean Basal T1', 'Native Mean Mid T1',
                'CA Mean Global T2', 'CA Mean Basal T2', 'CA Mean Mid T2'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(result)
        
        return send_file(csv_file_path, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Error uploading files: {e}")
        return "Internal Server Error", 500
    finally:
        for file in files:
            try:
                os.remove(os.path.join(upload_folder, file.filename))
            except Exception as e:
                app.logger.error(f"Error deleting file: {e}")

@app.route('/upload_function', methods=['POST'])
def upload_function_files():
    if 'files[]' not in request.files:
        return "No file part", 400
    files = request.files.getlist('files[]')
    if not files:
        return "No files selected", 400

    upload_folder = 'uploads'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    results = []
    try:
        for file in files:
            if file.filename == '':
                continue
            file_path = os.path.join(upload_folder, file.filename)
            file.save(file_path)
            results.extend(process_reports(upload_folder, extract_function=True))
        
        csv_file_path = os.path.join(upload_folder, 'extracted_function_values.csv')
        with open(csv_file_path, 'w', newline='') as csvfile:
            fieldnames = [
                'File',
                'LV ESV', 'LV EDV', 'LV MyoMass_syst',
                'RV EDV', 'RV ESV'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(result)
        
        return send_file(csv_file_path, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Error uploading function files: {e}")
        return "Internal Server Error", 500
    finally:
        for file in files:
            try:
                os.remove(os.path.join(upload_folder, file.filename))
            except Exception as e:
                app.logger.error(f"Error deleting file: {e}")

if __name__ == '__main__':
    app.run(debug=True)
