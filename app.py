from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
import os
import json

# Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database with persistent disk support
    if os.path.exists('/data'):
        DATABASE_PATH = '/data/neet_tracker.db'
    else:
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        DATABASE_PATH = os.path.join(BASE_DIR, 'neet_tracker.db')
    
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'TrackNeet@keemail.me'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'

# Initialize Flask
app = Flask(__name__)
app.config.from_object(Config)

# Import models and forms
from models import db, User, ChapterProgress, StudyLog, TestScore, QuestionLog, AdminLog
from forms import RegistrationForm, LoginForm, StudyLogForm, TestScoreForm, QuestionPracticeForm, AdminPasswordResetForm
from syllabus_data import NEET_SYLLABUS

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables and admin
with app.app_context():
    db.create_all()
    
    admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
    if not admin:
        admin = User(
            username=app.config['ADMIN_USERNAME'],
            email=app.config['ADMIN_EMAIL'],
            is_admin=True,
            is_active=True,
            full_name='System Administrator'
        )
        admin.set_password(app.config['ADMIN_PASSWORD'])
        db.session.add(admin)
        db.session.commit()

# Helper functions
def initialize_user_chapters(user):
    for subject, chapters in NEET_SYLLABUS.items():
        for idx, chapter_name in enumerate(chapters, 1):
            chapter_progress = ChapterProgress(
                user_id=user.id,
                subject=subject,
                chapter_name=chapter_name,
                chapter_order=idx
            )
            db.session.add(chapter_progress)
    db.session.commit()

# PUBLIC ROUTES
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            target_exam_year=form.target_exam_year.data,
            is_active=False
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        initialize_user_chapters(user)
        
        flash('Registration successful! Your account is pending admin approval.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
        
        if not user.is_active and not user.is_admin:
            flash('Your account is pending admin approval.', 'warning')
            return redirect(url_for('login'))
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        
        if user.must_change_password:
            flash('You must change your password before continuing.', 'warning')
            return redirect(url_for('change_password'))
        
        flash(f'Welcome back, {user.username}!', 'success')
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('admin_dashboard') if user.is_admin else url_for('dashboard')
        return redirect(next_page)
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# USER DASHBOARD
@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_active and not current_user.is_admin:
        flash('Your account is pending admin approval.', 'warning')
        return redirect(url_for('index'))
    
    physics_chapters = ChapterProgress.query.filter_by(user_id=current_user.id, subject='Physics').order_by(ChapterProgress.chapter_order).all()
    chemistry_chapters = ChapterProgress.query.filter_by(user_id=current_user.id, subject='Chemistry').order_by(ChapterProgress.chapter_order).all()
    biology_chapters = ChapterProgress.query.filter_by(user_id=current_user.id, subject='Biology').order_by(ChapterProgress.chapter_order).all()
    
    overall_progress = current_user.get_progress_percentage()
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    total_study_time = db.session.query(db.func.sum(StudyLog.duration_minutes)).filter(
        StudyLog.user_id == current_user.id,
        StudyLog.date >= week_ago
    ).scalar() or 0
    
    total_study_time_week = round(total_study_time / 60, 1)
    
    return render_template('dashboard.html',
                         physics_chapters=physics_chapters,
                         chemistry_chapters=chemistry_chapters,
                         biology_chapters=biology_chapters,
                         overall_progress=overall_progress,
                         total_study_time_week=total_study_time_week)

@app.route('/update_chapter/<int:chapter_id>', methods=['POST'])
@login_required
def update_chapter(chapter_id):
    chapter = ChapterProgress.query.get_or_404(chapter_id)
    
    if chapter.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'ncert_read' in data:
        chapter.ncert_read = data['ncert_read']
    if 'lecture_watched' in data:
        chapter.lecture_watched = data['lecture_watched']
    if 'questions_solved' in data:
        chapter.questions_solved = data['questions_solved']
    if 'revised' in data:
        chapter.revised = data['revised']
    
    chapter.update_completion_status()
    chapter.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'is_completed': chapter.is_completed})

# STUDY LOG
@app.route('/study_log', methods=['GET', 'POST'])
@login_required
def study_log():
    form = StudyLogForm()
    
    if form.validate_on_submit():
        log = StudyLog(
            user_id=current_user.id,
            date=form.date.data,
            subject=form.subject.data if form.subject.data else None,
            duration_minutes=form.duration_minutes.data,
            notes=form.notes.data
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Study session logged successfully!', 'success')
        return redirect(url_for('study_log'))
    
    logs = StudyLog.query.filter_by(user_id=current_user.id).order_by(StudyLog.date.desc()).limit(20).all()
    
    # Chart data
    last_30_days = date.today() - timedelta(days=30)
    study_data = db.session.query(
        StudyLog.date,
        StudyLog.subject,
        db.func.sum(StudyLog.duration_minutes)
    ).filter(
        StudyLog.user_id == current_user.id,
        StudyLog.date >= last_30_days
    ).group_by(StudyLog.date, StudyLog.subject).all()
    
    chart_data = {}
    for log_date, subject, minutes in study_data:
        date_str = log_date.strftime('%Y-%m-%d')
        if date_str not in chart_data:
            chart_data[date_str] = {'Physics': 0, 'Chemistry': 0, 'Biology': 0, 'All': 0}
        if subject:
            chart_data[date_str][subject] = round(minutes / 60, 1)
        else:
            chart_data[date_str]['All'] = round(minutes / 60, 1)
    
    return render_template('study_log.html', form=form, logs=logs, chart_data=json.dumps(chart_data))

@app.route('/delete_study_log/<int:log_id>', methods=['POST'])
@login_required
def delete_study_log(log_id):
    log = StudyLog.query.get_or_404(log_id)
    if log.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(log)
    db.session.commit()
    flash('Study log deleted.', 'info')
    return redirect(url_for('study_log'))
# TEST TRACKER
@app.route('/test_tracker', methods=['GET', 'POST'])
@login_required
def test_tracker():
    form = TestScoreForm()
    
    if form.validate_on_submit():
        test = TestScore(
            user_id=current_user.id,
            test_name=form.test_name.data,
            test_date=form.test_date.data,
            test_type=form.test_type.data,
            physics_score=form.physics_score.data,
            physics_total=form.physics_total.data,
            chemistry_score=form.chemistry_score.data,
            chemistry_total=form.chemistry_total.data,
            biology_score=form.biology_score.data,
            biology_total=form.biology_total.data,
            total_score=form.total_score.data,
            total_marks=form.total_marks.data,
            notes=form.notes.data
        )
        test.calculate_percentage()
        db.session.add(test)
        db.session.commit()
        
        flash('Test score added successfully!', 'success')
        return redirect(url_for('test_tracker'))
    
    tests = TestScore.query.filter_by(user_id=current_user.id).order_by(TestScore.test_date.desc()).all()
    
    # Chart data
    chart_data = []
    for test in tests:
        chart_data.append({
            'date': test.test_date.strftime('%Y-%m-%d'),
            'name': test.test_name,
            'percentage': test.percentage
        })
    
    return render_template('test_tracker.html', form=form, tests=tests, chart_data=json.dumps(chart_data))

@app.route('/delete_test/<int:test_id>', methods=['POST'])
@login_required
def delete_test(test_id):
    test = TestScore.query.get_or_404(test_id)
    if test.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(test)
    db.session.commit()
    flash('Test score deleted.', 'info')
    return redirect(url_for('test_tracker'))

# QUESTION PRACTICE
@app.route('/questions_practice', methods=['GET', 'POST'])
@login_required
def questions_practice():
    form = QuestionPracticeForm()
    
    if form.validate_on_submit():
        log = QuestionLog(
            user_id=current_user.id,
            subject=form.subject.data,
            chapter_name=form.chapter_name.data,
            questions_count=form.questions_count.data,
            date=form.date.data if form.date.data else date.today(),
            notes=form.notes.data
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Added {form.questions_count.data} questions for {form.chapter_name.data}!', 'success')
        return redirect(url_for('questions_practice'))
    
    logs = QuestionLog.query.filter_by(user_id=current_user.id).order_by(QuestionLog.date.desc()).limit(50).all()
    
    # Subject-wise totals
    subject_totals = db.session.query(
        QuestionLog.subject,
        db.func.sum(QuestionLog.questions_count)
    ).filter(QuestionLog.user_id == current_user.id).group_by(QuestionLog.subject).all()
    
    totals = {subject: count for subject, count in subject_totals}
    
    # Chart data - questions per day per subject
    last_30_days = date.today() - timedelta(days=30)
    question_data = db.session.query(
        QuestionLog.date,
        QuestionLog.subject,
        db.func.sum(QuestionLog.questions_count)
    ).filter(
        QuestionLog.user_id == current_user.id,
        QuestionLog.date >= last_30_days
    ).group_by(QuestionLog.date, QuestionLog.subject).all()
    
    chart_data = {}
    for log_date, subject, count in question_data:
        date_str = log_date.strftime('%Y-%m-%d')
        if date_str not in chart_data:
            chart_data[date_str] = {'Physics': 0, 'Chemistry': 0, 'Biology': 0}
        chart_data[date_str][subject] = count
    
    return render_template('questions_practice.html', 
                         form=form, 
                         logs=logs, 
                         totals=totals,
                         chart_data=json.dumps(chart_data))

@app.route('/delete_question_log/<int:log_id>', methods=['POST'])
@login_required
def delete_question_log(log_id):
    log = QuestionLog.query.get_or_404(log_id)
    if log.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(log)
    db.session.commit()
    flash('Question log deleted (undo successful).', 'info')
    return redirect(url_for('questions_practice'))

# PASSWORD CHANGE
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = AdminPasswordResetForm()
    
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        current_user.password_changed_at = datetime.utcnow()
        current_user.must_change_password = False
        
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('change_password.html', form=form, forced=current_user.must_change_password)

# ADMIN ROUTES
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('admin_login'))
        
        if not user.is_admin:
            flash('Admin access only.', 'danger')
            return redirect(url_for('admin_login'))
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome, Admin {user.username}!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/admin_login.html', form=form)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    total_users = User.query.filter_by(is_admin=False).count()
    active_users = User.query.filter_by(is_admin=False, is_active=True).count()
    pending_users = User.query.filter_by(is_admin=False, is_active=False).count()
    
    recent_users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('admin/admin_dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         pending_users=pending_users,
                         recent_users=recent_users)

@app.route('/admin/pending_users')
@login_required
def pending_users():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    pending = User.query.filter_by(is_admin=False, is_active=False).order_by(User.created_at.desc()).all()
    return render_template('admin/pending_users.html', pending_users=pending)

@app.route('/admin/approve_user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = True
    user.approved_at = datetime.utcnow()
    user.approved_by_id = current_user.id
    
    db.session.commit()
    
    log = AdminLog(
        admin_id=current_user.id,
        target_user_id=user.id,
        action_type='approve_user',
        description=f'Approved user: {user.username}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'User {user.username} approved!', 'success')
    return redirect(url_for('pending_users'))

@app.route('/admin/reject_user/<int:user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    username = user.username
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} rejected and deleted.', 'warning')
    return redirect(url_for('pending_users'))

@app.route('/admin/manage_users')
@login_required
def manage_users():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/user/<int:user_id>')
@login_required
def view_user_progress(user_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    physics_progress = user.chapter_progress.filter_by(subject='Physics').order_by(ChapterProgress.chapter_order).all()
    chemistry_progress = user.chapter_progress.filter_by(subject='Chemistry').order_by(ChapterProgress.chapter_order).all()
    biology_progress = user.chapter_progress.filter_by(subject='Biology').order_by(ChapterProgress.chapter_order).all()
    
    recent_study_logs = user.study_logs.order_by(StudyLog.date.desc()).limit(10).all()
    recent_tests = user.test_scores.order_by(TestScore.test_date.desc()).limit(10).all()
    
    return render_template('admin/view_user_progress.html',
                         user=user,
                         physics_progress=physics_progress,
                         chemistry_progress=chemistry_progress,
                         biology_progress=biology_progress,
                         recent_study_logs=recent_study_logs,
                         recent_tests=recent_tests)

@app.route('/admin/deactivate_user/<int:user_id>', methods=['POST'])
@login_required
def deactivate_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    
    flash(f'User {user.username} deactivated.', 'warning')
    return redirect(url_for('manage_users'))

@app.route('/admin/activate_user/<int:user_id>', methods=['POST'])
@login_required
def activate_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    
    flash(f'User {user.username} activated.', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/reset_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_reset_password(user_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = AdminPasswordResetForm()
    
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        user.password_changed_at = datetime.utcnow()
        user.must_change_password = True
        
        db.session.commit()
        
        log = AdminLog(
            admin_id=current_user.id,
            target_user_id=user.id,
            action_type='password_reset',
            description=f'Reset password for: {user.username}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Password reset for {user.username}! Temporary password: {form.new_password.data}', 'warning')
        flash('User must change password on next login.', 'info')
        return redirect(url_for('view_user_progress', user_id=user.id))
    
    return render_template('admin/reset_password.html', form=form, user=user)

# LEGAL PAGES
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ERROR HANDLERS
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

from decorators import admin_required, login_required, active_user_required, password_change_required

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Only accessible to logged-in admin users
    pass

@app.route('/dashboard')
@login_required
@active_user_required
@password_change_required
def dashboard():
    # Only accessible to active users who have changed their password
    pass


if __name__ == '__main__':
    app.run(debug=True)
