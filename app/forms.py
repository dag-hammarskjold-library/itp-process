from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class MissingFieldReportForm(FlaskForm):
    authority = StringField('Authority#', validators=[DataRequired()])
    field = StringField('Field', validators=[DataRequired()])

class MissingSubfieldReportForm(FlaskForm):
    authority = StringField('Authority#', validators=[DataRequired()])
    field = StringField('Field', validators=[DataRequired()])
    subfield = StringField('Subfield', validators=[DataRequired()])