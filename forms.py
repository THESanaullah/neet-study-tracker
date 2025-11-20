# Forms for NEET Study Tracker
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, DateField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional, NumberRange
from datetime import date

# ============================================================================
# AUTHENTICATION FORMS
# ============================================================================

class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Invalid email address')
    ])
    full_name = StringField('Full Name', validators=[Optional(), Length(max=128)])
    target_exam_year = IntegerField('Target NEET Year', validators=[
        Optional(),
        NumberRange(min=2024, max=2030, message='Please enter a valid year')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

# ============================================================================
# STUDY LOG FORM
# ============================================================================

class StudyLogForm(FlaskForm):
    """Study time logging form"""
    date = DateField('Date', validators=[DataRequired()], default=date.today)
    subject = SelectField('Subject (Optional)', 
                         choices=[('', 'All Subjects'), ('Physics', 'Physics'), 
                                 ('Chemistry', 'Chemistry'), ('Biology', 'Biology')],
                         validators=[Optional()])
    duration_minutes = IntegerField('Duration (minutes)', validators=[
        DataRequired(),
        NumberRange(min=1, max=1440, message='Duration must be between 1 and 1440 minutes')
    ])
    notes = TextAreaField('Notes (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Log Study Session')

# ============================================================================
# TEST SCORE FORM
# ============================================================================

class TestScoreForm(FlaskForm):
    """Mock test score tracking form"""
    test_name = StringField('Test Name', validators=[
        DataRequired(),
        Length(min=1, max=256, message='Test name must be between 1 and 256 characters')
    ])
    test_date = DateField('Test Date', validators=[DataRequired()], default=date.today)
    test_type = SelectField('Test Type',
                           choices=[
                               ('Full Length', 'Full Length Mock Test'),
                               ('Chapter Test', 'Chapter-wise Test'),
                               ('Subject Test', 'Subject Test'),
                               ('Online Test', 'Online Test Series'),
                               ('Offline Test', 'Offline Mock Test'),
                               ('Other', 'Other')
                           ],
                           validators=[DataRequired()])
    
    # Subject-wise scores (optional)
    physics_score = IntegerField('Physics Score', validators=[
        Optional(),
        NumberRange(min=0, max=1000, message='Score must be between 0 and 1000')
    ])
    physics_total = IntegerField('Physics Total Marks', validators=[
        Optional(),
        NumberRange(min=1, max=1000, message='Total marks must be between 1 and 1000')
    ])
    
    chemistry_score = IntegerField('Chemistry Score', validators=[
        Optional(),
        NumberRange(min=0, max=1000, message='Score must be between 0 and 1000')
    ])
    chemistry_total = IntegerField('Chemistry Total Marks', validators=[
        Optional(),
        NumberRange(min=1, max=1000, message='Total marks must be between 1 and 1000')
    ])
    
    biology_score = IntegerField('Biology Score', validators=[
        Optional(),
        NumberRange(min=0, max=1000, message='Score must be between 0 and 1000')
    ])
    biology_total = IntegerField('Biology Total Marks', validators=[
        Optional(),
        NumberRange(min=1, max=1000, message='Total marks must be between 1 and 1000')
    ])
    
    # Overall score (required)
    total_score = IntegerField('Total Score Obtained', validators=[
        DataRequired(),
        NumberRange(min=0, max=2000, message='Total score must be between 0 and 2000')
    ])
    total_marks = IntegerField('Total Marks', validators=[
        DataRequired(),
        NumberRange(min=1, max=2000, message='Total marks must be between 1 and 2000')
    ])
    
    notes = TextAreaField('Analysis Notes (Optional)', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Save Test Score')
    
    def validate_total_score(self, field):
        """Validate that total score doesn't exceed total marks"""
        if self.total_marks.data and field.data > self.total_marks.data:
            raise ValidationError('Total score cannot exceed total marks')
    
    def validate_physics_score(self, field):
        """Validate physics score"""
        if field.data and self.physics_total.data and field.data > self.physics_total.data:
            raise ValidationError('Physics score cannot exceed physics total marks')
    
    def validate_chemistry_score(self, field):
        """Validate chemistry score"""
        if field.data and self.chemistry_total.data and field.data > self.chemistry_total.data:
            raise ValidationError('Chemistry score cannot exceed chemistry total marks')
    
    def validate_biology_score(self, field):
        """Validate biology score"""
        if field.data and self.biology_total.data and field.data > self.biology_total.data:
            raise ValidationError('Biology score cannot exceed biology total marks')

# ============================================================================
# REVISION FORM
# ============================================================================

class RevisionForm(FlaskForm):
    """Revision logging form"""
    confidence_level = SelectField('Confidence Level',
                                  choices=[
                                      ('', 'Select confidence level'),
                                      ('1', '⭐ Very Low'),
                                      ('2', '⭐⭐ Low'),
                                      ('3', '⭐⭐⭐ Medium'),
                                      ('4', '⭐⭐⭐⭐ High'),
                                      ('5', '⭐⭐⭐⭐⭐ Very High')
                                  ],
                                  validators=[Optional()])
    notes = TextAreaField('Revision Notes (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Log Revision')
# ============================================================================
# CONTENT MANAGEMENT FORMS
# ============================================================================

class ContentEditForm(FlaskForm):
    """Website content editing form"""
    content = TextAreaField('Content', validators=[
        DataRequired(),
        Length(max=5000, message='Content must be less than 5000 characters')
    ], render_kw={'rows': 10})
    submit = SubmitField('Update Content')

class ChapterForm(FlaskForm):
    """Syllabus chapter management form"""
    subject = SelectField('Subject', 
                         choices=[('Physics', 'Physics'), 
                                 ('Chemistry', 'Chemistry'), 
                                 ('Biology', 'Biology')],
                         validators=[DataRequired()])
    chapter_name = StringField('Chapter Name', validators=[
        DataRequired(),
        Length(min=3, max=256, message='Chapter name must be between 3 and 256 characters')
    ])
    chapter_order = IntegerField('Order', validators=[
        DataRequired(),
        NumberRange(min=1, max=100, message='Order must be between 1 and 100')
    ])
    description = TextAreaField('Description (Optional)', validators=[
        Optional(),
        Length(max=500)
    ])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Chapter')

class AnnouncementForm(FlaskForm):
    """System announcement form"""
    title = StringField('Announcement Title', validators=[
        DataRequired(),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters')
    ])
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(max=1000, message='Message must be less than 1000 characters')
    ], render_kw={'rows': 5})
    announcement_type = SelectField('Type',
                                   choices=[
                                       ('info', '📘 Info'),
                                       ('success', '✅ Success'),
                                       ('warning', '⚠️ Warning'),
                                       ('danger', '🚨 Important')
                                   ],
                                   validators=[DataRequired()])
    show_on_pages = SelectField('Show On',
                               choices=[
                                   ('all', 'All Pages'),
                                   ('dashboard', 'Dashboard Only'),
                                   ('home', 'Home Page Only')
                               ],
                               validators=[DataRequired()])
    expires_at = DateField('Expires On (Optional)', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Create Announcement')
# ============================================================================
# ADMIN PASSWORD RESET FORM
# ============================================================================

class AdminPasswordResetForm(FlaskForm):
    """Admin force password reset form"""
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    notify_user = BooleanField('Send email notification to user', default=False)
    force_password_change = BooleanField('Force user to change password on next login', default=True)
    submit = SubmitField('Reset Password')
