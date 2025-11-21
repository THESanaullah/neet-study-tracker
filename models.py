from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(128))
    target_exam_year = db.Column(db.Integer)
    
    is_active = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    must_change_password = db.Column(db.Boolean, default=False)
    password_changed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    chapter_progress = db.relationship('ChapterProgress', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    study_logs = db.relationship('StudyLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    test_scores = db.relationship('TestScore', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    question_logs = db.relationship('QuestionLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_progress_percentage(self):
        total = self.chapter_progress.count()
        if total == 0:
            return 0
        completed = self.chapter_progress.filter_by(is_completed=True).count()
        return round((completed / total) * 100, 1)
    
    def __repr__(self):
        return f'<User {self.username}>'

class ChapterProgress(db.Model):
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
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def update_completion_status(self):
        self.is_completed = all([self.ncert_read, self.lecture_watched, self.questions_solved, self.revised])

class StudyLog(db.Model):
    __tablename__ = 'study_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    subject = db.Column(db.String(50))
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TestScore(db.Model):
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
        if self.total_marks > 0:
            self.percentage = round((self.total_score / self.total_marks) * 100, 2)
        else:
            self.percentage = 0.0

class QuestionLog(db.Model):
    __tablename__ = 'question_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    chapter_name = db.Column(db.String(256), nullable=False)
    questions_count = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
