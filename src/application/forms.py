"""
forms.py

Web forms based on Flask-WTForms

See: http://flask.pocoo.org/docs/patterns/wtforms/
     http://wtforms.simplecodes.com/

"""

from flask_wtf import form
from wtforms import fields, validators
from wtforms.ext.appengine.ndb import model_form

from models import ExampleModel


class ClassicExampleForm(form.FlaskForm):
    example_name = fields.StringField('Name', validators=[validators.DataRequired()])
    example_description = fields.TextAreaField('Description', validators=[validators.DataRequired()])


# App Engine ndb model form example
ExampleForm = model_form(ExampleModel, form.FlaskForm, field_args={
    'example_name': dict(validators=[validators.DataRequired()]),
    'example_description': dict(validators=[validators.DataRequired()]),
})
