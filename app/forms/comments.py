from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import Email, InputRequired, Optional

from app.config import RECAPTCHA_KEY


class CommentForm(FlaskForm):
    """
    Form for submitting a comment.

    Fields:
        name (StringField): Name of the commenter, input by the anonymous commenter or retrieved from a logged in user.
        email (StringField): Email of the commenter, input by the anonymous commenter or retrieved from a logged in user (optional).
        comment (TextAreaField): Content of the comment.
        submit_ (SubmitField): Submit button with ReCAPTCHA integration.
    """

    name = StringField(
        "Name",
        validators=[InputRequired(message="Name is required.")],
        render_kw={"placeholder": "Your Name"},
    )
    email = StringField(
        "Email",
        validators=[Email(message="Invalid email address."), Optional()],
        render_kw={"placeholder": "Your Email (optional)"},
    )
    comment = TextAreaField(
        "Comment",
        validators=[InputRequired(message="Comment cannot be empty.")],
        render_kw={"placeholder": "Your Comment"},
    )
    submit_ = SubmitField(
        "Submit",
        render_kw={
            "data-sitekey": RECAPTCHA_KEY,
            "data-callback": "onSubmit",
            "class": "btn btn-primary",
        },
    )
