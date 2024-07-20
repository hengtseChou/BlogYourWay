import re

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import URL, InputRequired, Optional, Regexp

slug_pattern = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class NewProjectForm(FlaskForm):
    title = StringField(validators=[InputRequired()])
    desc = StringField(validators=[InputRequired()])
    tags = StringField(
        render_kw={"placeholder": "Separate tags with ','"}, validators=[InputRequired()]
    )
    url0 = StringField(validators=[InputRequired(), URL()], render_kw={"placeholder": "URL"})
    url1 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    url2 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    url3 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    url4 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    caption0 = StringField(validators=[Optional()], render_kw={"placeholder": "caption"})
    caption1 = StringField(validators=[Optional()], render_kw={"placeholder": "caption"})
    caption2 = StringField(validators=[Optional()], render_kw={"placeholder": "caption"})
    caption3 = StringField(validators=[Optional()], render_kw={"placeholder": "caption"})
    caption4 = StringField(validators=[Optional()], render_kw={"placeholder": "caption"})
    custom_slug = StringField(
        render_kw={"placeholder": "Must be an url-friendly string"},
        validators=[Optional(), Regexp(slug_pattern)],
    )
    editor = TextAreaField()
    submit_ = SubmitField(label="Submit", render_kw={"onclick": "return validateNewProject()"})


class EditProjectForm(FlaskForm):
    title = StringField(validators=[InputRequired()])
    desc = StringField(validators=[InputRequired()])
    tags = StringField(
        render_kw={"placeholder": "Separate tags with ','"}, validators=[InputRequired()]
    )
    url0 = StringField(validators=[InputRequired(), URL()], render_kw={"placeholder": "URL"})
    url1 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    url2 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    url3 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    url4 = StringField(validators=[Optional(), URL()], render_kw={"placeholder": "URL"})
    caption0 = StringField(validators=[Optional()], render_kw={"placeholder": "caption"})
    caption1 = StringField(validators=[Optional()], render_kw={"placeholder": "caption"})
    caption2 = StringField(validators=[Optional()], render_kw={"placeholder": "caption"})
    caption3 = StringField(validators=[Optional()], render_kw={"placeholder": "caption"})
    caption4 = StringField(validators=[Optional()], render_kw={"placeholder": "caption"})
    custom_slug = StringField(
        render_kw={"placeholder": "Must be an url-friendly string"},
        validators=[Optional(), Regexp(slug_pattern)],
    )
    editor = TextAreaField()
    submit_ = SubmitField(label="Submit")
