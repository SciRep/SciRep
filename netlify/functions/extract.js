const { parse } = require('querystring');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { v4: uuidv4 } = require('uuid');

// This function mimics the extract_values function from your Flask app
function extractValues(data, patterns) {
  const results = {};
  
  for (const [key, pattern] of Object.entries(patterns)) {
    if (key.startsWith('AHA_Segment_')) {
      let ahaSection;
      
      if (key.includes('T1')) {
        ahaSection = data.match(/Regional Native T1 \(AHA Segmentation\)([\s\S]*?)(?=\n\n)/);
      } else if (key.includes('T2')) {
        ahaSection = data.match(/Regional (T2|CA T1) \(AHA [Ss]egmentation\)([\s\S]*?)(?=\n\n)/);
      }
      
      if (ahaSection) {
        const ahaData = key.includes('T2') ? ahaSection[0] : ahaSection[1];
        const segments = Array.from(ahaData.matchAll(/(\d+)\s+([\d.]+)/g));
        
        for (const [_, seg, value] of segments) {
          results[`${key}_${seg}`] = value;
        }
      }
    } else {
      const match = data.match(new RegExp(pattern));
      results[key] = match ? match[1] : null;
    }
  }
  
  return results;
}

// Define the patterns object from your Flask app
const patterns = {
  'SAX_function': {
    "LV EDV": "Clinical Results LV[\\s\\S]*?EDV\\s+([\\d.]+)\\s+ml",
    "LV ESV": "Clinical Results LV[\\s\\S]*?ESV\\s+([\\d.]+)\\s+ml",
    "LV EF": "Clinical Results LV[\\s\\S]*?EF\\s+([\\d.]+)\\s+%",
    "RV EDV": "Clinical Results RV[\\s\\S]*?EDV\\s+([\\d.]+)\\s+ml",
    "RV ESV": "Clinical Results RV[\\s\\S]*?ESV\\s+([\\d.]+)\\s+ml",
    "RV EF": "Clinical Results RV[\\s\\S]*?EF\\s+([\\d.]+)\\s+%"
  },
  'LAX_function': {
    "LV EDV": "Biplanar 2CV / 4CV[\\s\\S]*?EDV\\s+([\\d.]+)\\s+ml",
    "LV ESV": "Biplanar 2CV / 4CV[\\s\\S]*?ESV\\s+([\\d.]+)\\s+ml",
    "LV SV": "Biplanar 2CV / 4CV[\\s\\S]*?SV\\s+([\\d.]+)\\s+ml",
    "LV EF": "Biplanar 2CV / 4CV[\\s\\S]*?EF\\s+([\\d.]+)\\s+%",
    "CO": "Biplanar 2CV / 4CV[\\s\\S]*?CO\\s+([\\d.]+)\\s+l/min",
    "HR": "Biplanar 2CV / 4CV[\\s\\S]*?HR\\s+([\\d.]+)\\s+1/min"
  },
  // Add the rest of your patterns here
};

function processBase64File(base64Data, filename, extractionType) {
  try {
    // Remove data URL prefix if present
    const base64Content = base64Data.split(',')[1] || base64Data;
    const buffer = Buffer.from(base64Content, 'base64');
    
    // For UTF-16 encoded files, you might need to convert properly
    // This is a simple conversion that may need adjustments based on your files
    const text = buffer.toString('utf16le');
    
    // Extract values using the patterns
    const values = extractValues(text, patterns[extractionType]);
    
    return {
      File: filename,
      ...values
    };
  } catch (error) {
    console.error('Error processing file:', error);
    return { File: filename, error: 'Failed to process file' };
  }
}

// Main function handler
exports.handler = async (event, context) => {
  // Only allow POST requests
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method Not Allowed' })
    };
  }

  try {
    // Parse the incoming request
    const contentType = event.headers['content-type'];
    
    if (!contentType || !contentType.includes('application/json')) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Request must be application/json' })
      };
    }

    const requestBody = JSON.parse(event.body);
    const { files, extractionType } = requestBody;

    if (!files || !Array.isArray(files) || files.length === 0) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'No files in request' })
      };
    }

    if (!extractionType || !patterns[extractionType]) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Invalid extraction type' })
      };
    }

    // Process each file
    const results = files.map(file => {
      return processBase64File(file.content, file.name, extractionType);
    });

    // Convert results to CSV
    let csv = '';
    
    // Header row
    if (results.length > 0) {
      csv = Object.keys(results[0]).join(',') + '\\n';
      
      // Data rows
      results.forEach(row => {
        csv += Object.values(row).map(value => {
          // Handle null, undefined, or values with commas
          if (value === null || value === undefined) return '';
          return `"${String(value).replace(/"/g, '""')}"`;
        }).join(',') + '\\n';
      });
    }

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="extracted_${extractionType}_values.csv"`
      },
      body: csv
    };
  } catch (error) {
    console.error('Error processing request:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Server error processing request' })
    };
  }
};