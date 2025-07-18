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
    role = db.Column(db.String(20), nullable=False, default='job_seeker')  # 'job_seeker' or 'job_provider'

    # Job seeker specific fields
    skills = db.Column(db.String(300))
    default_cv = db.Column(db.String(300))
    default_cover_letter = db.Column(db.String(300))

    # Job provider specific fields
    company_name = db.Column(db.String(200))
    company_description = db.Column(db.Text)
    company_website = db.Column(db.String(300))
    company_location = db.Column(db.String(200))
    contact_person = db.Column(db.String(200))
    contact_phone = db.Column(db.String(20))

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
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to job provider
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Job requirements
    experience_level = db.Column(db.String(50), default='Entry Level')
    employment_type = db.Column(db.String(50), default='Full-time')
    salary_range = db.Column(db.String(100))

    poster = db.relationship('User', backref='posted_jobs')
    applications = db.relationship('Application', backref='job', lazy=True)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    cv_filename = db.Column(db.String(300))
    cover_letter_filename = db.Column(db.String(300))
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # pending, reviewed, accepted, rejected

    # Public visibility for peer reviews
    is_public = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref='applications')

class ApplicationReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    application = db.relationship('Application', backref='reviews')
    reviewer = db.relationship('User', backref='reviews_given')


def get_current_user():
    """Get the current logged-in user"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@app.context_processor
def inject_user():
    return dict(get_current_user=get_current_user)

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

def job_provider_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])
        if user.role != 'job_provider':
            flash('Access denied. Job providers only.', 'error')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function

def job_seeker_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])
        if user.role != 'job_seeker':
            flash('Access denied. Job seekers only.', 'error')
            return redirect(url_for('index'))

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

@app.route('/register')
def register():
    return render_template('register_choice.html')

@app.route('/register/job-seeker', methods=['GET', 'POST'])
def register_job_seeker():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        skills = request.form.get('skills', '')

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('register_job_seeker.html')

        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return render_template('register_job_seeker.html')

        # Create new job seeker
        user = User(
            username=username,
            email=email,
            skills=skills,
            role='job_seeker'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register_job_seeker.html')

@app.route('/register/job-provider', methods=['GET', 'POST'])
def register_job_provider():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        company_name = request.form['company_name']
        company_description = request.form.get('company_description', '')
        company_website = request.form.get('company_website', '')
        company_location = request.form.get('company_location', '')
        contact_person = request.form.get('contact_person', '')
        contact_phone = request.form.get('contact_phone', '')

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('register_job_provider.html')

        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return render_template('register_job_provider.html')

        # Create new job provider
        user = User(
            username=username,
            email=email,
            role='job_provider',
            company_name=company_name,
            company_description=company_description,
            company_website=company_website,
            company_location=company_location,
            contact_person=contact_person,
            contact_phone=contact_phone
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register_job_provider.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role
            flash('Login successful!', 'success')

            # Redirect based on role
            if user.role == 'job_provider':
                return redirect(url_for('provider_dashboard'))
            else:
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
        if user.role == 'job_seeker':
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

        elif user.role == 'job_provider':
            user.company_name = request.form.get('company_name', '')
            user.company_description = request.form.get('company_description', '')
            user.company_website = request.form.get('company_website', '')
            user.company_location = request.form.get('company_location', '')
            user.contact_person = request.form.get('contact_person', '')
            user.contact_phone = request.form.get('contact_phone', '')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/provider/dashboard')
@job_provider_required
def provider_dashboard():
    user = User.query.get(session['user_id'])
    posted_jobs = Job.query.filter_by(posted_by=user.id).order_by(Job.posted_at.desc()).all()

    # Get all applications for this provider's jobs
    job_ids = [job.id for job in posted_jobs]
    applications = Application.query.filter(Application.job_id.in_(job_ids)).order_by(Application.applied_at.desc()).all()

    return render_template('provider_dashboard.html',
                         user=user,
                         posted_jobs=posted_jobs,
                         applications=applications)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    # Get public applications for this job for peer review
    public_applications = Application.query.filter_by(job_id=job_id, is_public=True).all()

    # Check if current user already applied (if logged in)
    user_application = None
    if 'user_id' in session:
        user_application = Application.query.filter_by(
            user_id=session['user_id'],
            job_id=job_id
        ).first()

    return render_template('job_detail.html',
                         job=job,
                         applications=public_applications,
                         user_application=user_application)

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@job_seeker_required
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
        try:
            message = request.form.get('message', '').strip()
            if not message:
                flash('Please provide an application message.', 'error')
                return render_template('job_application.html', job=job, user=user)

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
                    if not cv_filename:
                        flash('Invalid CV file format. Please upload PDF, DOC, DOCX, or TXT files.', 'error')
                        return render_template('job_application.html', job=job, user=user)

            if use_default_cover and user.default_cover_letter:
                cover_letter_filename = user.default_cover_letter
            elif 'cover_letter' in request.files:
                cover_file = request.files['cover_letter']
                if cover_file and cover_file.filename:
                    cover_letter_filename = save_file(cover_file, "cover")
                    if not cover_letter_filename:
                        flash('Invalid cover letter file format. Please upload PDF, DOC, DOCX, or TXT files.', 'error')
                        return render_template('job_application.html', job=job, user=user)

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

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your application. Please try again.', 'error')
            print(f"Application error: {e}")  # For debugging
            return render_template('job_application.html', job=job, user=user)

    return render_template('job_application.html', job=job, user=user)

@app.route('/my-applications')
@job_seeker_required
def my_applications():
    applications = Application.query.filter_by(user_id=session['user_id']).order_by(Application.applied_at.desc()).all()
    return render_template('my_applications.html', applications=applications, current_time=datetime.utcnow())

@app.route('/application/<int:application_id>')
def view_application(application_id):
    application = Application.query.get_or_404(application_id)

    # Check if application is public or user owns it or user is the job provider
    job_provider_id = application.job.posted_by
    user_id = session.get('user_id')

    if not application.is_public and application.user_id != user_id and job_provider_id != user_id:
        flash('This application is private.', 'error')
        return redirect(url_for('index'))

    reviews = ApplicationReview.query.filter_by(application_id=application_id).order_by(ApplicationReview.created_at.desc()).all()

    # Check if current user has already reviewed this application
    user_review = None
    if user_id:
        user_review = ApplicationReview.query.filter_by(
            application_id=application_id,
            reviewer_id=user_id
        ).first()

    return render_template('application_detail.html', application=application, reviews=reviews, user_review=user_review)

@app.route('/application/<int:application_id>/<action>')
@login_required
def handle_application(application_id, action):
    application = Application.query.get_or_404(application_id)
    job = application.job

    current_user = get_current_user()
    if job.posted_by != current_user.id:
        flash("You are not authorized to take this action.")
        return redirect(url_for('provider_dashboard'))

    if action == 'accept':
        application.status = 'accepted'
    elif action == 'decline':
        application.status = 'declined'
    else:
        flash("Invalid action.")
        return redirect(url_for('provider_dashboard'))

    db.session.commit()
    flash(f"Application {action}ed successfully.")
    return redirect(url_for('provider_dashboard'))



@app.route('/application/<int:application_id>/status', methods=['POST'])
@job_provider_required
def update_application_status(application_id):
    application = Application.query.get_or_404(application_id)

    # Check if current user posted this job
    if application.job.posted_by != session['user_id']:
        flash('Access denied. You can only manage applications for your own jobs.', 'error')
        return redirect(url_for('provider_dashboard'))

    new_status = request.form.get('status')
    if new_status in ['pending', 'reviewed', 'accepted', 'rejected']:
        old_status = application.status
        application.status = new_status
        db.session.commit()

        # Create appropriate flash message
        if new_status == 'accepted':
            flash(f'Application from {application.user.username} has been accepted!', 'success')
        elif new_status == 'rejected':
            flash(f'Application from {application.user.username} has been rejected.', 'warning')
        elif new_status == 'reviewed':
            flash(f'Application from {application.user.username} has been marked as reviewed.', 'success')
        else:
            flash('Application status updated successfully!', 'success')
    else:
        flash('Invalid status provided.', 'error')

    return redirect(url_for('provider_dashboard'))

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
@job_provider_required
def add_job():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        skill_required = request.form['skill_required']
        course_link = request.form.get('course_link', '')
        location = request.form.get('location', '')
        experience_level = request.form.get('experience_level', 'Entry Level')
        employment_type = request.form.get('employment_type', 'Full-time')
        salary_range = request.form.get('salary_range', '')

        user = User.query.get(session['user_id'])

        job = Job(
            title=title,
            description=description,
            skill_required=skill_required,
            course_link=course_link,
            company=user.company_name,
            location=location,
            posted_by=user.id,
            experience_level=experience_level,
            employment_type=employment_type,
            salary_range=salary_range
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('provider_dashboard'))

    return render_template('add_job.html')

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()

        # Add sample job provider if none exist
        if User.query.filter_by(role='job_provider').count() == 0:
            sample_provider = User(
                username='techcompany',
                email='hr@techcompany.com',
                role='job_provider',
                company_name='Tech Rwanda',
                company_description='Leading technology company in Rwanda',
                company_location='Kigali, Rwanda',
                contact_person='John Doe',
                contact_phone='+250788123456'
            )
            sample_provider.set_password('password123')
            db.session.add(sample_provider)
            db.session.commit()

            # Add sample jobs if none exist
            if Job.query.count() == 0:
                sample_jobs = [
                    Job(
                        title="Junior Web Developer",
                        description="We're looking for a passionate junior web developer to join our team. You'll work on exciting projects and learn from experienced developers.",
                        skill_required="HTML, CSS, JavaScript",
                        course_link="https://freecodecamp.org/learn/responsive-web-design/",
                        company="Tech Rwanda",
                        location="Kigali, Rwanda",
                        posted_by=sample_provider.id,
                        experience_level="Entry Level",
                        employment_type="Full-time",
                        salary_range="300,000 - 500,000 RWF"
                    ),
                    Job(
                        title="Digital Marketing Assistant",
                        description="Help us grow our online presence through social media marketing, content creation, and SEO optimization.",
                        skill_required="Social Media Marketing, Content Creation",
                        course_link="https://www.coursera.org/learn/digital-marketing",
                        company="Tech Rwanda",
                        location="Kigali, Rwanda",
                        posted_by=sample_provider.id,
                        experience_level="Entry Level",
                        employment_type="Part-time",
                        salary_range="200,000 - 350,000 RWF"
                    )
                ]

                for job in sample_jobs:
                    db.session.add(job)
                db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)