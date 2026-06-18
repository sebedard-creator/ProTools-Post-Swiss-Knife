from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import zipfile
import tempfile
import io
from pathlib import Path

from parsers.avid_parser import parse_cue_sheet, parse_markers
from generators.pdf_generator import create_pdf, create_markers_pdf, create_adr_acteur_pdf, create_adr_technicien_pdf
from generators.excel_generator import create_excel, create_excel_tc_order
from utils.text_utils import extract_track_code_and_actor
from parsers.excel_parser import parse_excel_markers
from generators.aaf_generator import create_markers_aaf

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'your-secret-key-change-this-in-production'

ALLOWED_EXTENSIONS = {'txt', 'csv', 'edl', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/markers', methods=['POST'])
def export_markers():
    """Export markers from cue sheet to PDF"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and file.filename.rsplit('.', 1)[1].lower() == 'txt':
        filename = secure_filename(file.filename)
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                
                # Parse markers from cue sheet
                markers = parse_markers(filepath)
                
                if not markers:
                    flash('No markers found in the cue sheet')
                    return redirect(url_for('index'))
                
                # Use filename (without extension) as title
                title = filename.rsplit('.', 1)[0]
                
                # Generate PDF filename
                pdf_filename = f"MARKERS_{title}.pdf"
                pdf_path = os.path.join(temp_dir, pdf_filename)
                
                # Create markers PDF
                create_markers_pdf(markers, title, pdf_path)
                
                # Read into memory
                with open(pdf_path, 'rb') as f:
                    return_data = io.BytesIO(f.read())
                    
            # Send the PDF file from memory
            return send_file(return_data, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')
            
        except Exception as e:
            flash(f'Error extracting markers: {str(e)}')
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a .txt file')
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    output_format = request.form.get('format', 'spotting')  # Default to spotting
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                
                # Parse the cue sheet
                data = parse_cue_sheet(filepath)
                
                # Use filename (without extension) as title
                title = filename.rsplit('.', 1)[0]
                data['title'] = title
                
                if output_format == 'adr_recording':
                    # Generate multiple PDFs for ADR recording (zip file)
                    zip_filename = title + '_ADR_RECORDING.zip'
                    zip_path = os.path.join(temp_dir, zip_filename)
                    
                    print(f"\n=== ADR RECORDING GENERATION ===")
                    print(f"Processing {len(data['tracks'])} tracks")
                    
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for idx, track in enumerate(data['tracks'], 1):
                            # Extract track code and actor name
                            track_code, actor_name, actor_name_underscore = extract_track_code_and_actor(track['name'])
                            print(f"\nTrack {idx}: {actor_name} (Code: {track_code})")
                            
                            # Generate ACTEUR PDF
                            acteur_filename = f"{title}_{actor_name_underscore}_ACTEUR.pdf"
                            acteur_path = os.path.join(temp_dir, acteur_filename)
                            print(f"  Creating ACTEUR PDF: {acteur_filename}")
                            create_adr_acteur_pdf(track, track_code, actor_name, title, acteur_path)
                            
                            zipf.write(acteur_path, acteur_filename)
                            
                            # Generate TECHNICIEN PDF
                            tech_filename = f"{title}_{actor_name_underscore}_TECHNICIEN.pdf"
                            tech_path = os.path.join(temp_dir, tech_filename)
                            print(f"  Creating TECHNICIEN PDF: {tech_filename}")
                            create_adr_technicien_pdf(track, track_code, actor_name, title, tech_path)
                            
                            zipf.write(tech_path, tech_filename)
                    
                    # Read zip into memory
                    with open(zip_path, 'rb') as f:
                        return_data = io.BytesIO(f.read())
                        
                    return send_file(return_data, as_attachment=True, download_name=zip_filename, mimetype='application/zip')
                    
                elif output_format == 'adr':
                    # Generate Excel for ADR VALIDATION
                    excel_filename = title + '_CHARACTER_ORDER.xlsx'
                    excel_path = os.path.join(temp_dir, excel_filename)
                    create_excel(data, excel_path)
                    
                    with open(excel_path, 'rb') as f:
                        return_data = io.BytesIO(f.read())
                    return send_file(return_data, as_attachment=True, download_name=excel_filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    
                elif output_format == 'adr_tc_order':
                    # Generate Excel for ADR TC ORDER
                    excel_filename = title + '_TC_ORDER.xlsx'
                    excel_path = os.path.join(temp_dir, excel_filename)
                    create_excel_tc_order(data, excel_path)
                    
                    with open(excel_path, 'rb') as f:
                        return_data = io.BytesIO(f.read())
                    return send_file(return_data, as_attachment=True, download_name=excel_filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    
                else:
                    # Generate PDF for SPOTTING (default)
                    pdf_filename = title + '.pdf'
                    pdf_path = os.path.join(temp_dir, pdf_filename)
                    create_pdf(data, pdf_path)
                    
                    with open(pdf_path, 'rb') as f:
                        return_data = io.BytesIO(f.read())
                    return send_file(return_data, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')
                    
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a .txt file')
    return redirect(url_for('index'))

@app.route('/csv-to-edl', methods=['POST'])
def csv_to_edl():
    """Convert CSV cue sheet to EDL format"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and file.filename.rsplit('.', 1)[1].lower() == 'csv':
        filename = secure_filename(file.filename)
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                
                # Get output filename
                title = filename.rsplit('.', 1)[0]
                edl_filename = title + '.edl'
                edl_path = os.path.join(temp_dir, edl_filename)
                
                # Import and run the CSV to EDL converter
                import CSV_to_EDL
                CSV_to_EDL.csv_to_edl(filepath, edl_path)
                
                # Read into memory
                with open(edl_path, 'rb') as f:
                    return_data = io.BytesIO(f.read())
                    
            # Send the EDL file from memory
            return send_file(return_data, as_attachment=True, download_name=edl_filename, mimetype='text/plain')
            
        except Exception as e:
            flash(f'Error converting CSV to EDL: {str(e)}')
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a .csv file')
    return redirect(url_for('index'))

@app.route('/csv-to-pdf-tcorder', methods=['POST'])
def csv_to_pdf_tcorder_route():
    """Convert CSV cue sheet to a TC-ordered PDF (3 columns: TC IN / NOTE / COMMENTAIRE)"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and file.filename.rsplit('.', 1)[1].lower() == 'csv':
        filename = secure_filename(file.filename)
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                
                # Build output filename
                title = filename.rsplit('.', 1)[0]
                pdf_filename = title + '_TC_ORDER.pdf'
                pdf_path = os.path.join(temp_dir, pdf_filename)
                
                # Import and run the CSV to PDF (TC Order) converter
                import CSV_to_PDF_TCOrder
                CSV_to_PDF_TCOrder.csv_to_pdf_tcorder(filepath, pdf_path)
                
                # Read into memory
                with open(pdf_path, 'rb') as f:
                    return_data = io.BytesIO(f.read())
                    
            # Send the PDF file from memory
            return send_file(return_data, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')
            
        except Exception as e:
            flash(f'Error converting CSV to PDF: {str(e)}')
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a .csv file')
    return redirect(url_for('index'))

@app.route('/csv-to-aaf', methods=['POST'])
def csv_to_aaf():
    """Convert CSV directly to AAF format (combines CSV->EDL->AAF)"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    mode = request.form.get('mode', 'production')  # 'conception' or 'production'
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and file.filename.rsplit('.', 1)[1].lower() == 'csv':
        filename = secure_filename(file.filename)
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                
                # Get output filename with mode suffix
                title = filename.rsplit('.', 1)[0]
                edl_filename = title + '.edl'
                edl_path = os.path.join(temp_dir, edl_filename)
                
                # Step 1: Convert CSV to EDL
                import CSV_to_EDL
                CSV_to_EDL.csv_to_edl(filepath, edl_path)
                
                # Step 2: Convert EDL to AAF with mode suffix
                aaf_filename = f"{title}_{mode}.aaf"
                aaf_path = os.path.join(temp_dir, aaf_filename)
                
                import EDL_to_AAF_ProTools
                
                # Read EDL content
                edl_content = Path(edl_path).read_text(encoding='utf-8')
                frame_rate = EDL_to_AAF_ProTools.get_frame_rate(edl_content)
                session_start_tc = EDL_to_AAF_ProTools.get_session_start_tc(edl_content)
                edl_track_data = EDL_to_AAF_ProTools.parse_pts_like_edl(edl_content, frame_rate)
                
                if any(data['events'] for data in edl_track_data.values()):
                    EDL_to_AAF_ProTools.create_aaf_from_edl(
                        edl_track_data, 
                        str(aaf_path), 
                        frame_rate, 
                        session_start_tc
                    )
                else:
                    raise Exception("No valid EDL events found")
                
                # Read into memory
                with open(aaf_path, 'rb') as f:
                    return_data = io.BytesIO(f.read())
                    
            # Send the AAF file from memory
            return send_file(return_data, as_attachment=True, download_name=aaf_filename, mimetype='application/octet-stream')
            
        except Exception as e:
            flash(f'Error converting CSV to AAF: {str(e)}')
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a .csv file')
    return redirect(url_for('index'))

@app.route('/xls-to-aaf', methods=['POST'])
def xls_to_aaf():
    """Convert Excel with markers to AAF"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and file.filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx'}:
        filename = secure_filename(file.filename)
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                
                markers = parse_excel_markers(filepath)
                
                if not markers:
                    raise Exception("No valid markers found in the Excel file.")
                
                title = filename.rsplit('.', 1)[0]
                aaf_filename = f"MARKERS_{title}.aaf"
                aaf_path = os.path.join(temp_dir, aaf_filename)
                
                # Framerate is hardcoded to 23.976 as requested
                create_markers_aaf(markers, aaf_path, framerate=23.976)
                
                # Read into memory
                with open(aaf_path, 'rb') as f:
                    return_data = io.BytesIO(f.read())
                    
            # Send the AAF file from memory
            return send_file(return_data, as_attachment=True, download_name=aaf_filename, mimetype='application/octet-stream')
            
        except Exception as e:
            flash(f'Error converting Excel to AAF: {str(e)}')
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload an .xls or .xlsx file')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Get local IP address
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("\n" + "="*60)
    print("  [PROTOOLS POST SWISS KNIFE]")
    print("  Pour faire tout ce que ProTools ne fait pas.")
    print("="*60)
    print(f"\n  Access the application at:")
    print(f"  • From this computer: http://localhost:5000")
    print(f"  • From other devices:  http://{local_ip}:5000")
    print("\n  Press CTRL+C to stop the server")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
