#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path

print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

try:
    # Create site directory
    site_dir = Path('_site')
    if site_dir.exists():
        shutil.rmtree(site_dir)
    site_dir.mkdir()
    print(f"Created site directory: {site_dir}")

    # Copy static files
    static_dir = Path('static')
    if not static_dir.exists():
        print(f"Warning: Static directory not found at {static_dir}")
        static_dir.mkdir(exist_ok=True)
    shutil.copytree(static_dir, site_dir / 'static')
    print("Copied static files")

    # Copy the main HTML file
    # Choose the appropriate template based on environment variable
    if os.environ.get('DEPLOY_TARGET') == 'netlify':
        index_path = Path('templates/index_static.html')
    else:
        # Default to GitHub Pages
        index_path = Path('templates/index_for_github.html')

    if not index_path.exists():
        print(f"Error: Index file not found at {index_path}")
        print("Files in templates directory:")
        for f in Path('templates').glob('*'):
            print(f"  {f}")
        raise FileNotFoundError(f"Index file not found: {index_path}")
    
    shutil.copy(index_path, site_dir / 'index.html')
    print(f"Copied index.html from {index_path}")

    # Copy the format template
    format_dir = site_dir / 'format'
    format_dir.mkdir(exist_ok=True)
    
    # Choose the appropriate template based on environment variable
    if os.environ.get('DEPLOY_TARGET') == 'netlify':
        template_path = Path('templates/format_template_static.html')
    else:
        # Default to GitHub Pages
        template_path = Path('templates/format_template_for_github.html')
        
    if not template_path.exists():
        print(f"Warning: Format template not found at {template_path}")
        print("Using simplified template instead")
        with open(format_dir / 'template.html', 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Format Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <h1 id="title">Format Viewer</h1>
    <div id="content"></div>
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const type = urlParams.get('type');
        document.getElementById('title').textContent = type || 'Format Viewer';
        
        if (type) {
            fetch(`../static/format_${type}_1.txt`)
                .then(response => response.text())
                .then(text => {
                    document.getElementById('content').innerHTML = `<pre>${text}</pre>`;
                })
                .catch(err => {
                    document.getElementById('content').innerHTML = 
                        `<p>Error loading format: ${err.message}</p>`;
                });
        }
    </script>
</body>
</html>""")
    else:
        shutil.copy(template_path, format_dir / 'template.html')
    print("Created format template")

    # Create placeholders for the formats
    for format_type in ['SAX_function', 'LAX_function', 'atrial_volume', 'mapping', 
                        't1_aha_segmentation', 't2_aha_segmentation']:
        with open(format_dir / f'{format_type}.html', 'w') as f:
            title = f"{format_type.replace('_', ' ').title()}"
            title = title.replace('Aha', 'AHA').replace('Sax', 'SAX').replace('Lax', 'LAX')
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta http-equiv="refresh" content="0;url=/format/template.html?type={format_type}">
</head>
<body>
    <p>Redirecting to format viewer...</p>
</body>
</html>
""")
    print("Created format placeholders")

    # Create redirects file for Netlify
    with open(site_dir / '_redirects', 'w') as f:
        f.write("""
# Redirect format pages
/format/:type /format/template.html?type=:type 200
/api/* /.netlify/functions/:splat 200
""")
    print("Created Netlify redirects")

    print("Static site built successfully!")
    sys.exit(0)

except Exception as e:
    print(f"Error building site: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)