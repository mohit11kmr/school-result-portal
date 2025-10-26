from flask import Flask, render_template_string, request, send_file, redirect, url_for
import pandas as pd
from fpdf import FPDF
import io
import os
import json
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration
CONFIG_FILE = "schools_config.json"
DATA_DIR = "school_data"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)

# Class-wise subjects mapping
SUBJECTS_MAPPING = {
    "Nursery": ["Math", "English", "Hindi"],
    "LKG": ["Math", "English", "Hindi"], 
    "UKG": ["Math", "English", "Hindi"],
    "I": ["Math", "English", "Hindi", "EVS", "GK", "Computer"],
    "II": ["Math", "English", "Hindi", "EVS", "GK", "Computer"],
    "III": ["Math", "English", "Hindi", "EVS", "GK", "Computer"],
    "IV": ["Math", "English", "Hindi", "EVS", "GK", "Computer"],
    "V": ["Math", "English", "Hindi", "EVS", "GK", "Computer"],
    "VI": ["Math", "English", "Hindi", "Science", "Computer", "Sanskrit"],
    "VII": ["Math", "English", "Hindi", "Science", "Computer", "Sanskrit"],
    "VIII": ["Math", "English", "Hindi", "Science", "Computer", "Sanskrit"],
    "IX": ["Math", "English", "Hindi", "Science", "Sanskrit", "SST"],
    "X": ["Math", "English", "Hindi", "Science", "Sanskrit", "SST"],
    "XI": ["Math", "English", "Hindi", "Bio", "Physics", "Chemistry", "Sanskrit", "SST"],
    "XII": ["Math", "English", "Hindi", "Bio", "Physics", "Chemistry", "Sanskrit", "SST"]
}

# HTML Templates
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>School Result Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container { 
            max-width: 800px; margin: 0 auto; background: white;
            padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 { 
            text-align: center; margin-bottom: 10px; font-size: 36px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .subtitle { text-align: center; color: #666; margin-bottom: 40px; font-size: 18px; }
        .card { 
            background: #f8f9fa; padding: 30px; border-radius: 15px; 
            margin: 20px 0; border-left: 5px solid #667eea;
        }
        .btn { 
            display: block; width: 100%; padding: 15px; text-align: center;
            background: linear-gradient(45deg, #667eea, #764ba2); color: white;
            text-decoration: none; border-radius: 10px; font-size: 18px;
            font-weight: 600; margin: 10px 0; transition: all 0.3s ease;
        }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(102,126,234,0.3); }
        .btn-school { background: linear-gradient(45deg, #27ae60, #2ecc71); }
        .btn-student { background: linear-gradient(45deg, #e74c3c, #e67e22); }
        .school-list { margin: 20px 0; }
        .school-item { 
            padding: 15px; margin: 10px 0; background: white; 
            border-radius: 10px; border-left: 4px solid #3498db;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 School Result Portal</h1>
        <div class="subtitle">Multi-School Platform - Student Results & Management</div>
        
        <div class="card">
            <h2>🏫 For Schools</h2>
            <p>Register your school and upload student results</p>
            <a href="/school_admin" class="btn btn-school">📊 School Administration</a>
        </div>

        <div class="card">
            <h2>👨‍🎓 For Students</h2>
            <p>Check your result by selecting school and academic year</p>
            <a href="/student_login" class="btn btn-student">📝 Check My Result</a>
        </div>

        {% if schools %}
        <div class="card">
            <h3>🏆 Registered Schools</h3>
            <div class="school-list">
                {% for school in schools %}
                <div class="school-item">
                    <strong>{{ school.name }}</strong><br>
                    <small>ID: {{ school.id }} | Students: {{ school.student_count }}</small>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

SCHOOL_ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>School Administration</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container { 
            max-width: 900px; margin: 0 auto; background: white;
            padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 { 
            text-align: center; margin-bottom: 10px; font-size: 32px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #555; }
        input, select { 
            width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px;
            font-size: 16px; margin-bottom: 10px;
        }
        .btn { 
            padding: 15px 30px; background: linear-gradient(45deg, #27ae60, #2ecc71);
            color: white; border: none; border-radius: 10px; cursor: pointer;
            font-size: 16px; font-weight: 600; margin: 10px 5px;
        }
        .btn-upload { background: linear-gradient(45deg, #3498db, #2980b9); }
        .success { background: #d4edda; color: #155724; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .error { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .tabs { display: flex; margin: 20px 0; }
        .tab { padding: 15px 20px; background: #f8f9fa; margin-right: 5px; cursor: pointer; border-radius: 8px 8px 0 0; }
        .tab.active { background: #3498db; color: white; }
        .tab-content { display: none; padding: 20px; background: #f8f9fa; border-radius: 0 8px 8px 8px; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏫 School Administration Panel</h1>
        <a href="/" style="padding: 10px 15px; background: #95a5a6; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; display: inline-block;">← Back to Home</a>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('register')">📝 Register School</div>
            <div class="tab" onclick="showTab('upload')">📤 Upload Results</div>
            <div class="tab" onclick="showTab('manage')">⚙️ Manage Schools</div>
        </div>

        <div id="register" class="tab-content active">
            <h3>Register New School</h3>
            <form method="POST" action="/register_school">
                <div class="form-group">
                    <label>School Name:</label>
                    <input type="text" name="school_name" required placeholder="Enter school name">
                </div>
                <div class="form-group">
                    <label>School ID (Unique):</label>
                    <input type="text" name="school_id" required placeholder="e.g., S001, DPS001">
                </div>
                <div class="form-group">
                    <label>Contact Email:</label>
                    <input type="email" name="contact_email" placeholder="school@email.com">
                </div>
                <button type="submit" class="btn">🏫 Register School</button>
            </form>
        </div>

        <div id="upload" class="tab-content">
            <h3>Upload Student Results</h3>
            <form method="POST" action="/upload_results" enctype="multipart/form-data">
                <div class="form-group">
                    <label>Select School:</label>
                    <select name="school_id" required>
                        <option value="">-- Select School --</option>
                        {% for school in schools %}
                        <option value="{{ school.id }}">{{ school.name }} ({{ school.id }})</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>Academic Year:</label>
                    <select name="academic_year" required>
                        <option value="2024-25">2024-25</option>
                        <option value="2023-24">2023-24</option>
                        <option value="2025-26">2025-26</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Term:</label>
                    <select name="term" required>
                        <option value="1st_term">1st Term</option>
                        <option value="2nd_term">2nd Term</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Upload Excel File:</label>
                    <input type="file" name="excel_file" accept=".xlsx,.xls" required>
                </div>
                <button type="submit" class="btn btn-upload">📤 Upload Results</button>
            </form>
        </div>

        <div id="manage" class="tab-content">
            <h3>Manage Schools</h3>
            {% if schools %}
                {% for school in schools %}
                <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 8px;">
                    <strong>{{ school.name }}</strong> ({{ school.id }})<br>
                    <small>Registered: {{ school.registered_date }}</small><br>
                    <a href="/delete_school/{{ school.id }}" style="color: red; text-decoration: none;">🗑️ Delete</a>
                </div>
                {% endfor %}
            {% else %}
                <p>No schools registered yet.</p>
            {% endif %}
        </div>

        {% if message %}
        <div class="{{ 'success' if message_type == 'success' else 'error' }}">{{ message }}</div>
        {% endif %}
    </div>

    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            event.currentTarget.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        }
    </script>
</body>
</html>
'''

STUDENT_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Student Result Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container { 
            max-width: 600px; margin: 0 auto; background: white;
            padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 { 
            text-align: center; margin-bottom: 10px; font-size: 32px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #555; }
        input, select { 
            width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px;
            font-size: 16px; margin-bottom: 10px;
        }
        .btn { 
            padding: 15px 30px; background: linear-gradient(45deg, #e74c3c, #e67e22);
            color: white; border: none; border-radius: 10px; cursor: pointer;
            font-size: 16px; font-weight: 600; width: 100%;
        }
        .error { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>👨‍🎓 Student Result Portal</h1>
        <p style="text-align: center; color: #666; margin-bottom: 30px;">Check your academic performance</p>
        <a href="/" style="padding: 10px 15px; background: #95a5a6; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; display: inline-block;">← Back to Home</a>
        
        <form method="POST" action="/student_result">
            <div class="form-group">
                <label>Select Your School:</label>
                <select name="school_id" required>
                    <option value="">-- Select School --</option>
                    {% for school in schools %}
                    <option value="{{ school.id }}">{{ school.name }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="form-group">
                <label>Academic Year:</label>
                <select name="academic_year" required>
                    <option value="2024-25">2024-25</option>
                    <option value="2023-24">2023-24</option>
                    <option value="2025-26">2025-26</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Enter Your Roll Number:</label>
                <input type="text" name="roll_number" required placeholder="e.g., 101, 205, 301">
            </div>
            
            <button type="submit" class="btn">🔍 Get My Result</button>
        </form>

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

STUDENT_RESULT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Student Result</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container { 
            max-width: 1000px; margin: 0 auto; background: white;
            padding: 30px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header { 
            text-align: center; margin-bottom: 30px; padding: 20px;
            background: linear-gradient(45deg, #667eea, #764ba2); color: white;
            border-radius: 15px;
        }
        table { 
            width: 100%; border-collapse: collapse; margin: 20px 0;
            background: white; border-radius: 10px; overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        th, td { border: 1px solid #e0e0e0; padding: 12px 15px; text-align: left; }
        th { background: #34495e; color: white; font-weight: 600; }
        .btn { 
            padding: 12px 25px; background: linear-gradient(45deg, #27ae60, #2ecc71);
            color: white; border: none; border-radius: 8px; cursor: pointer;
            font-size: 16px; font-weight: 600; margin: 10px 5px; text-decoration: none;
            display: inline-block;
        }
        .performance-summary { 
            background: #f8f9fa; padding: 20px; border-radius: 10px; 
            margin: 20px 0; border-left: 4px solid #3498db;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Academic Report Card</h1>
            <h3>{{ school_name }} - {{ academic_year }}</h3>
        </div>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <p><strong>Student Name:</strong> {{ student_data.name }}</p>
            <p><strong>Roll Number:</strong> {{ student_data.roll }}</p>
            <p><strong>Class:</strong> {{ student_data.class }}</p>
            <p><strong>Academic Year:</strong> {{ academic_year }}</p>
        </div>

        <h3>📊 Academic Performance</h3>
        <table>
            <tr>
                <th>Subject</th>
                <th>1st Term</th>
                <th>2nd Term</th>
                <th>Total</th>
            </tr>
            {% for subject, marks in student_data.subjects.items() %}
            <tr>
                <td>{{ subject }}</td>
                <td>{{ marks.term1 }}</td>
                <td>{{ marks.term2 }}</td>
                <td><strong>{{ marks.total }}</strong></td>
            </tr>
            {% endfor %}
            <tr style="background: #f8f9fa; font-weight: bold;">
                <td>🎯 Grand Total</td>
                <td>{{ student_data.total1 }}</td>
                <td>{{ student_data.total2 }}</td>
                <td>{{ student_data.total1 + student_data.total2 }}</td>
            </tr>
        </table>

        <div class="performance-summary">
            <h3>📈 Performance Summary</h3>
            <table>
                <tr><td>1st Term Percentage</td><td><strong style="color: #667eea;">{{ student_data.percent1 }}%</strong></td></tr>
                <tr><td>2nd Term Percentage</td><td><strong style="color: #667eea;">{{ student_data.percent2 }}%</strong></td></tr>
                <tr><td>Combined Annual Percentage</td><td><strong style="color: #27ae60; font-size: 18px;">{{ student_data.combined_percent }}%</strong></td></tr>
            </table>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <form method="POST" action="/download_result_pdf" style="display: inline;">
                <input type="hidden" name="school_id" value="{{ school_id }}">
                <input type="hidden" name="academic_year" value="{{ academic_year }}">
                <input type="hidden" name="roll_number" value="{{ student_data.roll }}">
                <button type="submit" class="btn">📥 Download PDF Report</button>
            </form>
            <a href="/student_login" class="btn" style="background: linear-gradient(45deg, #3498db, #2980b9);">🔍 Check Another Result</a>
            <a href="/" class="btn" style="background: linear-gradient(45deg, #95a5a6, #7f8c8d);">🏠 Home</a>
        </div>
    </div>
</body>
</html>
'''

# Utility Functions
def load_schools_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return []

def save_schools_config(schools):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(schools, f, indent=2)

def get_school_folder(school_id, academic_year):
    return os.path.join(DATA_DIR, school_id, academic_year)

def calculate_student_result(student1, student2, subjects_list):
    """Calculate student result from both terms"""
    subjects_data = {}
    total_term1 = 0
    total_term2 = 0
    valid_subjects_count = 0
    
    for subject in subjects_list:
        term1_mark = 0
        term2_mark = 0
        
        if not student1.empty and subject in student1.columns:
            try:
                term1_mark = float(student1[subject].iloc[0])
                if pd.isna(term1_mark):
                    term1_mark = 0
            except:
                term1_mark = 0
        
        if not student2.empty and subject in student2.columns:
            try:
                term2_mark = float(student2[subject].iloc[0])
                if pd.isna(term2_mark):
                    term2_mark = 0
            except:
                term2_mark = 0
        
        if term1_mark > 0 or term2_mark > 0:
            subjects_data[subject] = {
                'term1': term1_mark,
                'term2': term2_mark,
                'total': term1_mark + term2_mark
            }
            total_term1 += term1_mark
            total_term2 += term2_mark
            valid_subjects_count += 1
    
    # Calculate percentages
    max_marks_term1 = valid_subjects_count * 20
    max_marks_term2 = valid_subjects_count * 20
    max_marks_combined = valid_subjects_count * 40
    
    percent1 = round((total_term1 / max_marks_term1) * 100, 2) if max_marks_term1 > 0 else 0
    percent2 = round((total_term2 / max_marks_term2) * 100, 2) if max_marks_term2 > 0 else 0
    combined_percent = round(((total_term1 + total_term2) / max_marks_combined) * 100, 2) if max_marks_combined > 0 else 0
    
    return {
        'subjects': subjects_data,
        'total1': total_term1,
        'total2': total_term2,
        'percent1': percent1,
        'percent2': percent2,
        'combined_percent': combined_percent
    }

def create_pdf_report(student_data, school_name, academic_year):
    """Create professional PDF report"""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'SCHOOL REPORT CARD', 0, 1, 'C')
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, school_name, 0, 1, 'C')
    pdf.cell(0, 10, f'Academic Year: {academic_year}', 0, 1, 'C')
    pdf.ln(5)
    
    # Student Details
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Student Information:', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Name: {student_data['name']}", 0, 1)
    pdf.cell(0, 8, f"Roll No: {student_data['roll']}", 0, 1)
    pdf.cell(0, 8, f"Class: {student_data['class']}", 0, 1)
    pdf.ln(5)
    
    # Marks Table
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(80, 10, 'Subject', 1, 0, 'C')
    pdf.cell(35, 10, '1st Term', 1, 0, 'C')
    pdf.cell(35, 10, '2nd Term', 1, 0, 'C')
    pdf.cell(35, 10, 'Total', 1, 1, 'C')
    
    pdf.set_font('Arial', '', 12)
    for subject, marks in student_data['subjects'].items():
        pdf.cell(80, 10, subject, 1, 0)
        pdf.cell(35, 10, str(marks['term1']), 1, 0, 'C')
        pdf.cell(35, 10, str(marks['term2']), 1, 0, 'C')
        pdf.cell(35, 10, str(marks['total']), 1, 1, 'C')
    
    # Totals
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(80, 10, 'TOTAL', 1, 0)
    pdf.cell(35, 10, str(student_data['total1']), 1, 0, 'C')
    pdf.cell(35, 10, str(student_data['total2']), 1, 0, 'C')
    pdf.cell(35, 10, str(student_data['total1'] + student_data['total2']), 1, 1, 'C')
    
    pdf.ln(5)
    
    # Performance Summary
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Performance Summary:', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"1st Term Percentage: {student_data['percent1']}%", 0, 1)
    pdf.cell(0, 8, f"2nd Term Percentage: {student_data['percent2']}%", 0, 1)
    pdf.cell(0, 8, f"Combined Percentage: {student_data['combined_percent']}%", 0, 1)
    
    # Footer
    pdf.ln(15)
    pdf.cell(0, 8, "Principal Signature: ___________________", 0, 1)
    pdf.cell(0, 8, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1)
    
    return pdf

# Routes
@app.route('/')
def index():
    schools = load_schools_config()
    return render_template_string(INDEX_TEMPLATE, schools=schools)

@app.route('/school_admin')
def school_admin():
    schools = load_schools_config()
    return render_template_string(SCHOOL_ADMIN_TEMPLATE, schools=schools)

@app.route('/student_login')
def student_login():
    schools = load_schools_config()
    return render_template_string(STUDENT_LOGIN_TEMPLATE, schools=schools)

@app.route('/register_school', methods=['POST'])
def register_school():
    school_name = request.form.get('school_name')
    school_id = request.form.get('school_id')
    contact_email = request.form.get('contact_email', '')
    
    schools = load_schools_config()
    
    # Check if school ID already exists
    if any(school['id'] == school_id for school in schools):
        return render_template_string(SCHOOL_ADMIN_TEMPLATE, 
                                   schools=load_schools_config(),
                                   message="School ID already exists!",
                                   message_type="error")
    
    # Add new school
    new_school = {
        'id': school_id,
        'name': school_name,
        'email': contact_email,
        'registered_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'student_count': 0
    }
    
    schools.append(new_school)
    save_schools_config(schools)
    
    # Create school directory
    os.makedirs(os.path.join(DATA_DIR, school_id), exist_ok=True)
    
    return render_template_string(SCHOOL_ADMIN_TEMPLATE, 
                               schools=load_schools_config(),
                               message=f"School '{school_name}' registered successfully!",
                               message_type="success")

@app.route('/upload_results', methods=['POST'])
def upload_results():
    if 'excel_file' not in request.files:
        return render_template_string(SCHOOL_ADMIN_TEMPLATE,
                                   schools=load_schools_config(),
                                   message="No file selected!",
                                   message_type="error")
    
    file = request.files['excel_file']
    school_id = request.form.get('school_id')
    academic_year = request.form.get('academic_year')
    term = request.form.get('term')
    
    if file.filename == '':
        return render_template_string(SCHOOL_ADMIN_TEMPLATE,
                                   schools=load_schools_config(),
                                   message="No file selected!",
                                   message_type="error")
    
    try:
        # Save the file
        school_folder = get_school_folder(school_id, academic_year)
        os.makedirs(school_folder, exist_ok=True)
        
        filename = f"{term}.xlsx"
        file_path = os.path.join(school_folder, filename)
        file.save(file_path)
        
        # Update student count
        schools = load_schools_config()
        for school in schools:
            if school['id'] == school_id:
                df = pd.read_excel(file_path)
                school['student_count'] = len(df)
                break
        save_schools_config(schools)
        
        return render_template_string(SCHOOL_ADMIN_TEMPLATE,
                                   schools=load_schools_config(),
                                   message=f"Results uploaded successfully! Students: {len(df)}",
                                   message_type="success")
    
    except Exception as e:
        return render_template_string(SCHOOL_ADMIN_TEMPLATE,
                                   schools=load_schools_config(),
                                   message=f"Error uploading file: {str(e)}",
                                   message_type="error")

@app.route('/student_result', methods=['POST'])
def student_result():
    school_id = request.form.get('school_id')
    academic_year = request.form.get('academic_year')
    roll_number = request.form.get('roll_number')
    
    try:
        school_folder = get_school_folder(school_id, academic_year)
        term1_file = os.path.join(school_folder, "1st_term.xlsx")
        term2_file = os.path.join(school_folder, "2nd_term.xlsx")
        
        if not os.path.exists(term1_file) or not os.path.exists(term2_file):
            return render_template_string(STUDENT_LOGIN_TEMPLATE,
                                       schools=load_schools_config(),
                                       error="Result data not available for selected school and year")
        
        df1 = pd.read_excel(term1_file)
        df2 = pd.read_excel(term2_file)
        
        df1['Roll #'] = df1['Roll #'].astype(str)
        df2['Roll #'] = df2['Roll #'].astype(str)
        
        student1 = df1[df1['Roll #'] == roll_number]
        student2 = df2[df2['Roll #'] == roll_number]
        
        if student1.empty and student2.empty:
            return render_template_string(STUDENT_LOGIN_TEMPLATE,
                                       schools=load_schools_config(),
                                       error="Roll number not found")
        
        student_row = student1 if not student1.empty else student2
        name = student_row['Student Name'].iloc[0]
        student_class = str(student_row['Class'].iloc[0])
        
        # Get subjects based on class
        if student_class in SUBJECTS_MAPPING:
            subjects_list = SUBJECTS_MAPPING[student_class]
        else:
            metadata_cols = ['Roll #', 'Student Name', 'Class', 'Sec']
            subjects_list = [col for col in df1.columns if col not in metadata_cols]
        
        # Calculate complete result
        result_data = calculate_student_result(student1, student2, subjects_list)
        result_data.update({
            'name': name,
            'roll': roll_number,
            'class': student_class
        })
        
        # Get school name
        schools = load_schools_config()
        school_name = next((s['name'] for s in schools if s['id'] == school_id), "Unknown School")
        
        return render_template_string(STUDENT_RESULT_TEMPLATE,
                                   student_data=result_data,
                                   school_name=school_name,
                                   school_id=school_id,
                                   academic_year=academic_year)
        
    except Exception as e:
        return render_template_string(STUDENT_LOGIN_TEMPLATE,
                                   schools=load_schools_config(),
                                   error=f"Error processing result: {str(e)}")

@app.route('/download_result_pdf', methods=['POST'])
def download_result_pdf():
    school_id = request.form.get('school_id')
    academic_year = request.form.get('academic_year')
    roll_number = request.form.get('roll_number')
    
    try:
        # Get student data
        school_folder = get_school_folder(school_id, academic_year)
        term1_file = os.path.join(school_folder, "1st_term.xlsx")
        term2_file = os.path.join(school_folder, "2nd_term.xlsx")
        
        df1 = pd.read_excel(term1_file)
        df2 = pd.read_excel(term2_file)
        
        df1@app.route('/download_result_pdf', methods=['POST'])
def download_result_pdf():
    school_id = request.form.get('school_id')
    academic_year = request.form.get('academic_year')
    roll_number = request.form.get('roll_number')
    
    try:
        # Get student data
        school_folder = get_school_folder(school_id, academic_year)
        term1_file = os.path.join(school_folder, "1st_term.xlsx")
        term2_file = os.path.join(school_folder, "2nd_term.xlsx")
        
        df1 = pd.read_excel(term1_file)
        df2 = pd.read_excel(term2_file)
        
        df1['Roll #'] = df1['Roll #'].astype(str)
        df2['Roll #'] = df2['Roll #'].astype(str)
        
        student1 = df1[df1['Roll #'] == roll_number]
        student2 = df2[df2['Roll #'] == roll_number]
        
        if student1.empty and student2.empty:
            return "Student data not found", 404
        
        student_row = student1 if not student1.empty else student2
        name = student_row['Student Name'].iloc[0]
        student_class = str(student_row['Class'].iloc[0])
        
        # Get subjects based on class
        if student_class in SUBJECTS_MAPPING:
            subjects_list = SUBJECTS_MAPPING[student_class]
        else:
            metadata_cols = ['Roll #', 'Student Name', 'Class', 'Sec']
            subjects_list = [col for col in df1.columns if col not in metadata_cols]
        
        # Calculate result
        result_data = calculate_student_result(student1, student2, subjects_list)
        result_data.update({
            'name': name,
            'roll': roll_number,
            'class': student_class
        })
        
        # Get school name
        schools = load_schools_config()
        school_name = next((s['name'] for s in schools if s['id'] == school_id), "Unknown School")
        
        # Create PDF
        pdf = create_pdf_report(result_data, school_name, academic_year)
        
        # Save to bytes buffer
        pdf_buffer = io.BytesIO()
        pdf_output = pdf.output(dest='S').encode('latin-1')
        pdf_buffer.write(pdf_output)
        pdf_buffer.seek(0)
        
        filename = f"ReportCard_{school_id}_{roll_number}_{academic_year}.pdf"
        return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
        
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500

@app.route('/delete_school/<school_id>')
def delete_school(school_id):
    try:
        schools = load_schools_config()
        schools = [s for s in schools if s['id'] != school_id]
        save_schools_config(schools)
        
        # Delete school data folder
        school_folder = os.path.join(DATA_DIR, school_id)
        if os.path.exists(school_folder):
            import shutil
            shutil.rmtree(school_folder)
        
        return redirect('/school_admin')
    except Exception as e:
        return f"Error deleting school: {str(e)}", 500

# Admin Dashboard Route
@app.route('/admin_dashboard')
def admin_dashboard():
    schools = load_schools_config()
    
    # Calculate statistics
    total_students = sum(school.get('student_count', 0) for school in schools)
    active_years = set()
    
    for school in schools:
        school_folder = os.path.join(DATA_DIR, school['id'])
        if os.path.exists(school_folder):
            for year in os.listdir(school_folder):
                active_years.add(year)
    
    stats = {
        'total_schools': len(schools),
        'total_students': total_students,
        'active_years': len(active_years)
    }
    
    recent_schools = sorted(schools, key=lambda x: x.get('registered_date', ''), reverse=True)[:5]
    
    ADMIN_DASHBOARD_TEMPLATE = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                min-height: 100vh; padding: 20px;
            }
            .container { 
                max-width: 1200px; margin: 0 auto; background: white;
                padding: 30px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            .header { 
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #eee;
            }
            .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 30px 0; }
            .stat-card { 
                background: linear-gradient(45deg, #667eea, #764ba2); color: white;
                padding: 25px; border-radius: 15px; text-align: center;
            }
            .stat-number { font-size: 36px; font-weight: bold; margin-bottom: 10px; }
            .stat-label { font-size: 16px; opacity: 0.9; }
            .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin: 30px 0; }
            .action-card { padding: 20px; background: #f8f9fa; border-radius: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏫 School Admin Dashboard</h1>
                <a href="/" style="padding: 10px 20px; background: #e74c3c; color: white; 
                   text-decoration: none; border-radius: 8px;">🏠 Home</a>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{{ stats.total_schools }}</div>
                    <div class="stat-label">Total Schools</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ stats.total_students }}</div>
                    <div class="stat-label">Total Students</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ stats.active_years }}</div>
                    <div class="stat-label">Active Years</div>
                </div>
            </div>

            <div class="actions">
                <div class="action-card">
                    <h3>📊 Quick Actions</h3>
                    <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 20px;">
                        <a href="/school_admin" style="padding: 15px; background: #27ae60; color: white; 
                           text-decoration: none; border-radius: 8px; text-align: center;">🏫 Manage Schools</a>
                        <a href="/student_login" style="padding: 15px; background: #e67e22; color: white; 
                           text-decoration: none; border-radius: 8px; text-align: center;">👨‍🎓 Student Portal</a>
                    </div>
                </div>

                <div class="action-card">
                    <h3>🏆 Recent Schools</h3>
                    {% for school in recent_schools %}
                    <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 8px;
                               border-left: 4px solid #3498db;">
                        <strong>{{ school.name }}</strong><br>
                        <small>ID: {{ school.id }} | Students: {{ school.student_count }}</small>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(ADMIN_DASHBOARD_TEMPLATE, 
                                stats=stats, 
                                recent_schools=recent_schools)

if __name__ == '__main__':
    print("🚀 Starting Multi-School Result Platform...")
    print("🏫 Features: School Registration, Result Upload, Student Portal")
    print("📊 Advanced: PDF Reports, Admin Dashboard, Multi-School Support")
    app.run(debug=False)  # debug=False for production


