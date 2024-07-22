import re

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import URL, InputRequired, Optional, Regexp

slug_pattern = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class NewPostForm(FlaskForm):
    title = StringField(validators=[InputRequired()])
    subtitle = StringField(validators=[InputRequired()])
    tags = StringField(
        render_kw={"placeholder": "Separate tags with ','"}, validators=[InputRequired()]
    )
    cover_url = StringField(
        render_kw={"placeholder": "Insert image url"}, validators=[Optional(), URL()]
    )
    custom_slug = StringField(
        render_kw={"placeholder": "Must be an url-friendly string"},
        validators=[Optional(), Regexp(slug_pattern)],
    )
    editor = TextAreaField()
    submit_ = SubmitField(label="Submit")


class EditPostForm(FlaskForm):
    title = StringField(validators=[InputRequired()])
    subtitle = StringField(validators=[InputRequired()])
    tags = StringField(
        render_kw={"placeholder": "Separate tags with ','"}, validators=[InputRequired()]
    )
    cover_url = StringField(
        render_kw={"placeholder": "Insert image url"}, validators=[Optional(), URL()]
    )
    custom_slug = StringField(
        render_kw={"placeholder": "Must be an url-friendly string"},
        validators=[Optional(), Regexp(slug_pattern)],
    )
    editor = TextAreaField()
    submit_ = SubmitField(label="Save Changes", render_kw={"onclick": "return validateUpdate()"})
