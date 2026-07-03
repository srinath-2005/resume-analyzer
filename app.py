import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# Import custom core modules
from resume_parser import extract_text
from nlp_utils import extract_contact_info, extract_sections
from skill_extractor import extract_skills
from recommender import analyze_resume_full

app = Flask(__name__)
app.secret_key = 'smart-resume-selector-secret'

# Database Configuration (Supports environment DB URLs in production)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_uri = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "data.db")}')
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File Upload Configuration
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}

db = SQLAlchemy(app)

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------------------------------------------
# DATABASE MODELS
# ----------------------------------------------------

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text, default='[]')  # Stored as JSON list of strings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to MatchResults
    matches = db.relationship('MatchResult', backref='job', cascade='all, delete-orphan')

class Resume(db.Model):
    __tablename__ = 'resumes'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    candidate_name = db.Column(db.String(120), default='Unknown')
    email = db.Column(db.String(120), default='')
    phone = db.Column(db.String(50), default='')
    skills = db.Column(db.Text, default='[]')  # Stored as JSON list of strings
    sections = db.Column(db.Text, default='{}')  # Stored as JSON dictionary of section texts
    text_content = db.Column(db.Text, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to MatchResults
    matches = db.relationship('MatchResult', backref='resume', cascade='all, delete-orphan')

class MatchResult(db.Model):
    __tablename__ = 'match_results'
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=True)  # Nullable for ad-hoc student matching
    ats_score = db.Column(db.Float, nullable=False)
    text_similarity = db.Column(db.Float, nullable=False)
    skill_overlap_score = db.Column(db.Float, nullable=False)
    matched_skills = db.Column(db.Text, default='[]')  # JSON list
    missing_skills = db.Column(db.Text, default='[]')  # JSON list
    suggestions = db.Column(db.Text, default='[]')  # JSON list of dicts
    rewrites = db.Column(db.Text, default='[]')  # JSON list of dicts
    matched_at = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------------------------------------
# ROUTES & CONTROLLERS
# ----------------------------------------------------

@app.route('/')
def index():
    """
    Landing Page.
    """
    return render_template('index.html')

@app.route('/student')
def student_dashboard():
    """
    Student View.
    Allows students to upload resume and analyze it against standard jobs or custom JD.
    """
    # Fetch available company job positions for the dropdown selection
    active_jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template('student.html', jobs=active_jobs)

@app.route('/student/analyze', methods=['POST'])
def student_analyze():
    """
    API endpoint: parses resume and returns direct analysis JSON back to frontend dashboard.
    """
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file uploaded.'}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file format. Please upload PDF, DOCX or TXT.'}), 400
        
    # Get job description text from form
    jd_type = request.form.get('jd_type')  # 'custom' or 'preset'
    jd_text = ""
    job_id = None
    
    if jd_type == 'preset':
        job_id_val = request.form.get('job_id')
        if job_id_val:
            job = Job.query.get(job_id_val)
            if job:
                jd_text = job.description
                job_id = job.id
    else:
        jd_text = request.form.get('custom_jd', '').strip()
        
    if not jd_text:
        return jsonify({'error': 'Job description cannot be empty.'}), 400
        
    try:
        # Save resume file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 1. Extract Text
        raw_text = extract_text(file_path)
        if not raw_text.strip():
            return jsonify({'error': 'Unable to extract text from the file. Ensure the file is not corrupt or scanned image PDF.'}), 400
            
        # 2. Extract Contact Info & Candidate Name
        contact_info = extract_contact_info(raw_text)
        
        # Determine candidate name from first line or email handle
        first_line = [l.strip() for l in raw_text.split('\n') if l.strip()][:1]
        name = first_line[0] if first_line else "Candidate"
        if len(name) > 50 or '@' in name:
            name = contact_info['email'].split('@')[0].title() if contact_info['email'] else "Candidate"
            
        # 3. Extract sections & skills
        sections = extract_sections(raw_text)
        skills_info = extract_skills(raw_text)
        
        # 4. Perform Matching and Recommendations
        analysis_report = analyze_resume_full(raw_text, jd_text)
        
        # 5. Store Resume and Match Result in DB (so we can access history)
        new_resume = Resume(
            filename=filename,
            candidate_name=name,
            email=contact_info['email'],
            phone=contact_info['phone'],
            skills=json.dumps(skills_info['skills']),
            sections=json.dumps(sections),
            text_content=raw_text
        )
        db.session.add(new_resume)
        db.session.commit() # Commit to get resume ID
        
        match_res = MatchResult(
            resume_id=new_resume.id,
            job_id=job_id,
            ats_score=analysis_report['ats_score'],
            text_similarity=analysis_report['text_similarity'],
            skill_overlap_score=analysis_report['skill_overlap_score'],
            matched_skills=json.dumps(analysis_report['matched_skills']),
            missing_skills=json.dumps(analysis_report['missing_skills']),
            suggestions=json.dumps(analysis_report['recommendations']),
            rewrites=json.dumps(analysis_report['sentence_rewrites'])
        )
        db.session.add(match_res)
        db.session.commit()
        
        # Return full report
        return jsonify({
            'success': True,
            'match_id': match_res.id,
            'report': analysis_report,
            'contact': {
                'name': name,
                'email': contact_info['email'],
                'phone': contact_info['phone']
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'An error occurred during analysis: {str(e)}'}), 500

@app.route('/company')
def company_dashboard():
    """
    Company View.
    Shows the job postings and general resume parsing repository.
    """
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    # Count of candidates parsed in total
    candidate_count = Resume.query.count()
    return render_template('company.html', jobs=jobs, candidate_count=candidate_count)

@app.route('/company/job/create', methods=['POST'])
def create_job():
    """
    Creates a new job description, automatically extracting key skills.
    """
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    
    if not title or not description:
        flash('Job title and description are required.', 'danger')
        return redirect(url_for('company_dashboard'))
        
    # Extract skills required automatically using skill extractor
    skills_info = extract_skills(description)
    required_skills = skills_info['skills']
    
    try:
        new_job = Job(
            title=title,
            description=description,
            required_skills=json.dumps(required_skills)
        )
        db.session.add(new_job)
        db.session.commit()
        flash(f"Job posting '{title}' created successfully!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating job: {str(e)}", 'danger')
        
    return redirect(url_for('company_dashboard'))

@app.route('/company/job/<int:job_id>')
def view_job(job_id):
    """
    Renders detailed page for a job post, displaying ranked candidate list.
    """
    job = Job.query.get_or_404(job_id)
    required_skills = json.loads(job.required_skills)
    
    # Query all matches against this specific job ID, sorted by ATS score descending
    matches = MatchResult.query.filter_by(job_id=job.id).order_by(MatchResult.ats_score.desc()).all()
    
    return render_template('job_detail.html', job=job, required_skills=required_skills, matches=matches)

@app.route('/company/job/<int:job_id>/upload', methods=['POST'])
def upload_resumes_for_job(job_id):
    """
    Bulk uploads multiple resumes for a single job description.
    """
    job = Job.query.get_or_404(job_id)
    
    if 'resumes' not in request.files:
        flash('No files uploaded.', 'danger')
        return redirect(url_for('view_job', job_id=job.id))
        
    files = request.files.getlist('resumes')
    if not files or files[0].filename == '':
        flash('No files selected.', 'danger')
        return redirect(url_for('view_job', job_id=job.id))
        
    success_count = 0
    error_count = 0
    
    for file in files:
        if file and allowed_file(file.filename):
            try:
                # Save file
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Extract details
                raw_text = extract_text(file_path)
                contact_info = extract_contact_info(raw_text)
                
                # Determine name
                first_line = [l.strip() for l in raw_text.split('\n') if l.strip()][:1]
                name = first_line[0] if first_line else "Candidate"
                if len(name) > 50 or '@' in name:
                    name = contact_info['email'].split('@')[0].title() if contact_info['email'] else "Candidate"
                    
                sections = extract_sections(raw_text)
                skills_info = extract_skills(raw_text)
                
                # Run analyzer against this specific job's description
                analysis_report = analyze_resume_full(raw_text, job.description)
                
                # Save to database
                new_resume = Resume(
                    filename=filename,
                    candidate_name=name,
                    email=contact_info['email'],
                    phone=contact_info['phone'],
                    skills=json.dumps(skills_info['skills']),
                    sections=json.dumps(sections),
                    text_content=raw_text
                )
                db.session.add(new_resume)
                db.session.commit()
                
                new_match = MatchResult(
                    resume_id=new_resume.id,
                    job_id=job.id,
                    ats_score=analysis_report['ats_score'],
                    text_similarity=analysis_report['text_similarity'],
                    skill_overlap_score=analysis_report['skill_overlap_score'],
                    matched_skills=json.dumps(analysis_report['matched_skills']),
                    missing_skills=json.dumps(analysis_report['missing_skills']),
                    suggestions=json.dumps(analysis_report['recommendations']),
                    rewrites=json.dumps(analysis_report['sentence_rewrites'])
                )
                db.session.add(new_match)
                db.session.commit()
                success_count += 1
            except Exception as e:
                db.session.rollback()
                print(f"Error bulk uploading resume {file.filename}: {e}")
                error_count += 1
        else:
            error_count += 1
            
    flash(f"Successfully processed {success_count} resumes. Errors: {error_count}", 'info')
    return redirect(url_for('view_job', job_id=job.id))

@app.route('/api/match/<int:match_id>')
def get_match_api(match_id):
    """
    JSON API returning complete detailed stats for a single MatchResult record.
    Used for overlay modal displays.
    """
    match_val = MatchResult.query.get_or_404(match_id)
    resume_val = Resume.query.get(match_val.resume_id)
    
    # Load JSON fields safely
    try:
        matched_skills = json.loads(match_val.matched_skills)
        missing_skills = json.loads(match_val.missing_skills)
        suggestions = json.loads(match_val.suggestions)
        rewrites = json.loads(match_val.rewrites)
        all_resume_skills = json.loads(resume_val.skills)
        sections = json.loads(resume_val.sections)
    except Exception:
        matched_skills = []
        missing_skills = []
        suggestions = []
        rewrites = []
        all_resume_skills = []
        sections = {}
        
    return jsonify({
        'id': match_val.id,
        'candidate_name': resume_val.candidate_name,
        'email': resume_val.email,
        'phone': resume_val.phone,
        'filename': resume_val.filename,
        'ats_score': match_val.ats_score,
        'text_similarity': match_val.text_similarity,
        'skill_overlap_score': match_val.skill_overlap_score,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'all_resume_skills': all_resume_skills,
        'suggestions': suggestions,
        'rewrites': rewrites,
        'sections': {
            'experience': sections.get('experience', ''),
            'education': sections.get('education', ''),
            'projects': sections.get('projects', '')
        }
    })

# ----------------------------------------------------
# DATABASE INITIALIZATION
# ----------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
