from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import Email, InputRequired, Optional

from blogyourway.config import RECAPTCHA_KEY


class CommentForm(FlaskForm):
    name = StringField("Name", validators=[InputRequired()])
    email = StringField("Email", validators=[Email(), Optional()])
    comment = TextAreaField("Comment", validators=[InputRequired()])
    submit_ = SubmitField(
        "Submit", render_kw={"data-sitekey": RECAPTCHA_KEY, "data-callback": "onSubmit"}
    )
