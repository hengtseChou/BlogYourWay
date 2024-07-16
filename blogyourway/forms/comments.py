from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional

from blogyourway.config import RECAPTCHA_KEY


class CommentForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[Email(), Optional()])
    comment = TextAreaField("Comment", validators=[DataRequired()])
    submit_ = SubmitField(
        "Submit", render_kw={"data-sitekey": RECAPTCHA_KEY, "data-callback": "onSubmit"}
    )
