from flask import Flask, request, jsonify, send_file, render_template_string
import os
import re
import csv
from functools import partial

app = Flask(__name__)

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

