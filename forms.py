from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, DateField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange
from datetime import date

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[Optional(), Length(max=128)])
    target_exam_year = IntegerField('Target Exam Year', validators=[Optional(), NumberRange(min=2024, max=2030)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class StudyLogForm(FlaskForm):
    date = DateField('Date', default=date.today, validators=[DataRequired()])
    subject = SelectField('Subject', choices=[('', 'All Subjects'), ('Physics', 'Physics'), ('Chemistry', 'Chemistry'), ('Biology', 'Biology')])
    duration_minutes = IntegerField('Duration (minutes)', validators=[DataRequired(), NumberRange(min=1, max=1440)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Log Study Session')

class TestScoreForm(FlaskForm):
    test_name = StringField('Test Name', validators=[DataRequired(), Length(max=256)])
    test_date = DateField('Test Date', default=date.today, validators=[DataRequired()])
    test_type = SelectField('Test Type', choices=[('Full Length', 'Full Length'), ('Chapter Test', 'Chapter Test'), ('Subject Test', 'Subject Test')])
    physics_score = IntegerField('Physics Score', validators=[Optional(), NumberRange(min=0, max=1000)])
    physics_total = IntegerField('Physics Total', validators=[Optional(), NumberRange(min=0, max=1000)])
    chemistry_score = IntegerField('Chemistry Score', validators=[Optional(), NumberRange(min=0, max=1000)])
    chemistry_total = IntegerField('Chemistry Total', validators=[Optional(), NumberRange(min=0, max=1000)])
    biology_score = IntegerField('Biology Score', validators=[Optional(), NumberRange(min=0, max=1000)])
    biology_total = IntegerField('Biology Total', validators=[Optional(), NumberRange(min=0, max=1000)])
    total_score = IntegerField('Total Score', validators=[DataRequired(), NumberRange(min=0, max=2000)])
    total_marks = IntegerField('Total Marks', validators=[DataRequired(), NumberRange(min=1, max=2000)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Save Test Score')

class QuestionPracticeForm(FlaskForm):
    subject = SelectField('Subject', choices=[('Physics', 'Physics'), ('Chemistry', 'Chemistry'), ('Biology', 'Biology')], validators=[DataRequired()])
    chapter_name = StringField('Chapter Name', validators=[DataRequired(), Length(max=256)])
    questions_count = IntegerField('Questions Practiced', validators=[DataRequired(), NumberRange(min=1, max=10000)])
    date = DateField('Date', default=date.today, validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Add Practice Log')

class AdminPasswordResetForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')
