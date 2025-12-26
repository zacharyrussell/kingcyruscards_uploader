from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import socket
from datetime import datetime
from werkzeug.utils import secure_filename
import threading
import time
from qr_window import show_qr_code
from update_checker import check_for_updates, prompt_update
from ebay_config import load_config, save_config, is_configured, load_defaults, save_defaults
from ebay_uploader import eBayUploader
app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'heic', 'heif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = secure_filename(file.filename)
        name, ext = os.path.splitext(original_filename)
        filename = f"{timestamp}_{name}{ext}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({'success': True, 'filename': filename}), 200
    
    return jsonify({'success': False, 'error': 'Invalid file type'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/images')
def list_images():
    files = []
    if os.path.exists(UPLOAD_FOLDER):
        files = [f for f in os.listdir(UPLOAD_FOLDER) 
                if allowed_file(f)]
        files.sort(reverse=True)  # Most recent first
    return jsonify({'images': files})

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'success': True}), 200
        return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ebay/config', methods=['GET', 'POST'])
def ebay_config():
    if request.method == 'GET':
        config = load_config()
        # Don't send sensitive data to client, just check if configured
        return jsonify({
            'configured': is_configured(),
            'authenticated': bool(config.get('user_token')),
            'environment': config.get('environment', 'sandbox')
        })
    
    elif request.method == 'POST':
        data = request.json
        config = {
            'app_id': data.get('app_id'),
            'dev_id': data.get('dev_id'),
            'cert_id': data.get('cert_id'),
            'environment': data.get('environment', 'sandbox')
        }
        
        if save_config(config):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to save config'}), 500

@app.route('/ebay/login')
def ebay_login():
    """Initiate eBay OAuth login"""
    try:
        uploader = eBayUploader()
        auth_url = uploader.get_auth_url()
        return jsonify({'success': True, 'auth_url': auth_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ebay/callback')
def ebay_callback():
    """Serve the redirect page that will parse the code"""
    return render_template('ebay_redirect.html')

@app.route('/ebay/exchange-token', methods=['POST'])
def exchange_token():
    """Exchange the authorization code for a token"""
    try:
        data = request.json
        code = data.get('code')
        
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400
        
        uploader = eBayUploader()
        uploader.exchange_code_for_token(code)
        
        return jsonify({'success': True})
    except Exception as e:
        import traceback
        print(f"Token exchange error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ebay/create-listing', methods=['POST'])
def create_ebay_listing():
    if not is_configured():
        return jsonify({'success': False, 'error': 'eBay not configured'}), 400
    
    try:
        data = request.json
        print(f"Received listing data: {data}")  # Debug log
        
        # Get image URLs (convert local paths to URLs)
        image_filenames = data.get('images', [])
        image_urls = [f"http://{get_local_ip()}:5000/uploads/{img}" for img in image_filenames]
        
        listing_data = {
            'title': data.get('title'),
            'description': data.get('description'),
            'price': float(data.get('price')),
            'quantity': int(data.get('quantity', 1)),
            'category_id': data.get('category_id'),
            'condition': data.get('condition', 'NEW'),
            'image_urls': image_urls
        }
        
        print(f"Creating listing with data: {listing_data}")  # Debug log
        
        uploader = eBayUploader()
        result = uploader.create_listing(listing_data)
        
        print(f"Listing created successfully: {result}")  # Debug log
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error creating listing:\n{error_trace}")  # Full error log
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/settings/defaults', methods=['GET', 'POST'])
def settings_defaults():
    if request.method == 'GET':
        defaults = load_defaults()
        return jsonify(defaults)
    
    elif request.method == 'POST':
        data = request.json
        if save_defaults(data):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to save defaults'}), 500

def run_flask():
    """Run Flask server in background thread"""
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)

if __name__ == '__main__':
    # Check for updates on startup
    print("\n🔍 Checking for updates...")
    update_info = check_for_updates()
    if update_info and update_info.get('available'):
        prompt_update(update_info)
    else:
        print("✅ You're running the latest version!\n")
    
    # Get local IP address
    local_ip = get_local_ip()
    port = 5000
    url = f"http://{local_ip}:{port}"
    
    print(f"\n{'='*50}")
    print(f"🚀 Server starting at: {url}")
    print(f"{'='*50}\n")
    
    # Run Flask in a background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Give Flask a moment to start
    time.sleep(1)
    
    # Show QR code window on main thread
    show_qr_code(url)