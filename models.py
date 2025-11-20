# Database models for NEET Study Tracker
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Create db instance WITHOUT app binding
db = SQLAlchemy()

# ============================================================================
# USER MODEL
# ============================================================================

class User(UserMixin, db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(128))
    target_exam_year = db.Column(db.Integer)
    
    is_active = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    chapter_progress = db.relationship('ChapterProgress', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    study_logs = db.relationship('StudyLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    test_scores = db.relationship('TestScore', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    revision_logs = db.relationship('RevisionLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    pomodoro_sessions = db.relationship('PomodoroSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_progress_percentage(self):
        """Calculate overall progress percentage"""
        total_chapters = self.chapter_progress.count()
        if total_chapters == 0:
            return 0
        completed_chapters = self.chapter_progress.filter_by(is_completed=True).count()
        return round((completed_chapters / total_chapters) * 100, 1)
    
    def get_subject_progress(self, subject):
        """Calculate progress for specific subject"""
        subject_chapters = self.chapter_progress.filter_by(subject=subject).all()
        if not subject_chapters:
            return 0
        completed = sum(1 for ch in subject_chapters if ch.is_completed)
        return round((completed / len(subject_chapters)) * 100, 1)
    
    def __repr__(self):
        return f'<User {self.username}>'

# ============================================================================
# CHAPTER PROGRESS MODEL
# ============================================================================

class ChapterProgress(db.Model):
    """Chapter-wise progress tracking"""
    __tablename__ = 'chapter_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    chapter_name = db.Column(db.String(256), nullable=False)
    chapter_order = db.Column(db.Integer)
    
    ncert_read = db.Column(db.Boolean, default=False)
    lecture_watched = db.Column(db.Boolean, default=False)
    questions_solved = db.Column(db.Boolean, default=False)
    revised = db.Column(db.Boolean, default=False)
    
    is_completed = db.Column(db.Boolean, default=False)
    revision_count = db.Column(db.Integer, default=0)
    last_revised_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    revision_logs = db.relationship('RevisionLog', backref='chapter', lazy='dynamic', cascade='all, delete-orphan')
    
    def update_completion_status(self):
        """Update completion status based on checkboxes"""
        self.is_completed = all([
            self.ncert_read,
            self.lecture_watched,
            self.questions_solved,
            self.revised
        ])
    
    def __repr__(self):
        return f'<ChapterProgress {self.subject} - {self.chapter_name}>'

# ============================================================================
# STUDY LOG MODEL
# ============================================================================

class StudyLog(db.Model):
    """Daily study time logging"""
    __tablename__ = 'study_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    subject = db.Column(db.String(50))
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudyLog {self.date} - {self.duration_minutes}min>'

# ============================================================================
# TEST SCORE MODEL
# ============================================================================

class TestScore(db.Model):
    """Mock test score tracking"""
    __tablename__ = 'test_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_name = db.Column(db.String(256), nullable=False)
    test_date = db.Column(db.Date, nullable=False)
    test_type = db.Column(db.String(50))
    
    physics_score = db.Column(db.Integer)
    physics_total = db.Column(db.Integer)
    chemistry_score = db.Column(db.Integer)
    chemistry_total = db.Column(db.Integer)
    biology_score = db.Column(db.Integer)
    biology_total = db.Column(db.Integer)
    
    total_score = db.Column(db.Integer, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float)
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_percentage(self):
        """Calculate percentage score"""
        if self.total_marks > 0:
            self.percentage = round((self.total_score / self.total_marks) * 100, 2)
        else:
            self.percentage = 0.0
    
    def __repr__(self):
        return f'<TestScore {self.test_name} - {self.percentage}%>'

# ============================================================================
# REVISION LOG MODEL
# ============================================================================

class RevisionLog(db.Model):
    """Revision history tracking"""
    __tablename__ = 'revision_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chapter_progress_id = db.Column(db.Integer, db.ForeignKey('chapter_progress.id'), nullable=False)
    
    revision_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    revision_number = db.Column(db.Integer)
    confidence_level = db.Column(db.Integer)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<RevisionLog Chapter#{self.chapter_progress_id} Rev#{self.revision_number}>'

# ============================================================================
# POMODORO SESSION MODEL
# ============================================================================

class PomodoroSession(db.Model):
    """Pomodoro timer session tracking"""
    __tablename__ = 'pomodoro_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    sessions_completed = db.Column(db.Integer, default=0)
    total_focus_time = db.Column(db.Integer, default=0)
    subject = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PomodoroSession {self.session_date} - {self.sessions_completed} sessions>'

# ============================================================================
# ADMIN LOG MODEL
# ============================================================================

class AdminLog(db.Model):
    """Admin action logging"""
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    admin = db.relationship('User', foreign_keys=[admin_id], backref='admin_actions')
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='received_actions')
    
    def __repr__(self):
        return f'<AdminLog {self.action_type} by Admin#{self.admin_id}>'
