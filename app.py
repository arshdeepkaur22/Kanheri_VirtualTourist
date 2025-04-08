from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
import csv
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Load cave data from CSV file
CAVE_DATA = {}
try:
    with open('metadata.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            cave_id = row['cave_id']
            
            # Convert string representation of list to actual list for unique_features
            if 'unique_features' in row and row['unique_features']:
                try:
                    # Remove brackets and split by commas
                    features_str = row['unique_features'].strip('[]')
                    features_list = [feature.strip().strip("'\"") for feature in features_str.split(',')]
                    row['unique_features'] = features_list
                except:
                    row['unique_features'] = []
            else:
                row['unique_features'] = []
            
            # Add image path for each cave (necessary for feature extraction)
            row['image_path'] = f'/dataset/{cave_id}.jpg'
                
            CAVE_DATA[cave_id] = row
except FileNotFoundError:
    print("Warning: metadata.csv not found. Using default data.")
    # Fallback to some default data if the CSV doesn't exist
    CAVE_DATA = {
        'kanheri1': {
            'cave_id': 'kanheri1',
            'cave_name': 'Cave 1 (Main Chaitya)',
            'description': 'The largest and most impressive cave at Kanheri, serving as a Buddhist prayer hall (Chaitya).',
            'significance': 'Dating to the 2nd century CE, this cave represents the peak of rock-cut architecture.',
            'unique_features': ['Massive Stupa', 'Wooden-beamed ceiling', 'Intricately carved pillars'],
            'historical_period': '2nd century CE',
            'influence': 'Hinayana Buddhism with later Mahayana influences',
            'image_path': '/dataset/kanheri1.jpg'
        }
    }

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_cave_id(filename):
    """Extract the cave ID from the filename"""
    # Try to match patterns like "cave1", "kanheri1", etc.
    pattern = r'(?:cave|kanheri)(\d+)'
    match = re.search(pattern, filename.lower())
    if match:
        cave_number = match.group(1)
        return f'kanheri{cave_number}'
    return None

# Home page route
@app.route('/')
def home():
    return render_template('index.html')

# Upload page route
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Create upload folder if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Save the file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Use the improved matching function to find the cave ID
            matched_cave = extract_cave_id(filename)
            
            # Check if the matched cave exists in our data
            if matched_cave and matched_cave in CAVE_DATA:
                pass
            else:
                # If no match or not in database, default to first cave
                # Get the first cave ID from CAVE_DATA or default to 'kanheri1'
                matched_cave = next(iter(CAVE_DATA.keys())) if CAVE_DATA else 'kanheri1'
            
            return redirect(url_for('result', 
                                    uploaded_image=filename, 
                                    matched_image=matched_cave))
        
    return render_template('upload.html')

# Result page route
@app.route('/result')
def result():
    uploaded_image = request.args.get('uploaded_image')
    matched_image = request.args.get('matched_image')
    
    if not uploaded_image:
        return redirect(url_for('upload'))
    
    cave_data = {}
    if matched_image and matched_image in CAVE_DATA:
        cave_data = CAVE_DATA[matched_image]
    
    # Format unique features for display if they exist
    unique_features = cave_data.get('unique_features', [])
    unique_features_str = ", ".join(unique_features) if unique_features else ""
    
    return render_template('result.html',
                          uploaded_image=uploaded_image,
                          matched_image=matched_image,
                          cave_name=cave_data.get('cave_name', ''),
                          description=cave_data.get('description', ''),
                          significance=cave_data.get('significance', ''),
                          unique_features=unique_features_str,
                          historical_period=cave_data.get('historical_period', ''),
                          influence=cave_data.get('influence', ''))

# Live recognition route
@app.route('/live-recognition')
def live_recognition():
    return render_template('live_recognition.html')

# API Route to provide cave data for frontend
@app.route('/api/caves')
def get_caves():
    caves = []
    for cave_id, cave_data in CAVE_DATA.items():
        caves.append(cave_data)
    return jsonify(caves)

# Route to serve dataset files


# Route to serve dataset files
@app.route('/dataset/<path:filename>')
def serve_dataset(filename):
    return send_from_directory('dataset', filename)

# Route to list all available caves


# Route to view details for a specific cave


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)