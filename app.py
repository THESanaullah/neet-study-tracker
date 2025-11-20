# Main Flask application for NEET Study Tracker
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
from config import Config
from models import db, User, ChapterProgress, StudyLog, TestScore, RevisionLog, PomodoroSession, AdminLog
from forms import RegistrationForm, LoginForm, StudyLogForm, TestScoreForm, RevisionForm
from decorators import admin_required, active_required
from syllabus_data import NEET_SYLLABUS, get_chapters_by_subject
import json

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
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
# INITIALIZATION & DATABASE SETUP
# ============================================================================

@app.before_request
def initialize_database():
    """Create database tables and admin user on first run"""
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

def initialize_user_chapters(user):
    """Initialize chapter progress records for new user"""
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
            is_active=False  # Requires admin approval
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Initialize chapter progress for user
        initialize_user_chapters(user)
        
        flash('Registration successful! Your account is pending admin approval. You will be notified once approved.', 'success')
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
            flash('Your account is pending admin approval. Please wait for activation.', 'warning')
            return redirect(url_for('login'))
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect to appropriate dashboard
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
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# ============================================================================
# USER DASHBOARD ROUTES
# ============================================================================

@app.route('/dashboard')
@login_required
@active_required
def dashboard():
    """Main user dashboard with syllabus tracker"""
    # Get chapter progress for all subjects
    physics_chapters = ChapterProgress.query.filter_by(
        user_id=current_user.id, 
        subject='Physics'
    ).order_by(ChapterProgress.chapter_order).all()
    
    chemistry_chapters = ChapterProgress.query.filter_by(
        user_id=current_user.id,
        subject='Chemistry'
    ).order_by(ChapterProgress.chapter_order).all()
    
    biology_chapters = ChapterProgress.query.filter_by(
        user_id=current_user.id,
        subject='Biology'
    ).order_by(ChapterProgress.chapter_order).all()
    
    # Calculate progress percentages
    total_chapters = len(physics_chapters) + len(chemistry_chapters) + len(biology_chapters)
    completed_chapters = sum(1 for ch in physics_chapters + chemistry_chapters + biology_chapters if ch.is_completed)
    overall_progress = round((completed_chapters / total_chapters * 100), 1) if total_chapters > 0 else 0
    
    physics_progress = current_user.get_subject_progress('Physics')
    chemistry_progress = current_user.get_subject_progress('Chemistry')
    biology_progress = current_user.get_subject_progress('Biology')
    
    # Get recent study stats
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    total_study_time_week = db.session.query(db.func.sum(StudyLog.duration_minutes)).filter(
        StudyLog.user_id == current_user.id,
        StudyLog.date >= week_ago
    ).scalar() or 0
    
    total_study_time_week_hours = round(total_study_time_week / 60, 1)
    
    # Get study streak
    study_streak = calculate_study_streak(current_user.id)
    
    # Get recent test scores
    recent_tests = TestScore.query.filter_by(user_id=current_user.id).order_by(
        TestScore.test_date.desc()
    ).limit(5).all()
    
    # Get chapters needing revision (not revised in 7+ days)
    revision_threshold = datetime.utcnow() - timedelta(days=app.config['REVISION_REMINDER_DAYS'])
    chapters_need_revision = ChapterProgress.query.filter(
        ChapterProgress.user_id == current_user.id,
        ChapterProgress.revised == True,
        ChapterProgress.last_revised_date < revision_threshold
    ).count()
    
    # Get Pomodoro stats for today
    pomodoro_today = PomodoroSession.query.filter_by(
        user_id=current_user.id,
        session_date=today
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
                         total_study_time_week=total_study_time_week_hours,
                         study_streak=study_streak,
                         recent_tests=recent_tests,
                         chapters_need_revision=chapters_need_revision,
                         pomodoro_count_today=pomodoro_count_today)

def calculate_study_streak(user_id):
    """Calculate consecutive days studied"""
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
        
        # Limit check to avoid infinite loop
        if streak > 365:
            break
    
    return streak

@app.route('/update_chapter/<int:chapter_id>', methods=['POST'])
@login_required
@active_required
def update_chapter(chapter_id):
    """Update chapter progress checkboxes"""
    chapter = ChapterProgress.query.get_or_404(chapter_id)
    
    # Security: Ensure user owns this chapter
    if chapter.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update checkboxes
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
    
    # Update completion status
    chapter.update_completion_status()
    chapter.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_completed': chapter.is_completed,
        'revision_count': chapter.revision_count
    })

# ============================================================================
# STUDY LOG ROUTES
# ============================================================================

@app.route('/study_log', methods=['GET', 'POST'])
@login_required
@active_required
def study_log():
    """Study time logging page"""
    form = StudyLogForm()
    
    # Set default date to today
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
        
        flash(f'Study session logged: {form.duration_minutes.data} minutes on {form.date.data}', 'success')
        return redirect(url_for('study_log'))
    
    # Get recent study logs
    logs = StudyLog.query.filter_by(user_id=current_user.id).order_by(
        StudyLog.date.desc()
    ).limit(30).all()
    
    # Calculate statistics
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
@active_required
def study_stats():
    """Get study statistics for charts"""
    days = request.args.get('days', 30, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    logs = StudyLog.query.filter(
        StudyLog.user_id == current_user.id,
        StudyLog.date >= start_date
    ).order_by(StudyLog.date).all()
    
    # Prepare data for charts
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
@active_required
def test_tracker():
    """Mock test score tracking"""
    form = TestScoreForm()
    
    # Set default date to today
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
        
        flash(f'Test score saved: {test.test_name} - {test.percentage}%', 'success')
        return redirect(url_for('test_tracker'))
    
    # Get all test scores
    tests = TestScore.query.filter_by(user_id=current_user.id).order_by(
        TestScore.test_date.desc()
    ).all()
    
    return render_template('test_tracker.html', form=form, tests=tests)

@app.route('/test_stats')
@login_required
@active_required
def test_stats():
    """Get test statistics for charts"""
    tests = TestScore.query.filter_by(user_id=current_user.id).order_by(
        TestScore.test_date
    ).all()
    
    dates = [t.test_date.strftime('%Y-%m-%d') for t in tests]
    percentages = [t.percentage for t in tests]
    
    # Subject-wise performance
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

# (Continue in next part...)
# ... (continuing from Part 1)

# ============================================================================
# REVISION TRACKING ROUTES
# ============================================================================

@app.route('/revision')
@login_required
@active_required
def revision():
    """Revision tracking dashboard"""
    # Get all chapters with revision history
    chapters = ChapterProgress.query.filter_by(user_id=current_user.id).order_by(
        ChapterProgress.subject, ChapterProgress.chapter_order
    ).all()
    
    # Get chapters needing revision (not revised in 7+ days)
    revision_threshold = datetime.utcnow() - timedelta(days=app.config['REVISION_REMINDER_DAYS'])
    chapters_need_revision = [ch for ch in chapters 
                             if ch.revised and ch.last_revised_date 
                             and ch.last_revised_date < revision_threshold]
    
    # Get recent revisions across all chapters
    recent_revisions = RevisionLog.query.filter_by(user_id=current_user.id).order_by(
        RevisionLog.revision_date.desc()
    ).limit(20).all()
    
    return render_template('revision.html',
                         chapters=chapters,
                         chapters_need_revision=chapters_need_revision,
                         recent_revisions=recent_revisions)

@app.route('/log_revision/<int:chapter_id>', methods=['POST'])
@login_required
@active_required
def log_revision(chapter_id):
    """Log a revision for a specific chapter"""
    chapter = ChapterProgress.query.get_or_404(chapter_id)
    
    # Security check
    if chapter.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Increment revision count
    chapter.revision_count += 1
    chapter.last_revised_date = datetime.utcnow()
    chapter.revised = True
    chapter.update_completion_status()
    
    # Create revision log entry
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
# POMODORO TIMER API ROUTES
# ============================================================================

@app.route('/pomodoro/start', methods=['POST'])
@login_required
@active_required
def pomodoro_start():
    """Start a Pomodoro session"""
    data = request.get_json()
    subject = data.get('subject')
    
    return jsonify({'success': True, 'message': 'Pomodoro started'})

@app.route('/pomodoro/complete', methods=['POST'])
@login_required
@active_required
def pomodoro_complete():
    """Log a completed Pomodoro session"""
    data = request.get_json()
    today = date.today()
    
    # Get or create today's Pomodoro session record
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
    
    # Update session
    session.sessions_completed += 1
    session.total_focus_time += 25  # 25 minutes per Pomodoro
    if data.get('subject'):
        session.subject = data['subject']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'sessions_today': session.sessions_completed,
        'total_minutes': session.total_focus_time
    })

@app.route('/pomodoro/stats')
@login_required
@active_required
def pomodoro_stats():
    """Get Pomodoro statistics"""
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
    """Admin login page"""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('admin_login'))
        
        if not user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome, Admin {user.username}!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/admin_login.html', form=form)

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard overview"""
    # Get statistics
    total_users = User.query.filter_by(is_admin=False).count()
    active_users = User.query.filter_by(is_admin=False, is_active=True).count()
    pending_users = User.query.filter_by(is_admin=False, is_active=False).count()
    
    # Recent registrations
    recent_users = User.query.filter_by(is_admin=False).order_by(
        User.created_at.desc()
    ).limit(10).all()
    
    # Recent admin actions
    recent_actions = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(15).all()
    
    return render_template('admin/admin_dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         pending_users=pending_users,
                         recent_users=recent_users,
                         recent_actions=recent_actions)

@app.route('/admin/pending_users')
@login_required
@admin_required
def pending_users():
    """View pending user registrations"""
    pending = User.query.filter_by(is_admin=False, is_active=False).order_by(
        User.created_at.desc()
    ).all()
    
    return render_template('admin/pending_users.html', pending_users=pending)

@app.route('/admin/approve_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    """Approve a pending user registration"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot modify admin accounts.', 'danger')
        return redirect(url_for('pending_users'))
    
    user.is_active = True
    user.approved_at = datetime.utcnow()
    user.approved_by_id = current_user.id
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action_type='approve',
        target_user_id=user.id,
        description=f'Approved user: {user.username}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'User {user.username} has been approved and can now log in.', 'success')
    return redirect(url_for('pending_users'))

@app.route('/admin/reject_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    """Reject and delete a pending user registration"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot delete admin accounts.', 'danger')
        return redirect(url_for('pending_users'))
    
    username = user.username
    
    # Log admin action before deletion
    log = AdminLog(
        admin_id=current_user.id,
        action_type='reject',
        target_user_id=user.id,
        description=f'Rejected and deleted user: {username}'
    )
    db.session.add(log)
    
    # Delete user and all related data (cascades automatically)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been rejected and removed from the system.', 'info')
    return redirect(url_for('pending_users'))

@app.route('/admin/manage_users')
@login_required
@admin_required
def manage_users():
    """Manage all registered users"""
    page = request.args.get('page', 1, type=int)
    users = User.query.filter_by(is_admin=False).order_by(
        User.created_at.desc()
    ).paginate(page=page, per_page=app.config['USERS_PER_PAGE'], error_out=False)
    
    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/view_user/<int:user_id>')
@login_required
@admin_required
def view_user_progress(user_id):
    """View a specific user's dashboard in read-only mode"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot view admin user progress.', 'warning')
        return redirect(url_for('manage_users'))
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action_type='view',
        target_user_id=user.id,
        description=f'Viewed progress for user: {user.username}'
    )
    db.session.add(log)
    db.session.commit()
    
    # Get user's progress data
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
    
    # Recent activity
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
@admin_required
def deactivate_user(user_id):
    """Deactivate a user account"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot deactivate admin accounts.', 'danger')
        return redirect(url_for('manage_users'))
    
    user.is_active = False
    
    log = AdminLog(
        admin_id=current_user.id,
        action_type='deactivate',
        target_user_id=user.id,
        description=f'Deactivated user: {user.username}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'User {user.username} has been deactivated.', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Permanently delete a user account"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot delete admin accounts.', 'danger')
        return redirect(url_for('manage_users'))
    
    username = user.username
    
    log = AdminLog(
        admin_id=current_user.id,
        action_type='delete',
        target_user_id=user.id,
        description=f'Permanently deleted user: {username}'
    )
    db.session.add(log)
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been permanently deleted.', 'warning')
    return redirect(url_for('manage_users'))

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
