# Main Flask application for NEET Study Tracker
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-this-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///neet_tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@neetstudy.com'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    
    POMODORO_WORK_MINUTES = 25
    POMODORO_SHORT_BREAK = 5
    POMODORO_LONG_BREAK = 15
    POMODORO_CYCLES_BEFORE_LONG_BREAK = 4
    
    REVISION_REMINDER_DAYS = 7
    USERS_PER_PAGE = 20

# ============================================================================
# INITIALIZE FLASK APP
# ============================================================================

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config.from_object(Config)

# ============================================================================
# IMPORT AND INITIALIZE DATABASE
# ============================================================================

# Import db from models (it's not initialized yet)
from models import db, User, ChapterProgress, StudyLog, TestScore, RevisionLog, PomodoroSession, AdminLog

# NOW initialize db with app
db.init_app(app)

# ============================================================================
# INITIALIZE LOGIN MANAGER
# ============================================================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

# ============================================================================
# IMPORT FORMS AND DATA
# ============================================================================

from forms import RegistrationForm, LoginForm, StudyLogForm, TestScoreForm
from syllabus_data import NEET_SYLLABUS

# ============================================================================
# CREATE DATABASE TABLES
# ============================================================================

with app.app_context():
    db.create_all()
    
    # Create admin user if doesn't exist
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
        print(f"✅ Admin user created: {app.config['ADMIN_USERNAME']}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def initialize_user_chapters(user):
    """Initialize chapter progress for new user"""
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

def calculate_study_streak(user_id):
    """Calculate consecutive study days"""
    today = date.today()
    streak = 0
    check_date = today
    
    while True:
        log = StudyLog.query.filter_by(user_id=user_id, date=check_date).first()
        if log:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
        if streak > 365:
            break
    
    return streak

# ============================================================================
# PUBLIC ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
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
    """User login"""
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
        
        # Check if user must change password
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
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ============================================================================
# USER DASHBOARD
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main user dashboard"""
    if not current_user.is_active and not current_user.is_admin:
        flash('Your account is pending admin approval.', 'warning')
        return redirect(url_for('index'))
    
    physics_chapters = ChapterProgress.query.filter_by(
        user_id=current_user.id, subject='Physics'
    ).order_by(ChapterProgress.chapter_order).all()
    
    chemistry_chapters = ChapterProgress.query.filter_by(
        user_id=current_user.id, subject='Chemistry'
    ).order_by(ChapterProgress.chapter_order).all()
    
    biology_chapters = ChapterProgress.query.filter_by(
        user_id=current_user.id, subject='Biology'
    ).order_by(ChapterProgress.chapter_order).all()
    
    overall_progress = current_user.get_progress_percentage()
    physics_progress = current_user.get_subject_progress('Physics')
    chemistry_progress = current_user.get_subject_progress('Chemistry')
    biology_progress = current_user.get_subject_progress('Biology')
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    total_study_time = db.session.query(db.func.sum(StudyLog.duration_minutes)).filter(
        StudyLog.user_id == current_user.id,
        StudyLog.date >= week_ago
    ).scalar() or 0
    
    total_study_time_week = round(total_study_time / 60, 1)
    study_streak = calculate_study_streak(current_user.id)
    
    revision_threshold = datetime.utcnow() - timedelta(days=app.config['REVISION_REMINDER_DAYS'])
    chapters_need_revision = ChapterProgress.query.filter(
        ChapterProgress.user_id == current_user.id,
        ChapterProgress.revised == True,
        ChapterProgress.last_revised_date < revision_threshold
    ).count()
    
    pomodoro_today = PomodoroSession.query.filter_by(
        user_id=current_user.id, session_date=today
    ).first()
    
    pomodoro_count_today = pomodoro_today.sessions_completed if pomodoro_today else 0
    
    return render_template('dashboard.html',
                         physics_chapters=physics_chapters,
                         chemistry_chapters=chemistry_chapters,
                         biology_chapters=biology_chapters,
                         overall_progress=overall_progress,
                         physics_progress=physics_progress,
                         chemistry_progress=chemistry_progress,
                         biology_progress=biology_progress,
                         total_study_time_week=total_study_time_week,
                         study_streak=study_streak,
                         chapters_need_revision=chapters_need_revision,
                         pomodoro_count_today=pomodoro_count_today)

@app.route('/update_chapter/<int:chapter_id>', methods=['POST'])
@login_required
def update_chapter(chapter_id):
    """Update chapter progress"""
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
        if data['revised']:
            chapter.revision_count += 1
            chapter.last_revised_date = datetime.utcnow()
    
    chapter.update_completion_status()
    chapter.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_completed': chapter.is_completed,
        'revision_count': chapter.revision_count
    })

# Continue with remaining routes...
# (Due to length, use the previous full app.py I provided)

# ============================================================================
# LEGAL PAGES ROUTES
# ============================================================================

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/terms')
def terms():
    """Terms and conditions"""
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    """Privacy policy"""
    return render_template('privacy.html')

@app.route('/disclaimer')
def disclaimer():
    """Disclaimer page"""
    return render_template('disclaimer.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')



if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# ============================================================================
# STUDY LOG ROUTES
# ============================================================================

@app.route('/study_log', methods=['GET', 'POST'])
@login_required
def study_log():
    """Study time logging"""
    form = StudyLogForm()
    
    if request.method == 'GET':
        form.date.data = date.today()
    
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
        
        flash(f'Study session logged: {form.duration_minutes.data} minutes', 'success')
        return redirect(url_for('study_log'))
    
    logs = StudyLog.query.filter_by(user_id=current_user.id).order_by(
        StudyLog.date.desc()
    ).limit(30).all()
    
    total_time = db.session.query(db.func.sum(StudyLog.duration_minutes)).filter_by(
        user_id=current_user.id
    ).scalar() or 0
    
    avg_time = db.session.query(db.func.avg(StudyLog.duration_minutes)).filter_by(
        user_id=current_user.id
    ).scalar() or 0
    
    total_hours = round(total_time / 60, 1)
    avg_hours = round(avg_time / 60, 1)
    
    return render_template('study_log.html',
                         form=form,
                         logs=logs,
                         total_hours=total_hours,
                         avg_hours=avg_hours)

@app.route('/study_stats')
@login_required
def study_stats():
    """Get study statistics"""
    days = request.args.get('days', 30, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    logs = StudyLog.query.filter(
        StudyLog.user_id == current_user.id,
        StudyLog.date >= start_date
    ).order_by(StudyLog.date).all()
    
    dates = []
    durations = []
    
    for log in logs:
        dates.append(log.date.strftime('%Y-%m-%d'))
        durations.append(log.duration_minutes)
    
    return jsonify({
        'dates': dates,
        'durations': durations
    })

# ============================================================================
# TEST TRACKER ROUTES
# ============================================================================

@app.route('/test_tracker', methods=['GET', 'POST'])
@login_required
def test_tracker():
    """Mock test tracker"""
    form = TestScoreForm()
    
    if request.method == 'GET':
        form.test_date.data = date.today()
    
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
        
        flash(f'Test score saved: {test.percentage}%', 'success')
        return redirect(url_for('test_tracker'))
    
    tests = TestScore.query.filter_by(user_id=current_user.id).order_by(
        TestScore.test_date.desc()
    ).all()
    
    return render_template('test_tracker.html', form=form, tests=tests)

@app.route('/test_stats')
@login_required
def test_stats():
    """Get test statistics"""
    tests = TestScore.query.filter_by(user_id=current_user.id).order_by(
        TestScore.test_date
    ).all()
    
    dates = [t.test_date.strftime('%Y-%m-%d') for t in tests]
    percentages = [t.percentage for t in tests]
    
    physics_scores = []
    chemistry_scores = []
    biology_scores = []
    
    for t in tests:
        if t.physics_total and t.physics_total > 0:
            physics_scores.append(round((t.physics_score / t.physics_total) * 100, 1))
        if t.chemistry_total and t.chemistry_total > 0:
            chemistry_scores.append(round((t.chemistry_score / t.chemistry_total) * 100, 1))
        if t.biology_total and t.biology_total > 0:
            biology_scores.append(round((t.biology_score / t.biology_total) * 100, 1))
    
    return jsonify({
        'dates': dates,
        'percentages': percentages,
        'physics_scores': physics_scores,
        'chemistry_scores': chemistry_scores,
        'biology_scores': biology_scores
    })

# ============================================================================
# REVISION ROUTES
# ============================================================================

@app.route('/revision')
@login_required
def revision():
    """Revision tracking"""
    chapters = ChapterProgress.query.filter_by(user_id=current_user.id).order_by(
        ChapterProgress.subject, ChapterProgress.chapter_order
    ).all()
    
    revision_threshold = datetime.utcnow() - timedelta(days=app.config['REVISION_REMINDER_DAYS'])
    chapters_need_revision = [ch for ch in chapters 
                             if ch.revised and ch.last_revised_date 
                             and ch.last_revised_date < revision_threshold]
    
    recent_revisions = RevisionLog.query.filter_by(user_id=current_user.id).order_by(
        RevisionLog.revision_date.desc()
    ).limit(20).all()
    
    return render_template('revision.html',
                         chapters=chapters,
                         chapters_need_revision=chapters_need_revision,
                         recent_revisions=recent_revisions,
                         now=datetime.utcnow())

@app.route('/log_revision/<int:chapter_id>', methods=['POST'])
@login_required
def log_revision(chapter_id):
    """Log revision"""
    chapter = ChapterProgress.query.get_or_404(chapter_id)
    
    if chapter.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    chapter.revision_count += 1
    chapter.last_revised_date = datetime.utcnow()
    chapter.revised = True
    chapter.update_completion_status()
    
    revision = RevisionLog(
        user_id=current_user.id,
        chapter_progress_id=chapter.id,
        revision_date=datetime.utcnow(),
        revision_number=chapter.revision_count,
        notes=data.get('notes', ''),
        confidence_level=int(data.get('confidence_level', 0)) if data.get('confidence_level') else None
    )
    
    db.session.add(revision)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'revision_count': chapter.revision_count,
        'last_revised': chapter.last_revised_date.strftime('%Y-%m-%d')
    })

# ============================================================================
# POMODORO ROUTES
# ============================================================================

@app.route('/pomodoro/start', methods=['POST'])
@login_required
def pomodoro_start():
    """Start pomodoro"""
    return jsonify({'success': True, 'message': 'Pomodoro started'})

@app.route('/pomodoro/complete', methods=['POST'])
@login_required
def pomodoro_complete():
    """Complete pomodoro"""
    today = date.today()
    
    session = PomodoroSession.query.filter_by(
        user_id=current_user.id,
        session_date=today
    ).first()
    
    if not session:
        session = PomodoroSession(
            user_id=current_user.id,
            session_date=today,
            sessions_completed=0,
            total_focus_time=0
        )
        db.session.add(session)
    
    session.sessions_completed += 1
    session.total_focus_time += 25
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'sessions_today': session.sessions_completed,
        'total_minutes': session.total_focus_time
    })

@app.route('/pomodoro/stats')
@login_required
def pomodoro_stats():
    """Get pomodoro stats"""
    days = request.args.get('days', 7, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    sessions = PomodoroSession.query.filter(
        PomodoroSession.user_id == current_user.id,
        PomodoroSession.session_date >= start_date
    ).order_by(PomodoroSession.session_date).all()
    
    dates = [s.session_date.strftime('%Y-%m-%d') for s in sessions]
    session_counts = [s.sessions_completed for s in sessions]
    
    total_sessions = sum(session_counts)
    total_hours = round(sum(s.total_focus_time for s in sessions) / 60, 1)
    
    return jsonify({
        'dates': dates,
        'sessions': session_counts,
        'total_sessions': total_sessions,
        'total_hours': total_hours
    })

# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('admin_login'))
        
        if not user.is_admin:
            flash('Access denied.', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome, Admin {user.username}!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/admin_login.html', form=form)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    total_users = User.query.filter_by(is_admin=False).count()
    active_users = User.query.filter_by(is_admin=False, is_active=True).count()
    pending_users = User.query.filter_by(is_admin=False, is_active=False).count()
    
    recent_users = User.query.filter_by(is_admin=False).order_by(
        User.created_at.desc()
    ).limit(10).all()
    
    recent_actions = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(15).all()
    
    return render_template('admin/admin_dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         pending_users=pending_users,
                         recent_users=recent_users,
                         recent_actions=recent_actions,
                         now=datetime.utcnow())

@app.route('/admin/pending_users')
@login_required
def pending_users():
    """Pending users"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    pending = User.query.filter_by(is_admin=False, is_active=False).order_by(
        User.created_at.desc()
    ).all()
    
    return render_template('admin/pending_users.html', pending_users=pending, now=datetime.utcnow())

@app.route('/admin/approve_user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    """Approve user"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    user.is_active = True
    user.approved_at = datetime.utcnow()
    user.approved_by_id = current_user.id
    
    log = AdminLog(
        admin_id=current_user.id,
        action_type='approve',
        target_user_id=user.id,
        description=f'Approved user: {user.username}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'User {user.username} approved!', 'success')
    return redirect(url_for('pending_users'))

@app.route('/admin/reject_user/<int:user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    """Reject user"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    username = user.username
    
    log = AdminLog(
        admin_id=current_user.id,
        action_type='reject',
        target_user_id=user.id,
        description=f'Rejected user: {username}'
    )
    db.session.add(log)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} rejected!', 'info')
    return redirect(url_for('pending_users'))

@app.route('/admin/manage_users')
@login_required
def manage_users():
    """Manage users"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.filter_by(is_admin=False).order_by(
        User.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/manage_users.html', users=users, now=datetime.utcnow())

@app.route('/admin/view_user/<int:user_id>')
@login_required
def view_user_progress(user_id):
    """View user progress"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot view admin user progress.', 'warning')
        return redirect(url_for('manage_users'))
    
    log = AdminLog(
        admin_id=current_user.id,
        action_type='view',
        target_user_id=user.id,
        description=f'Viewed progress: {user.username}'
    )
    db.session.add(log)
    db.session.commit()
    
    physics_chapters = ChapterProgress.query.filter_by(
        user_id=user.id, subject='Physics'
    ).order_by(ChapterProgress.chapter_order).all()
    
    chemistry_chapters = ChapterProgress.query.filter_by(
        user_id=user.id, subject='Chemistry'
    ).order_by(ChapterProgress.chapter_order).all()
    
    biology_chapters = ChapterProgress.query.filter_by(
        user_id=user.id, subject='Biology'
    ).order_by(ChapterProgress.chapter_order).all()
    
    overall_progress = user.get_progress_percentage()
    physics_progress = user.get_subject_progress('Physics')
    chemistry_progress = user.get_subject_progress('Chemistry')
    biology_progress = user.get_subject_progress('Biology')
    
    recent_tests = TestScore.query.filter_by(user_id=user.id).order_by(
        TestScore.test_date.desc()
    ).limit(5).all()
    
    recent_study = StudyLog.query.filter_by(user_id=user.id).order_by(
        StudyLog.date.desc()
    ).limit(10).all()
    
    return render_template('admin/view_user_progress.html',
                         user=user,
                         physics_chapters=physics_chapters,
                         chemistry_chapters=chemistry_chapters,
                         biology_chapters=biology_chapters,
                         overall_progress=overall_progress,
                         physics_progress=physics_progress,
                         chemistry_progress=chemistry_progress,
                         biology_progress=biology_progress,
                         recent_tests=recent_tests,
                         recent_study=recent_study)

@app.route('/admin/deactivate_user/<int:user_id>', methods=['POST'])
@login_required
def deactivate_user(user_id):
    """Deactivate user"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = False
    
    log = AdminLog(
        admin_id=current_user.id,
        action_type='deactivate',
        target_user_id=user.id,
        description=f'Deactivated: {user.username}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'User {user.username} deactivated!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete user"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    username = user.username
    
    log = AdminLog(
        admin_id=current_user.id,
        action_type='delete',
        target_user_id=user.id,
        description=f'Deleted: {username}'
    )
    db.session.add(log)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} deleted!', 'warning')
    return redirect(url_for('manage_users'))

# ============================================================================
# ADMIN - CONTENT MANAGEMENT ROUTES
# ============================================================================

@app.route('/admin/content')
@login_required
def admin_content():
    """Content management dashboard"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    contents = WebsiteContent.query.order_by(WebsiteContent.page, WebsiteContent.section).all()
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(10).all()
    
    return render_template('admin/content_management.html',
                         contents=contents,
                         announcements=announcements)

@app.route('/admin/content/edit/<int:content_id>', methods=['GET', 'POST'])
@login_required
def edit_content(content_id):
    """Edit website content"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    content = WebsiteContent.query.get_or_404(content_id)
    form = ContentEditForm()
    
    if form.validate_on_submit():
        content.content = form.content.data
        content.updated_by_id = current_user.id
        content.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Content updated: {content.page} - {content.section}', 'success')
        return redirect(url_for('admin_content'))
    
    if request.method == 'GET':
        form.content.data = content.content
    
    return render_template('admin/edit_content.html', form=form, content=content)

# ============================================================================
# ADMIN - SYLLABUS MANAGEMENT
# ============================================================================

@app.route('/admin/syllabus')
@login_required
def admin_syllabus():
    """Syllabus management"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    physics_chapters = SyllabusChapter.query.filter_by(subject='Physics').order_by(
        SyllabusChapter.chapter_order
    ).all()
    
    chemistry_chapters = SyllabusChapter.query.filter_by(subject='Chemistry').order_by(
        SyllabusChapter.chapter_order
    ).all()
    
    biology_chapters = SyllabusChapter.query.filter_by(subject='Biology').order_by(
        SyllabusChapter.chapter_order
    ).all()
    
    return render_template('admin/syllabus_management.html',
                         physics_chapters=physics_chapters,
                         chemistry_chapters=chemistry_chapters,
                         biology_chapters=biology_chapters)

@app.route('/admin/syllabus/add', methods=['GET', 'POST'])
@login_required
def add_chapter():
    """Add new chapter"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    form = ChapterForm()
    
    if form.validate_on_submit():
        chapter = SyllabusChapter(
            subject=form.subject.data,
            chapter_name=form.chapter_name.data,
            chapter_order=form.chapter_order.data,
            description=form.description.data,
            is_active=form.is_active.data,
            created_by_id=current_user.id
        )
        
        db.session.add(chapter)
        db.session.commit()
        
        # Add to existing users' progress
        users = User.query.filter_by(is_admin=False, is_active=True).all()
        for user in users:
            progress = ChapterProgress(
                user_id=user.id,
                subject=chapter.subject,
                chapter_name=chapter.chapter_name,
                chapter_order=chapter.chapter_order
            )
            db.session.add(progress)
        
        db.session.commit()
        
        flash(f'Chapter added: {chapter.chapter_name}', 'success')
        return redirect(url_for('admin_syllabus'))
    
    return render_template('admin/chapter_form.html', form=form, title='Add Chapter')

@app.route('/admin/syllabus/edit/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
def edit_chapter(chapter_id):
    """Edit chapter"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    chapter = SyllabusChapter.query.get_or_404(chapter_id)
    form = ChapterForm()
    
    if form.validate_on_submit():
        old_name = chapter.chapter_name
        
        chapter.subject = form.subject.data
        chapter.chapter_name = form.chapter_name.data
        chapter.chapter_order = form.chapter_order.data
        chapter.description = form.description.data
        chapter.is_active = form.is_active.data
        chapter.updated_at = datetime.utcnow()
        
        # Update in users' progress
        ChapterProgress.query.filter_by(
            subject=chapter.subject,
            chapter_name=old_name
        ).update({
            'chapter_name': chapter.chapter_name,
            'chapter_order': chapter.chapter_order
        })
        
        db.session.commit()
        
        flash(f'Chapter updated: {chapter.chapter_name}', 'success')
        return redirect(url_for('admin_syllabus'))
    
    if request.method == 'GET':
        form.subject.data = chapter.subject
        form.chapter_name.data = chapter.chapter_name
        form.chapter_order.data = chapter.chapter_order
        form.description.data = chapter.description
        form.is_active.data = chapter.is_active
    
    return render_template('admin/chapter_form.html', form=form, title='Edit Chapter', chapter=chapter)

@app.route('/admin/syllabus/delete/<int:chapter_id>', methods=['POST'])
@login_required
def delete_chapter(chapter_id):
    """Delete chapter"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    chapter = SyllabusChapter.query.get_or_404(chapter_id)
    chapter_name = chapter.chapter_name
    
    # Delete from users' progress
    ChapterProgress.query.filter_by(
        subject=chapter.subject,
        chapter_name=chapter.chapter_name
    ).delete()
    
    db.session.delete(chapter)
    db.session.commit()
    
    flash(f'Chapter deleted: {chapter_name}', 'warning')
    return redirect(url_for('admin_syllabus'))

# ============================================================================
# ADMIN - ANNOUNCEMENTS
# ============================================================================

@app.route('/admin/announcements')
@login_required
def admin_announcements():
    """Announcements management"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    
    return render_template('admin/announcements.html', announcements=announcements)

@app.route('/admin/announcements/add', methods=['GET', 'POST'])
@login_required
def add_announcement():
    """Add announcement"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    form = AnnouncementForm()
    
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data,
            message=form.message.data,
            announcement_type=form.announcement_type.data,
            show_on_pages=form.show_on_pages.data,
            is_active=form.is_active.data,
            expires_at=form.expires_at.data,
            created_by_id=current_user.id
        )
        
        db.session.add(announcement)
        db.session.commit()
        
        flash(f'Announcement created: {announcement.title}', 'success')
        return redirect(url_for('admin_announcements'))
    
    return render_template('admin/announcement_form.html', form=form, title='Create Announcement')

@app.route('/admin/announcements/edit/<int:announcement_id>', methods=['GET', 'POST'])
@login_required
def edit_announcement(announcement_id):
    """Edit announcement"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    announcement = Announcement.query.get_or_404(announcement_id)
    form = AnnouncementForm()
    
    if form.validate_on_submit():
        announcement.title = form.title.data
        announcement.message = form.message.data
        announcement.announcement_type = form.announcement_type.data
        announcement.show_on_pages = form.show_on_pages.data
        announcement.is_active = form.is_active.data
        announcement.expires_at = form.expires_at.data
        
        db.session.commit()
        
        flash(f'Announcement updated: {announcement.title}', 'success')
        return redirect(url_for('admin_announcements'))
    
    if request.method == 'GET':
        form.title.data = announcement.title
        form.message.data = announcement.message
        form.announcement_type.data = announcement.announcement_type
        form.show_on_pages.data = announcement.show_on_pages
        form.is_active.data = announcement.is_active
        form.expires_at.data = announcement.expires_at
    
    return render_template('admin/announcement_form.html', form=form, title='Edit Announcement', announcement=announcement)

@app.route('/admin/announcements/delete/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    """Delete announcement"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    announcement = Announcement.query.get_or_404(announcement_id)
    title = announcement.title
    
    db.session.delete(announcement)
    db.session.commit()
    
    flash(f'Announcement deleted: {title}', 'warning')
    return redirect(url_for('admin_announcements'))

@app.route('/admin/announcements/toggle/<int:announcement_id>', methods=['POST'])
@login_required
def toggle_announcement(announcement_id):
    """Toggle announcement active status"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    announcement = Announcement.query.get_or_404(announcement_id)
    announcement.is_active = not announcement.is_active
    
    db.session.commit()
    
    status = 'activated' if announcement.is_active else 'deactivated'
    flash(f'Announcement {status}: {announcement.title}', 'info')
    return redirect(url_for('admin_announcements'))

# ============================================================================
# ADMIN - INITIALIZE DEFAULT CONTENT
# ============================================================================

@app.route('/admin/init_content')
@login_required
def init_default_content():
    """Initialize default website content"""
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    # Check if content already exists
    if WebsiteContent.query.count() > 0:
        flash('Content already initialized!', 'warning')
        return redirect(url_for('admin_content'))
    
    # Default content
    default_contents = [
        {
            'page': 'home',
            'section': 'hero_title',
            'content': '🎯 NEET Study Tracker',
            'content_type': 'text'
        },
        {
            'page': 'home',
            'section': 'hero_subtitle',
            'content': 'Your complete study companion for NEET preparation. Track progress, log study time, analyze test scores, and stay motivated!',
            'content_type': 'text'
        },
        {
            'page': 'about',
            'section': 'mission',
            'content': 'NEET Study Tracker is a comprehensive web application designed specifically for NEET aspirants to help them stay organized, track their preparation progress, and achieve their medical education goals.',
            'content_type': 'text'
        },
        {
            'page': 'about',
            'section': 'description',
            'content': 'We understand that preparing for NEET is challenging and requires consistent effort, smart planning, and regular monitoring of progress. Our platform provides all the essential tools you need to succeed.',
            'content_type': 'text'
        }
    ]
    
    for content_data in default_contents:
        content = WebsiteContent(
            page=content_data['page'],
            section=content_data['section'],
            content=content_data['content'],
            content_type=content_data['content_type'],
            updated_by_id=current_user.id
        )
        db.session.add(content)
    
    db.session.commit()
    
    flash('Default content initialized successfully!', 'success')
    return redirect(url_for('admin_content'))

# ============================================================================
# ADMIN - PASSWORD MANAGEMENT
# ============================================================================

@app.route('/admin/user/<int:user_id>/reset_password', methods=['GET', 'POST'])
@login_required
def admin_reset_user_password(user_id):
    """Admin reset user password"""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot reset admin user password.', 'danger')
        return redirect(url_for('manage_users'))
    
    form = AdminPasswordResetForm()
    
    if form.validate_on_submit():
        # Set new password
        user.set_password(form.new_password.data)
        user.password_changed_at = datetime.utcnow()
        user.password_reset_by_id = current_user.id
        user.must_change_password = form.force_password_change.data
        
        db.session.commit()
        
        # Log admin action
        log = AdminLog(
            admin_id=current_user.id,
            action_type='password_reset',
            target_user_id=user.id,
            description=f'Reset password for user: {user.username}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Password reset successfully for {user.username}!', 'success')
        
        if form.force_password_change.data:
            flash(f'{user.username} must change password on next login.', 'info')
        
        # Show temporary password (optional - for admin to share with user)
        if form.notify_user.data:
            flash(f'Notification feature coming soon! Share this password with user: {form.new_password.data}', 'warning')
        else:
            flash(f'New password: {form.new_password.data} - Share this with the user securely.', 'warning')
        
        return redirect(url_for('view_user_progress', user_id=user.id))
    
    return render_template('admin/reset_password.html', form=form, user=user)

@app.route('/admin/user/<int:user_id>/generate_temp_password', methods=['POST'])
@login_required
def admin_generate_temp_password(user_id):
    """Admin generate temporary password"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        return jsonify({'error': 'Cannot reset admin password'}), 403
    
    # Generate secure random password
    import secrets
    import string
    
    # Generate 12-character password with letters, digits, and symbols
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
    
    # Set password
    user.set_password(temp_password)
    user.password_changed_at = datetime.utcnow()
    user.password_reset_by_id = current_user.id
    user.must_change_password = True
    
    db.session.commit()
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action_type='temp_password',
        target_user_id=user.id,
        description=f'Generated temporary password for: {user.username}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Temporary password generated for {user.username}!', 'success')
    flash(f'Password: {temp_password}', 'warning')
    flash('User MUST change this password on next login.', 'info')
    
    return redirect(url_for('view_user_progress', user_id=user.id))

# ============================================================================
# USER - FORCED PASSWORD CHANGE
# ============================================================================

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """User change password (including forced change)"""
    form = AdminPasswordResetForm()
    
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        current_user.password_changed_at = datetime.utcnow()
        current_user.must_change_password = False
        
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('change_password.html', form=form, forced=current_user.must_change_password)



# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ============================================================================
# RUN
# ============================================================================

# ============================================================================
# TEMPORARY MIGRATION ROUTE (Remove after running once)
# ============================================================================

@app.route('/admin/migrate_db')
@login_required
def migrate_db():
    """One-time database migration"""
    if not current_user.is_admin:
        return "Access denied", 403
    
    try:
        # Add new columns to users table
        with db.engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(db.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='must_change_password'
            """))
            
            if result.fetchone() is None:
                # Columns don't exist, add them
                conn.execute(db.text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE"))
                conn.execute(db.text("ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP"))
                conn.execute(db.text("ALTER TABLE users ADD COLUMN password_reset_by_id INTEGER REFERENCES users(id)"))
                conn.commit()
                
                return """
                <h1>✅ Migration Successful!</h1>
                <p>New password management fields have been added to the database.</p>
                <p><a href="/admin/dashboard">Go to Admin Dashboard</a></p>
                <p><strong>Note:</strong> You can now remove the /admin/migrate_db route from app.py</p>
                """
            else:
                return """
                <h1>✅ Already Migrated</h1>
                <p>The database already has the password management fields.</p>
                <p><a href="/admin/dashboard">Go to Admin Dashboard</a></p>
                """
    except Exception as e:
        db.session.rollback()
        return f"""
        <h1>❌ Migration Failed</h1>
        <p>Error: {str(e)}</p>
        <p><a href="/admin/dashboard">Go back</a></p>
        """


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
