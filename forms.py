# WTForms for secure form handling and validation
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField, SelectField, DateField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from models import User

class RegistrationForm(FlaskForm):
    """User registration form with validation"""
    username = StringField('Username', 
                          validators=[DataRequired(), Length(min=3, max=80)],
                          render_kw={"placeholder": "Choose a username"})
    
    email = StringField('Email', 
                       validators=[DataRequired(), Email()],
                       render_kw={"placeholder": "your.email@example.com"})
    
    full_name = StringField('Full Name',
                           validators=[Optional(), Length(max=100)],
                           render_kw={"placeholder": "Your full name (optional)"})
    
    target_exam_year = IntegerField('Target NEET Year',
                                   validators=[Optional(), NumberRange(min=2024, max=2030)],
                                   render_kw={"placeholder": "2025"})
    
    password = PasswordField('Password', 
                            validators=[DataRequired(), Length(min=6)],
                            render_kw={"placeholder": "Min 6 characters"})
    
    confirm_password = PasswordField('Confirm Password',
                                    validators=[DataRequired(), EqualTo('password', message='Passwords must match')],
                                    render_kw={"placeholder": "Re-enter password"})
    
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Check if username already exists"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Check if email already exists"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', 
                          validators=[DataRequired()],
                          render_kw={"placeholder": "Your username"})
    
    password = PasswordField('Password', 
                            validators=[DataRequired()],
                            render_kw={"placeholder": "Your password"})
    
    remember_me = BooleanField('Remember Me')
    
    submit = SubmitField('Login')


class StudyLogForm(FlaskForm):
    """Form to log daily study time"""
    date = DateField('Study Date', 
                    validators=[DataRequired()],
                    format='%Y-%m-%d')
    
    subject = SelectField('Subject (Optional)',
                         choices=[('', 'All Subjects'), ('Physics', 'Physics'), 
                                 ('Chemistry', 'Chemistry'), ('Biology', 'Biology')],
                         validators=[Optional()])
    
    duration_minutes = IntegerField('Duration (minutes)',
                                   validators=[DataRequired(), NumberRange(min=1, max=1440)],
                                   render_kw={"placeholder": "e.g., 120"})
    
    notes = TextAreaField('Notes (Optional)',
                         validators=[Optional(), Length(max=500)],
                         render_kw={"placeholder": "What did you study today?"})
    
    submit = SubmitField('Log Study Time')


class TestScoreForm(FlaskForm):
    """Form to log mock test scores"""
    test_name = StringField('Test Name',
                           validators=[DataRequired(), Length(max=200)],
                           render_kw={"placeholder": "e.g., ALLEN Mock Test 1"})
    
    test_date = DateField('Test Date',
                         validators=[DataRequired()],
                         format='%Y-%m-%d')
    
    test_type = SelectField('Test Type',
                           choices=[('Full Test', 'Full Test'), 
                                   ('Physics Only', 'Physics Only'),
                                   ('Chemistry Only', 'Chemistry Only'),
                                   ('Biology Only', 'Biology Only'),
                                   ('PCB Combined', 'PCB Combined')],
                           validators=[DataRequired()])
    
    # Subject-wise scores
    physics_score = IntegerField('Physics Score', validators=[Optional(), NumberRange(min=0)])
    physics_total = IntegerField('Physics Total', validators=[Optional(), NumberRange(min=0)])
    
    chemistry_score = IntegerField('Chemistry Score', validators=[Optional(), NumberRange(min=0)])
    chemistry_total = IntegerField('Chemistry Total', validators=[Optional(), NumberRange(min=0)])
    
    biology_score = IntegerField('Biology Score', validators=[Optional(), NumberRange(min=0)])
    biology_total = IntegerField('Biology Total', validators=[Optional(), NumberRange(min=0)])
    
    # Overall scores
    total_score = IntegerField('Total Score',
                              validators=[DataRequired(), NumberRange(min=0)],
                              render_kw={"placeholder": "e.g., 540"})
    
    total_marks = IntegerField('Total Marks',
                              validators=[DataRequired(), NumberRange(min=1)],
                              render_kw={"placeholder": "e.g., 720"})
    
    notes = TextAreaField('Analysis Notes (Optional)',
                         validators=[Optional(), Length(max=1000)],
                         render_kw={"placeholder": "Weak areas, strategy notes, etc."})
    
    submit = SubmitField('Save Test Score')


class RevisionForm(FlaskForm):
    """Form to log chapter revision"""
    revision_date = DateField('Revision Date',
                             validators=[DataRequired()],
                             format='%Y-%m-%d')
    
    confidence_level = SelectField('Confidence Level',
                                  choices=[('', 'Select confidence'),
                                          ('1', '1 - Need more practice'),
                                          ('2', '2 - Somewhat confident'),
                                          ('3', '3 - Moderately confident'),
                                          ('4', '4 - Very confident'),
                                          ('5', '5 - Fully mastered')],
                                  validators=[Optional()])
    
    notes = TextAreaField('Revision Notes (Optional)',
                         validators=[Optional(), Length(max=1000)],
                         render_kw={"placeholder": "Key points, doubts, formulas to remember..."})
    
    submit = SubmitField('Log Revision')
