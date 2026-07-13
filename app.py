from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
load_dotenv(override=True) 
import os
print("KEY LOADED:", os.getenv('GOOGLE_API_KEY'))  
import uuid
from datetime import datetime
import json
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import google.generativeai as genai  # ✅ FIXED: Correct import
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'cancer_detection_secret_key_2024')
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ✅ FIXED: Correct Gemini API configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Gemini API configured successfully.")
else:
    logger.warning("GOOGLE_API_KEY is not set. Gemini chat endpoint will fail until set.")

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'dcm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    """Get database connection"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'Sachin2609@'),
            database=os.getenv('DB_NAME', 'cancer_app'),
            auth_plugin='mysql_native_password'
        )
        return conn
    except mysql.connector.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                age INT NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                password VARCHAR(255) NOT NULL,
                profile_picture VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        # Create assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id VARCHAR(50) NOT NULL,
                assessment_id VARCHAR(100) UNIQUE NOT NULL,
                assessment_data JSON NOT NULL,
                risk_score FLOAT NOT NULL,
                results JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES users(patient_id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute("""
            SELECT COUNT(1)
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'assessments'
                AND INDEX_NAME = 'idx_patient_id'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute('CREATE INDEX idx_patient_id ON assessments(patient_id)')
            cursor.execute('CREATE INDEX idx_created_at ON assessments(created_at)')
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Database initialized successfully")

def allowed_file(filename):
    """Check if file type is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database when app starts
init_database()

# ─────────────────────────────────────────────
#  Page Routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/auth')
    return render_template('dashboard.html')

@app.route('/assessment')
def assessment():
    if 'user_id' not in session:
        return redirect('/auth')
    return render_template('assessment.html')

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect('/auth')
    return render_template('results.html')

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect('/auth')
    return render_template('history.html')

@app.route('/tracker')
def tracker():
    if 'user_id' not in session:
        return redirect('/auth')
    return render_template('tracker.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/auth')
    return render_template('profile.html')

@app.route('/image-analysis')
def image_analysis():
    if 'user_id' not in session:
        return redirect('/auth')
    return render_template('image_analysis.html')

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect('/auth')
    return render_template('chat.html')

# ─────────────────────────────────────────────
#  API Routes
# ─────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    """Handle user registration"""
    try:
        data = request.json
        name = data.get('name')
        age = data.get('age')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        
        if not all([name, age, email, phone, password]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        patient_id = f"PT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (patient_id, name, age, email, phone, password)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (patient_id, name, age, email, phone, hashed_password))
            
            conn.commit()
            session['user_id'] = patient_id
            session['user_name'] = name
            
            logger.info(f"New user registered: {patient_id}")
            
            return jsonify({
                'success': True,
                'message': 'Registration successful',
                'patient_id': patient_id,
                'user': {'name': name, 'patient_id': patient_id}
            })
            
        except mysql.connector.IntegrityError:
            return jsonify({'success': False, 'message': 'Email already exists'}), 400
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'success': False, 'message': 'Registration failed'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Handle user login"""
    try:
        data = request.json
        patient_id = data.get('patient_id')
        password = data.get('password')
        
        if not patient_id or not password:
            return jsonify({'success': False, 'message': 'Patient ID and password are required'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE patient_id = %s', (patient_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['patient_id']
            session['user_name'] = user['name']
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'name': user['name'],
                    'patient_id': user['patient_id'],
                    'email': user['email'],
                    'age': user['age']
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid Patient ID or Password'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Login failed'}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze cancer risk"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        data = request.json
        patient_id = session['user_id']
        
        risk_score = calculate_risk_score(data)
        assessment_id = str(uuid.uuid4())
        results = generate_results(risk_score, data)
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO assessments (patient_id, assessment_id, assessment_data, risk_score, results)
            VALUES (%s, %s, %s, %s, %s)
        ''', (patient_id, assessment_id, json.dumps(data), risk_score, json.dumps(results)))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Assessment saved for patient: {patient_id}, risk: {risk_score}%")
        
        return jsonify({
            'success': True,
            'assessment_id': assessment_id,
            'risk_score': risk_score,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'success': False, 'message': 'Analysis failed'}), 500

@app.route('/api/history/<patient_id>')
def get_history(patient_id):
    """Get patient assessment history"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT assessment_id, assessment_data, risk_score, results, created_at
            FROM assessments 
            WHERE patient_id = %s 
            ORDER BY created_at DESC
        ''', (patient_id,))
        
        assessments = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for assessment in assessments:
            assessment['assessment_data'] = json.loads(assessment['assessment_data'])
            assessment['results'] = json.loads(assessment['results'])
        
        return jsonify({'success': True, 'assessments': assessments})
        
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch history'}), 500

@app.route('/api/user/profile')
def get_user_profile():
    """Get user profile data"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT name, age, email, phone, patient_id, profile_picture, created_at
            FROM users WHERE patient_id = %s
        ''', (session['user_id'],))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({'success': True, 'user': user})
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch profile'}), 500

@app.route('/api/user/update', methods=['POST'])
def update_user_profile():
    """Update user profile"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        data = request.json
        name = data.get('name')
        age = data.get('age')
        email = data.get('email')
        phone = data.get('phone')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET name = %s, age = %s, email = %s, phone = %s 
            WHERE patient_id = %s
        ''', (name, age, email, phone, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        session['user_name'] = name
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except mysql.connector.IntegrityError:
        return jsonify({'success': False, 'message': 'Email already exists'}), 400
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return jsonify({'success': False, 'message': 'Profile update failed'}), 500

@app.route('/api/upload-report', methods=['POST'])
def upload_report():
    """Upload X-ray or medical report"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{session['user_id']}_{int(datetime.now().timestamp())}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'message': 'Database connection failed'}), 500

            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS uploads (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_id VARCHAR(50) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES users(patient_id) ON DELETE CASCADE
                )
            ''')
            cursor.execute(
                'INSERT INTO uploads (patient_id, filename) VALUES (%s, %s)',
                (session['user_id'], unique_filename)
            )
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({
                'success': True,
                'message': 'Report uploaded successfully',
                'file_path': f"/static/uploads/{unique_filename}"
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400

    except Exception as e:
        logger.error(f"Report upload error: {e}")
        return jsonify({'success': False, 'message': 'Upload failed'}), 500

@app.route('/api/logout')
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})


# ✅ FIXED: Correct Gemini API chat endpoint
@app.route('/api/chat', methods=['POST'])
def chat_with_gemini():
    """Send a message to Google Gemini 2.0 Flash and return the response"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    prompt = request.json.get('message', '').strip()
    if not prompt:
        return jsonify({'success': False, 'message': 'Message is required'}), 400

    if not GOOGLE_API_KEY:
        return jsonify({'success': False, 'message': 'Gemini API key not configured on server'}), 500

    try:
        # ✅ Correct way to use Gemini API
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,   # 'gemini-2.0-flash'
            system_instruction=(
                "You are a cancer-support assistant. "
                "Provide helpful, empathetic medical information and always encourage "
                "the user to consult a qualified healthcare professional for diagnosis "
                "and treatment decisions."
            )
        )

        response = model.generate_content(prompt)
        assistant_text = response.text

        logger.info(f"Gemini response generated for user: {session['user_id']}")
        return jsonify({'success': True, 'message': assistant_text})

    except Exception as e:
        logger.error(f"Gemini chat error: {e}")
        return jsonify({'success': False, 'message': f'Gemini chat failed: {str(e)}'}), 500


# ─────────────────────────────────────────────
#  Utility Functions
# ─────────────────────────────────────────────

def calculate_risk_score(data):
    """Calculate cancer risk score based on inputs"""
    score = 0
    
    age = int(data.get('age', 0))
    if age > 50:
        score += 25
    elif age > 40:
        score += 15
    elif age > 30:
        score += 5
    
    symptoms = data.get('symptoms', [])
    score += len(symptoms) * 8
    
    smoking = data.get('smoking', 'never')
    if smoking == 'current':
        score += 25
    elif smoking == 'former':
        score += 10
    
    alcohol = data.get('alcohol', 'never')
    if alcohol == 'current':
        score += 15
    elif alcohol == 'former':
        score += 5
    
    weight = float(data.get('weight', 0))
    height = float(data.get('height', 1))
    if height > 0:
        bmi = weight / ((height / 100) ** 2)
        if bmi > 30:
            score += 10
        elif bmi > 25:
            score += 5
    
    wbc = float(data.get('wbc', 0))
    if wbc > 11000:
        score += 10
    
    rbc = float(data.get('rbc', 0))
    if rbc < 4.0:
        score += 5
    
    platelets = float(data.get('platelets', 0))
    if platelets < 150000:
        score += 5
    
    pain_level = int(data.get('pain_level', 0))
    score += pain_level * 2
    
    if data.get('family_history', False):
        score += 15
    
    return min(score, 100)

def generate_results(risk_score, data):
    """Generate results based on risk score"""
    if risk_score > 50:
        cancer_type = "High Risk - Multiple Types Possible"
        stage = "Requires Further Diagnosis"
        risk_description = "Based on your inputs, you have a high risk of cancer. Please consult with a healthcare professional immediately."
        recommendations = {
            "monitoring": "Monthly self-examinations, Quarterly doctor visits, Immediate specialist consultation",
            "diet": "Turmeric, Green Tea, Berries, Broccoli, Tomatoes, Walnuts, Dark Chocolate, Olive Oil, Leafy Greens",
            "doctors": ["Oncologist", "Primary Care Physician", "Specialist based on symptoms", "Nutritionist"],
            "tests": ["CT Scan", "MRI", "Biopsy", "Complete Blood Work", "Cancer Marker Tests", "Genetic Testing"]
        }
    elif risk_score > 30:
        cancer_type = "Moderate Risk"
        stage = "Early Detection Recommended"
        risk_description = "Based on your inputs, you have a moderate risk of cancer. Consider lifestyle changes and regular screenings."
        recommendations = {
            "monitoring": "Quarterly check-ups, Annual screenings, Regular self-exams, Lifestyle monitoring",
            "diet": "Balanced diet with fruits and vegetables, Limit processed foods, Increase fiber intake, Reduce red meat",
            "doctors": ["Primary Care Physician", "Nutritionist", "Preventive care specialist"],
            "tests": ["Annual physical", "Age-appropriate screenings", "Blood tests", "Basic imaging if needed"]
        }
    else:
        cancer_type = "Low Risk"
        stage = "No Cancer Detected"
        risk_description = "Based on your inputs, you have a low risk of cancer. Maintain your healthy lifestyle."
        recommendations = {
            "monitoring": "Annual health check-ups, Regular exercise routine, Healthy lifestyle maintenance",
            "diet": "Maintain healthy lifestyle, Balanced nutrition, Regular hydration, Portion control",
            "doctors": ["Primary Care Physician for routine check-ups"],
            "tests": ["Routine blood tests", "Basic health screening", "Preventive care tests"]
        }
    
    return {
        'cancer_type': cancer_type,
        'stage': stage,
        'risk_percentage': risk_score,
        'risk_description': risk_description,
        'recommendations': recommendations,
        'patient_name': data.get('name', ''),
        'patient_age': data.get('age', ''),
        'assessment_date': datetime.now().isoformat()
    }


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    print("🚀 Cancer Detection System Starting...")
    print(f"🤖 Gemini Model: {GEMINI_MODEL}")
    print("📊 Database initialized")
    print("🌐 Server ready at http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)