import re

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import URL, InputRequired, Optional, Regexp

slug_pattern = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class NewPostForm(FlaskForm):
    """
    Form for creating a new post.

    Fields:
        title (StringField): Post title.
        subtitle (StringField): Post subtitle.
        tags (StringField): Tags associated with the post.
        cover_url (StringField): URL for the post cover image.
        custom_slug (StringField): Custom URL-friendly slug for the post.
        editor (TextAreaField): Post content.
        submit_ (SubmitField): Submit button.
    """

    title = StringField(validators=[InputRequired(message="Title is required.")])
    subtitle = StringField(validators=[InputRequired(message="Subtitle is required.")])
    tags = StringField(
        render_kw={"placeholder": "Separate tags with ','"},
        validators=[InputRequired(message="Tags are required.")],
    )
    cover_url = StringField(
        render_kw={"placeholder": "Insert image URL"},
        validators=[Optional(), URL(message="Invalid URL.")],
    )
    custom_slug = StringField(
        render_kw={"placeholder": "Must be an URL-friendly string"},
        validators=[Optional(), Regexp(slug_pattern, message="Slug must be URL-friendly.")],
    )
    editor = TextAreaField()
    submit_ = SubmitField(label="Submit", render_kw={"onclick": "return validateNewPost()"})


class EditPostForm(FlaskForm):
    """
    Form for editing an existing post.

    Fields:
        title (StringField): Post title.
        subtitle (StringField): Post subtitle.
        tags (StringField): Tags associated with the post.
        cover_url (StringField): URL for the post cover image.
        custom_slug (StringField): Custom URL-friendly slug for the post.
        editor (TextAreaField): Post content.
        submit_ (SubmitField): Submit button.
    """

    title = StringField(validators=[InputRequired(message="Title is required.")])
    subtitle = StringField(validators=[InputRequired(message="Subtitle is required.")])
    tags = StringField(
        render_kw={"placeholder": "Separate tags with ','"},
        validators=[InputRequired(message="Tags are required.")],
    )
    cover_url = StringField(
        render_kw={"placeholder": "Insert image URL"},
        validators=[Optional(), URL(message="Invalid URL.")],
    )
    custom_slug = StringField(
        render_kw={"placeholder": "Must be a URL-friendly string"},
        validators=[Optional(), Regexp(slug_pattern, message="Slug must be URL-friendly.")],
    )
    editor = TextAreaField()
    submit_ = SubmitField(label="Save Changes", render_kw={"onclick": "return validateUpdate()"})
