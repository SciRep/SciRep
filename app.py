{\rtf1\ansi\ansicpg1252\cocoartf2761
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww30040\viewh16140\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 from flask import Flask, request, redirect, url_for, send_file, render_template\
import os\
import re\
import csv\
from werkzeug.utils import secure_filename\
\
app = Flask(__name__)\
app.config['UPLOAD_FOLDER'] = 'uploads'\
app.config['ALLOWED_EXTENSIONS'] = \{'txt'\}\
\
if not os.path.exists('uploads'):\
    os.makedirs('uploads')\
\
def allowed_file(filename):\
    return '.' in filename and \\\
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']\
\
def extract_t1_t2_values(file_path):\
    with open(file_path, 'r') as file:\
        data = file.read()\
\
    native_t1_global_pattern = r"Native T1[\\s\\S]*?Global Myo T1 Across Slices\\s+(\\d+\\.?\\d*)"\
    native_t1_slice1_pattern = r"Regional Native T1 Slice 1[\\s\\S]*?Myo\\s+(\\d+\\.?\\d*)"\
    native_t1_slice2_pattern = r"Regional Native T1 Slice 2[\\s\\S]*?Myo\\s+(\\d+\\.?\\d*)"\
\
    ca_t1_global_pattern = r"CA T1[\\s\\S]*?Global Myo T1 Across Slices\\s+(\\d+\\.?\\d*)"\
    ca_t1_slice1_pattern = r"Regional CA T1 Slice 1[\\s\\S]*?Myo\\s+(\\d+\\.?\\d*)"\
    ca_t1_slice2_pattern = r"Regional CA T1 Slice 2[\\s\\S]*?Myo\\s+(\\d+\\.?\\d*)"\
\
    native_t1_global = re.search(native_t1_global_pattern, data)\
    native_t1_slice1 = re.search(native_t1_slice1_pattern, data)\
    native_t1_slice2 = re.search(native_t1_slice2_pattern, data)\
\
    ca_t1_global = re.search(ca_t1_global_pattern, data)\
    ca_t1_slice1 = re.search(ca_t1_slice1_pattern, data)\
    ca_t1_slice2 = re.search(ca_t1_slice2_pattern, data)\
\
    native_t1_global_value = native_t1_global.group(1) if native_t1_global else None\
    native_t1_slice1_value = native_t1_slice1.group(1) if native_t1_slice1 else None\
    native_t1_slice2_value = native_t1_slice2.group(1) if native_t1_slice2 else None\
\
    ca_t1_global_value = ca_t1_global.group(1) if ca_t1_global else None\
    ca_t1_slice1_value = ca_t1_slice1.group(1) if ca_t1_slice1 else None\
    ca_t1_slice2_value = ca_t1_slice2.group(1) if ca_t1_slice2 else None\
\
    return \{\
        "Native Mean Global T1": native_t1_global_value,\
        "Native Mean Basal T1": native_t1_slice1_value,\
        "Native Mean Mid T1": native_t1_slice2_value,\
        "CA Mean Global T2": ca_t1_global_value,\
        "CA Mean Basal T2": ca_t1_slice1_value,\
        "CA Mean Mid T2": ca_t1_slice2_value\
    \}\
\
def process_reports(folder_path):\
    report_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]\
    results = []\
\
    for report_file in report_files:\
        file_path = os.path.join(folder_path, report_file)\
        t1_t2_values = extract_t1_t2_values(file_path)\
        results.append(\{\
            "File": report_file,\
            "Native Mean Global T1": t1_t2_values["Native Mean Global T1"],\
            "Native Mean Basal T1": t1_t2_values["Native Mean Basal T1"],\
            "Native Mean Mid T1": t1_t2_values["Native Mean Mid T1"],\
            "CA Mean Global T2": t1_t2_values["CA Mean Global T2"],\
            "CA Mean Basal T2": t1_t2_values["CA Mean Basal T2"],\
            "CA Mean Mid T2": t1_t2_values["CA Mean Mid T2"]\
        \})\
\
    return results\
\
@app.route('/')\
def upload_file():\
    return render_template('upload.html')\
\
@app.route('/uploader', methods=['POST'])\
def uploader_file():\
    if 'file' not in request.files:\
        return redirect(request.url)\
    files = request.files.getlist('file')\
    for file in files:\
        if file and allowed_file(file.filename):\
            filename = secure_filename(file.filename)\
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))\
\
    results = process_reports(app.config['UPLOAD_FOLDER'])\
\
    csv_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_t1_t2_values.csv')\
    with open(csv_file_path, 'w', newline='') as csvfile:\
        fieldnames = [\
            'File', \
            'Native Mean Global T1', 'Native Mean Basal T1', 'Native Mean Mid T1',\
            'CA Mean Global T2', 'CA Mean Basal T2', 'CA Mean Mid T2'\
        ]\
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)\
        writer.writeheader()\
        for result in results:\
            writer.writerow(result)\
\
    return send_file(csv_file_path, as_attachment=True)\
\
if __name__ == '__main__':\
    app.run(debug=True)\
}