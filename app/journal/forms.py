from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

EMOTION_CHOICES = [
    ("Happy", "Happy"),
    ("Neutral", "Neutral"),
    ("Sad", "Sad"),
    ("Angry", "Angry"),
    ("Stressed", "Stressed"),
]

class JournalEntryForm(FlaskForm):
    content = TextAreaField(
        "Content",
        validators=[DataRequired(message="Content is required"), Length(max=5000)],
    )
    user_emotion = SelectField(
        "How are you feeling?",
        choices=EMOTION_CHOICES,
        validators=[DataRequired(message="Select an emotion")],
    )
    submit = SubmitField("Save")