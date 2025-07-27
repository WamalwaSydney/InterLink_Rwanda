## HOW TO RUN THE APP
--------------------------------------------
**1. Move to the directory + Run the file**


 "cd interlink_rwanda && source ../interlink_env/bin/activate && flask run"
# 🚀 InternLink Rwanda

**Connecting Rwandan youth with meaningful employment opportunities through technology**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Contributing](#contributing)
- [Deployment](#deployment)
- [Performance Optimization](#performance-optimization)
- [Security Features](#security-features)
- [Internationalization](#internationalization)
- [Mobile Responsiveness](#mobile-responsiveness)
- [Analytics & Monitoring](#analytics--monitoring)
- [Troubleshooting](#troubleshooting)
- [Support](#support)
- [Roadmap](#roadmap)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Links](#links)

---

## 🌟 Overview

InternLink Rwanda is a job-matching platform aimed at reducing youth unemployment in Rwanda by linking job seekers with employers. It includes features like application tracking, peer reviews, WhatsApp integration, and more.

### 🎯 Mission
To reduce youth unemployment in Rwanda by connecting talented young professionals with employers seeking skilled workers.

### 🌍 Vision
To become Rwanda's leading platform for youth employment, enabling economic growth through strategic job matching and skill development.

---

## ✨ Features

### 👥 For Job Seekers
- Profile management
- Smart job search
- Application tracking
- Peer review system
- Document management
- Email and WhatsApp notifications
- Curated skill development resources

### 🏢 For Employers
- Company profile management
- Job posting and editing
- Application review and tracking
- Candidate communication
- Analytics dashboard

### 🤝 Peer Review System
- Public job applications for peer feedback
- Star rating system
- Constructive comments
- Review statistics
- Email alerts

### 📱 Communication Features
- Automated WhatsApp alerts
- Real-time email notifications
- Instant status updates

---

## 🛠 Technology Stack

### Backend
- Flask 2.0+
- SQLAlchemy (SQLite / PostgreSQL / MySQL)
- Flask-Mail (SMTP)
- Flask-Migrate
- Werkzeug Security

### Frontend
- Jinja2 templating
- HTML5/CSS3, Responsive design
- Font Awesome Icons
- Vanilla JavaScript

### Infrastructure
- Local file storage (S3 optional)
- python-dotenv
- Gunicorn (production-ready)
- Docker support

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip
- Git

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/internlink-rwanda.git
   cd internlink-rwanda
Create Virtual Environment

python -m venv interlink_env
source interlink_env/bin/activate
Install Dependencies

pip install -r requirements.txt
Configure Environment Variables

cp .env.example .env
# Update .env with your credentials and config
Run Migrations

flask db init
flask db migrate -m "initial"
flask db upgrade
Run the App

cd internlink_rwanda && source ../interlink_env/bin/activate && flask run
Visit: http://localhost:5000

⚙️ Configuration
.env Variables
SECRET_KEY=your-secret
DEBUG=True
DATABASE_URL=sqlite:///youth_jobs.db

EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True

UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

WHATSAPP_API_URL=http://localhost:3000
WHATSAPP_ENABLED=True
📖 Usage
For Job Seekers
Register at /register/job-seeker

Complete your profile

Browse and apply to jobs

Get feedback from peers

Track application status

For Employers
Register at /register/job-provider

Post and manage jobs

View and review applicants

Communicate directly with candidates

📊 API Documentation
Authentication
POST /login
username=john_doe&password=securepassword
Jobs
GET /api/jobs
POST /add-job
Applications
GET /api/application/{id}/stats
POST /application/{id}/review
Dashboard
GET /dashboard/stats
🗄️ Database Schema
users
id

username

email

password_hash

role (job_seeker/job_provider)

skills

company_name

created_at

jobs
id

title

description

skill_required

company

location

posted_by

experience_level

employment_type

salary_range

posted_at

applications
id

user_id

job_id

message

cv_filename

cover_letter_filename

applied_at

status

is_public

application_reviews
id

application_id

reviewer_id

rating

comment

created_at

🤝 Contributing
Fork the repo

Create a feature branch

git checkout -b feature/amazing-feature
Make your changes and add tests

Submit a pull request

Code Style
Python: PEP8

HTML/CSS: 2-space indentation

JavaScript: ES6+

Tests
python -m pytest
python -m pytest tests/test_applications.py
python -m pytest --cov=app
🔧 Deployment
Gunicorn (Linux Server)
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@localhost/internlink
flask db upgrade
gunicorn -w 4 -b 0.0.0.0:5000 app:app
Docker
Dockerfile

FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
📈 Performance Optimization
Index frequent queries

Use connection pooling

Cache using Redis

Optimize file storage with S3

CDN for static files

🔒 Security Features
Password hashing with Werkzeug

Secure cookies

File type validation & sanitization

SQL injection prevention

XSS protection with Jinja2

CSRF protection (to be added)

🌐 Internationalization
Supported Languages:

English (default)

Kinyarwanda (planned)

French (planned)

📱 Mobile Responsiveness
Optimized for:

Desktop

Tablet

Mobile

📊 Analytics & Monitoring
Registration and job metrics

Peer review engagement

Error logging and uptime monitoring

User behavior analytics (planned)

🆘 Troubleshooting
Database Errors
echo $DATABASE_URL
flask db current
Email Issues
Verify Gmail App Password

Check SMTP settings

File Upload Issues
Verify permissions

Validate file types and size

Debug Mode
export FLASK_ENV=development
flask run
📄 License
MIT License
See LICENSE for full details.

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
🙏 Acknowledgments
African Leadership University


🔗 Links
Website: https://internlink.rw

Documentation: https://docs.internlink.rw

API Reference: https://api.internlink.rw/docs

Status: https://status.internlink.rw

Built with ❤️ in Rwanda for Rwandan Youth
InternLink Rwanda – Bridging the gap between talent and opportunity
