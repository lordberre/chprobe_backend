from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional

class ProbeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
#    currentlocation = StringField('Current location', render_kw={'readonly': True})
    location = StringField('Location',validators=[DataRequired()])
#    locationlist = SelectField('Select new location',validators=[Optional()])
    eventlog = TextAreaField('Event log', validators=[DataRequired()])
    refresh = SubmitField('Refresh Data')
    submit = SubmitField('Submit New data')
