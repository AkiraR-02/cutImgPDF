import os
import json
import tempfile
import shutil
from io import BytesIO
from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from pdf_generator import PDFReportGenerator

app = Flask(__name__, static_folder='../public', static_url_path='')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/generate', methods=['POST'])
def generate_pdf():
    # Create a temporary directory for session files
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Load and parse the config JSON
        config_str = request.form.get('config', '[]')
        elements = json.loads(config_str)
        
        # Document layout options
        page_size = request.form.get('page_size', 'LETTER').upper()
        min_split_height = int(request.form.get('min_split_height', 100))
        
        margin_left = float(request.form.get('margin_left', 54.0))
        margin_right = float(request.form.get('margin_right', 54.0))
        margin_top = float(request.form.get('margin_top', 54.0))
        margin_bottom = float(request.form.get('margin_bottom', 54.0))
        
        margins = (margin_left, margin_right, margin_top, margin_bottom)
        
        # Process files and map them in the config
        resolved_elements = []
        for el in elements:
            el_copy = el.copy()
            el_type = el_copy.get('type', '').lower()
            
            if el_type == 'image':
                file_id = el_copy.get('file_id')
                if file_id and file_id in request.files:
                    file = request.files[file_id]
                    if file.filename:
                        safe_name = secure_filename(file.filename)
                        save_path = os.path.join(temp_dir, f"{file_id}_{safe_name}")
                        file.save(save_path)
                        el_copy['path'] = save_path
                else:
                    # Fallback to default if no file was uploaded
                    el_copy['path'] = ''
                    
            elif el_type == 'double_images':
                file_id1 = el_copy.get('file_id1')
                file_id2 = el_copy.get('file_id2')
                
                # Image 1
                if file_id1 and file_id1 in request.files:
                    file1 = request.files[file_id1]
                    if file1.filename:
                        safe_name1 = secure_filename(file1.filename)
                        save_path1 = os.path.join(temp_dir, f"{file_id1}_{safe_name1}")
                        file1.save(save_path1)
                        el_copy['path1'] = save_path1
                else:
                    el_copy['path1'] = ''
                    
                # Image 2
                if file_id2 and file_id2 in request.files:
                    file2 = request.files[file_id2]
                    if file2.filename:
                        safe_name2 = secure_filename(file2.filename)
                        save_path2 = os.path.join(temp_dir, f"{file_id2}_{safe_name2}")
                        file2.save(save_path2)
                        el_copy['path2'] = save_path2
                else:
                    el_copy['path2'] = ''
            
            resolved_elements.append(el_copy)
            
        # Target output PDF file inside temp folder
        pdf_path = os.path.join(temp_dir, "output.pdf")
        
        # Instantiate engine and build PDF
        generator = PDFReportGenerator(
            output_path=pdf_path,
            page_size=page_size,
            margins=margins,
            min_split_height=min_split_height
        )
        generator.build_report(resolved_elements)
        
        # Read the generated PDF into memory
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
            
        # Clean up the entire temp directory
        shutil.rmtree(temp_dir)
        
        # Return PDF binary buffer
        output_filename = request.form.get('filename', 'reporte.pdf')
        if not output_filename.endswith('.pdf'):
            output_filename += '.pdf'
            
        return send_file(
            BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=output_filename
        )
        
    except Exception as e:
        # Clean up temp folder in case of error
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Run server locally on port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
