# Database models for the NEET Study Tracker application
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for student accounts"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    
    # Account status
    is_active = db.Column(db.Boolean, default=False)  # Requires admin approval
    is_admin = db.Column(db.Boolean, default=False)
    
    # Profile information
    full_name = db.Column(db.String(100))
    target_exam_year = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    chapter_progress = db.relationship('ChapterProgress', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    study_logs = db.relationship('StudyLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    test_scores = db.relationship('TestScore', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    revisions = db.relationship('RevisionLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    pomodoro_sessions = db.relationship('PomodoroSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_progress_percentage(self):
        """Calculate overall syllabus completion percentage"""
        total_chapters = self.chapter_progress.count()
        if total_chapters == 0:
            return 0
        completed = self.chapter_progress.filter_by(is_completed=True).count()
        return round((completed / total_chapters) * 100, 1)
    
    def get_subject_progress(self, subject):
        """Get progress percentage for a specific subject"""
        subject_chapters = self.chapter_progress.filter_by(subject=subject).all()
        if not subject_chapters:
            return 0
        completed = sum(1 for ch in subject_chapters if ch.is_completed)
        return round((completed / len(subject_chapters)) * 100, 1)
    
    def __repr__(self):
        return f'<User {self.username}>'


class ChapterProgress(db.Model):
    """Track progress for each NEET syllabus chapter"""
    __tablename__ = 'chapter_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Chapter information
    subject = db.Column(db.String(50), nullable=False)  # Physics, Chemistry, Biology
    chapter_name = db.Column(db.String(200), nullable=False)
    chapter_order = db.Column(db.Integer)  # Order in syllabus
    
    # Progress tracking checkboxes
    ncert_read = db.Column(db.Boolean, default=False)
    lecture_watched = db.Column(db.Boolean, default=False)
    questions_solved = db.Column(db.Boolean, default=False)
    revised = db.Column(db.Boolean, default=False)
    
    # Overall completion status
    is_completed = db.Column(db.Boolean, default=False)
    
    # Revision tracking
    revision_count = db.Column(db.Integer, default=0)
    last_revised_date = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one record per user per chapter
    __table_args__ = (db.UniqueConstraint('user_id', 'subject', 'chapter_name'),)
    
    def update_completion_status(self):
        """Auto-update completion status based on checkboxes"""
        self.is_completed = all([
            self.ncert_read,
            self.lecture_watched,
            self.questions_solved,
            self.revised
        ])
    
    def __repr__(self):
        return f'<ChapterProgress {self.subject} - {self.chapter_name}>'


class StudyLog(db.Model):
    """Daily study time logging"""
    __tablename__ = 'study_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Study session details
    date = db.Column(db.Date, nullable=False, index=True)
    subject = db.Column(db.String(50))  # Optional: specific subject studied
    duration_minutes = db.Column(db.Integer, nullable=False)  # Study duration in minutes
    
    # Optional notes
    notes = db.Column(db.Text)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudyLog {self.date} - {self.duration_minutes}min>'


class TestScore(db.Model):
    """Mock test score tracking"""
    __tablename__ = 'test_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Test details
    test_name = db.Column(db.String(200), nullable=False)
    test_date = db.Column(db.Date, nullable=False, index=True)
    test_type = db.Column(db.String(50))  # Full test, Subject-wise, Chapter-wise
    
    # Subject-wise scores
    physics_score = db.Column(db.Integer)
    physics_total = db.Column(db.Integer)
    chemistry_score = db.Column(db.Integer)
    chemistry_total = db.Column(db.Integer)
    biology_score = db.Column(db.Integer)
    biology_total = db.Column(db.Integer)
    
    # Overall scores
    total_score = db.Column(db.Integer, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float)
    
    # Optional analysis
    notes = db.Column(db.Text)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_percentage(self):
        """Calculate percentage score"""
        if self.total_marks > 0:
            self.percentage = round((self.total_score / self.total_marks) * 100, 2)
        else:
            self.percentage = 0
    
    def __repr__(self):
        return f'<TestScore {self.test_name} - {self.percentage}%>'


class RevisionLog(db.Model):
    """Track chapter revisions and notes"""
    __tablename__ = 'revision_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chapter_progress_id = db.Column(db.Integer, db.ForeignKey('chapter_progress.id'), nullable=False)
    
    # Revision details
    revision_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    revision_number = db.Column(db.Integer)  # 1st revision, 2nd revision, etc.
    
    # Optional notes for this revision
    notes = db.Column(db.Text)
    confidence_level = db.Column(db.Integer)  # 1-5 rating
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    chapter = db.relationship('ChapterProgress', backref='revision_history')
    
    def __repr__(self):
        return f'<RevisionLog {self.revision_date}>'


class PomodoroSession(db.Model):
    """Track Pomodoro study sessions"""
    __tablename__ = 'pomodoro_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Session details
    session_date = db.Column(db.Date, nullable=False, index=True)
    sessions_completed = db.Column(db.Integer, default=0)  # Number of 25-min sessions
    total_focus_time = db.Column(db.Integer, default=0)  # Total minutes of focused study
    
    # Optional: subject being studied
    subject = db.Column(db.String(50))
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PomodoroSession {self.session_date} - {self.sessions_completed} sessions>'


class AdminLog(db.Model):
    """Log admin actions for accountability"""
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Action details
    action_type = db.Column(db.String(50), nullable=False)  # 'approve', 'reject', 'delete', 'view'
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    description = db.Column(db.Text)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    admin = db.relationship('User', foreign_keys=[admin_id], backref='admin_actions')
    target_user = db.relationship('User', foreign_keys=[target_user_id])
    
    def __repr__(self):
        return f'<AdminLog {self.action_type} by Admin {self.admin_id}>'
