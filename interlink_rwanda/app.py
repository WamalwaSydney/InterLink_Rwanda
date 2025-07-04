from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_migrate import Migrate
import os
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///youth_jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    skills = db.Column(db.String(300))
    # User's default CV and cover letter
    default_cv = db.Column(db.String(300))
    default_cover_letter = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skill_required = db.Column(db.String(200), nullable=False)
    course_link = db.Column(db.String(300))
    company = db.Column(db.String(200))
    location = db.Column(db.String(200))
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    cv_filename = db.Column(db.String(300))
    cover_letter_filename = db.Column(db.String(300))
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Public visibility for peer reviews
    is_public = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref='applications')
    job = db.relationship('Job', backref='applications')

class ApplicationReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    application = db.relationship('Application', backref='reviews')
    reviewer = db.relationship('User', backref='reviews_given')

# Helper functions
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def save_file(file, prefix="file"):
    """Save uploaded file with unique name"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{prefix}_{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return unique_filename
    return None

# Routes
@app.route('/')
def index():
    jobs = Job.query.order_by(Job.posted_at.desc()).all()
    return render_template('index.html', jobs=jobs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        skills = request.form.get('skills', '')

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return render_template('register.html')

        # Create new user
        user = User(username=username, email=email, skills=skills)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.skills = request.form.get('skills', '')

        # Handle default CV upload
        if 'default_cv' in request.files:
            cv_file = request.files['default_cv']
            if cv_file and cv_file.filename:
                # Remove old CV if exists
                if user.default_cv:
                    old_cv_path = os.path.join(app.config['UPLOAD_FOLDER'], user.default_cv)
                    if os.path.exists(old_cv_path):
                        os.remove(old_cv_path)

                user.default_cv = save_file(cv_file, "cv")

        # Handle default cover letter upload
        if 'default_cover_letter' in request.files:
            cover_file = request.files['default_cover_letter']
            if cover_file and cover_file.filename:
                # Remove old cover letter if exists
                if user.default_cover_letter:
                    old_cover_path = os.path.join(app.config['UPLOAD_FOLDER'], user.default_cover_letter)
                    if os.path.exists(old_cover_path):
                        os.remove(old_cover_path)

                user.default_cover_letter = save_file(cover_file, "cover")

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    # Get public applications for this job for peer review
    public_applications = Application.query.filter_by(job_id=job_id, is_public=True).all()
    return render_template('job_detail.html', job=job, applications=public_applications)

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply(job_id):
    job = Job.query.get_or_404(job_id)
    user = User.query.get(session['user_id'])

    # Check if user already applied
    existing_application = Application.query.filter_by(
        user_id=session['user_id'],
        job_id=job_id
    ).first()

    if existing_application:
        flash('You have already applied for this job!', 'warning')
        return redirect(url_for('job_detail', job_id=job_id))

    if request.method == 'POST':
        message = request.form['message']
        is_public = request.form.get('is_public') == 'on'

        # Handle file uploads
        cv_filename = None
        cover_letter_filename = None

        # Check if user wants to use default files
        use_default_cv = request.form.get('use_default_cv') == 'on'
        use_default_cover = request.form.get('use_default_cover') == 'on'

        if use_default_cv and user.default_cv:
            cv_filename = user.default_cv
        elif 'cv' in request.files:
            cv_file = request.files['cv']
            if cv_file and cv_file.filename:
                cv_filename = save_file(cv_file, "cv")

        if use_default_cover and user.default_cover_letter:
            cover_letter_filename = user.default_cover_letter
        elif 'cover_letter' in request.files:
            cover_file = request.files['cover_letter']
            if cover_file and cover_file.filename:
                cover_letter_filename = save_file(cover_file, "cover")

        application = Application(
            user_id=session['user_id'],
            job_id=job_id,
            message=message,
            cv_filename=cv_filename,
            cover_letter_filename=cover_letter_filename,
            is_public=is_public
        )
        db.session.add(application)
        db.session.commit()
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('my_applications'))

    return render_template('apply.html', job=job, user=user)

@app.route('/my-applications')
@login_required
def my_applications():
    applications = Application.query.filter_by(user_id=session['user_id']).order_by(Application.applied_at.desc()).all()
    return render_template('my_applications.html', applications=applications , current_time=datetime.utcnow())

@app.route('/application/<int:application_id>')
def view_application(application_id):
    application = Application.query.get_or_404(application_id)

    # Check if application is public or user owns it
    if not application.is_public and application.user_id != session.get('user_id'):
        flash('This application is private.', 'error')
        return redirect(url_for('index'))

    reviews = ApplicationReview.query.filter_by(application_id=application_id).order_by(ApplicationReview.created_at.desc()).all()

    # Check if current user has already reviewed this application
    user_review = None
    if 'user_id' in session:
        user_review = ApplicationReview.query.filter_by(
            application_id=application_id,
            reviewer_id=session['user_id']
        ).first()

    return render_template('application_detail.html', application=application, reviews=reviews, user_review=user_review)

@app.route('/review/<int:application_id>', methods=['POST'])
@login_required
def review_application(application_id):
    application = Application.query.get_or_404(application_id)

    # Check if application is public
    if not application.is_public:
        flash('This application is not available for review.', 'error')
        return redirect(url_for('index'))

    # Check if user is trying to review their own application
    if application.user_id == session['user_id']:
        flash('You cannot review your own application.', 'error')
        return redirect(url_for('view_application', application_id=application_id))

    # Check if user has already reviewed this application
    existing_review = ApplicationReview.query.filter_by(
        application_id=application_id,
        reviewer_id=session['user_id']
    ).first()

    if existing_review:
        flash('You have already reviewed this application.', 'warning')
        return redirect(url_for('view_application', application_id=application_id))

    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '')

    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating (1-5 stars).', 'error')
        return redirect(url_for('view_application', application_id=application_id))

    if not comment.strip():
        flash('Please provide a comment with your review.', 'error')
        return redirect(url_for('view_application', application_id=application_id))

    review = ApplicationReview(
        application_id=application_id,
        reviewer_id=session['user_id'],
        rating=rating,
        comment=comment
    )
    db.session.add(review)
    db.session.commit()

    flash('Review submitted successfully!', 'success')
    return redirect(url_for('view_application', application_id=application_id))

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    try:
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)
    except FileNotFoundError:
        flash('File not found.', 'error')
        return redirect(url_for('index'))

@app.route('/add-job', methods=['GET', 'POST'])
@login_required
def add_job():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        skill_required = request.form['skill_required']
        course_link = request.form.get('course_link', '')
        company = request.form.get('company', '')
        location = request.form.get('location', '')

        job = Job(
            title=title,
            description=description,
            skill_required=skill_required,
            course_link=course_link,
            company=company,
            location=location
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_job.html')

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()

        # Add sample jobs if none exist
        if Job.query.count() == 0:
            sample_jobs = [
                Job(
                    title="Junior Web Developer",
                    description="We're looking for a passionate junior web developer to join our team. You'll work on exciting projects and learn from experienced developers.",
                    skill_required="HTML, CSS, JavaScript",
                    course_link="https://freecodecamp.org/learn/responsive-web-design/",
                    company="Tech Rwanda",
                    location="Kigali, Rwanda"
                ),
                Job(
                    title="Digital Marketing Assistant",
                    description="Help us grow our online presence through social media marketing, content creation, and SEO optimization.",
                    skill_required="Social Media Marketing, Content Creation",
                    course_link="https://www.coursera.org/learn/digital-marketing",
                    company="Creative Agency",
                    location="Kigali, Rwanda"
                ),
                Job(
                    title="Data Entry Specialist",
                    description="Accurate data entry and management for our growing database. Perfect for detail-oriented individuals.",
                    skill_required="Microsoft Excel, Attention to Detail",
                    course_link="https://www.coursera.org/learn/excel-basics-data-analysis",
                    company="DataCorp Rwanda",
                    location="Kigali, Rwanda"
                ),
                Job(
                    title="Customer Service Representative",
                    description="Provide excellent customer support via phone, email, and chat. Great communication skills required.",
                    skill_required="Communication, Problem-solving",
                    course_link="https://www.coursera.org/learn/customer-service",
                    company="ServicePro Rwanda",
                    location="Kigali, Rwanda"
                )
            ]

            for job in sample_jobs:
                db.session.add(job)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)