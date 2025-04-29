import os
import shutil
from pathlib import Path

# Create site directory
site_dir = Path('_site')
if site_dir.exists():
    shutil.rmtree(site_dir)
site_dir.mkdir()

# Copy static files
static_dir = Path('static')
shutil.copytree(static_dir, site_dir / 'static')

# Copy the main HTML file
shutil.copy('templates/index_static.html', site_dir / 'index.html')

# Copy the format template
format_dir = site_dir / 'format'
format_dir.mkdir(exist_ok=True)
shutil.copy('templates/format_template_static.html', format_dir / 'template.html')

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

# Create redirects file for Netlify
with open(site_dir / '_redirects', 'w') as f:
    f.write("""
# Redirect format pages
/format/:type /format/template.html?type=:type 200
/api/* /.netlify/functions/:splat 200
""")

print("Static site built successfully!")