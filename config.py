# Configuration for NEET Study Tracker
import os

class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///neet_tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Admin credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@neetstudy.com'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    
    # Pomodoro settings
    POMODORO_WORK_MINUTES = 25
    POMODORO_SHORT_BREAK = 5
    POMODORO_LONG_BREAK = 15
    POMODORO_CYCLES_BEFORE_LONG_BREAK = 4
    
    # Revision settings
    REVISION_REMINDER_DAYS = 7
    
    # Pagination
    USERS_PER_PAGE = 20
