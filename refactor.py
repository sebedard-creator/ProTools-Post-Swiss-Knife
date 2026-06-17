import os

def main():
    with open("Y:/PT SK 2.0/app.py", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Create pdf_generator.py
    pdf_lines = [
        "import os\n",
        "import tempfile\n",
        "from datetime import datetime\n",
        "from reportlab.lib.pagesizes import letter, landscape\n",
        "from reportlab.lib import colors\n",
        "from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle\n",
        "from reportlab.lib.units import inch\n",
        "from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle\n",
        "from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT\n",
        "from utils.text_utils import format_text_for_pdf, transform_track_name_for_excel, extract_clip_name_and_comment, tc_to_seconds, extract_track_code_and_actor\n\n"
    ]
    pdf_lines.extend(lines[188:334])
    pdf_lines.extend(["\n"])
    pdf_lines.extend(lines[448:488])
    pdf_lines.extend(["\n"])
    pdf_lines.extend(lines[704:1084])

    with open("Y:/PT SK 2.0/generators/pdf_generator.py", "w", encoding="utf-8") as f:
        f.writelines(pdf_lines)

    # Create new app.py
    app_lines = []
    # Lines 1-34 are imports and setup
    # But we need to add our new imports
    
    # Let's keep original imports, but we might have extra
    # We will just write a clean app.py manually
    
    new_app = """from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import zipfile
from pathlib import Path

from parsers.avid_parser import parse_cue_sheet, parse_markers
from generators.pdf_generator import create_pdf, create_markers_pdf, create_adr_acteur_pdf, create_adr_technicien_pdf
from generators.excel_generator import create_excel, create_excel_tc_order
from utils.text_utils import extract_track_code_and_actor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'your-secret-key-change-this-in-production'

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'txt', 'csv', 'edl'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

"""
    # Now we append the routes from line 1085 onwards
    app_routes = lines[1085:]
    
    with open("Y:/PT SK 2.0/app.py", "w", encoding="utf-8") as f:
        f.write(new_app)
        f.writelines(app_routes)

if __name__ == "__main__":
    main()
