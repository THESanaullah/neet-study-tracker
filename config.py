# Configuration settings for the Flask application
import os
from datetime import timedelta

class Config:
    """Base configuration class with common settings"""
    
    # Security: Secret key for session management and CSRF protection
    # IMPORTANT: Change this to a random secret key in production!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'
    
    # Database configuration
    # Uses SQLite for easy deployment, can be changed to PostgreSQL/MySQL for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///neet_tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Users stay logged in for 7 days
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS in production
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    
    # Admin credentials (for initial admin account)
    # IMPORTANT: Change these in production or use environment variables
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@neetstudy.com'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    
    # Pagination settings
    USERS_PER_PAGE = 20
    
    # Pomodoro timer defaults (can be customized per user)
    POMODORO_WORK_MINUTES = 25
    POMODORO_SHORT_BREAK = 5
    POMODORO_LONG_BREAK = 15
    POMODORO_CYCLES_BEFORE_LONG_BREAK = 4
    
    # Revision reminder threshold (days)
    REVISION_REMINDER_DAYS = 7
