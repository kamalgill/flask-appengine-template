
from google.appengine.api import users

from flask import render_template, flash, url_for, redirect

from application import app
from models import ExampleModel
from decorators import login_required
from forms import ExampleForm


@app.route('/')
def redirect_to_home():
    return redirect(url_for('list_examples'))


@app.route('/hello/<username>')
def say_hello(username):
    '''Contrived example to demonstrate Flask's url routing capabilities'''
    return 'Hello %s' % username


@app.route('/examples')
def list_examples():
    examples = ExampleModel.all()
    return render_template('list_examples.html', examples=examples)


@app.route('/example/new', methods = ['GET', 'POST'])
@login_required
def new_example():
    form = ExampleForm()
    if form.validate_on_submit():
        example = ExampleModel(
                    example_id = form.example_id.data,
                    example_title = form.example_title.data,
                    added_by = users.get_current_user()
                    )
        example.put()
        flash('Example successfully saved.')
        return redirect(url_for('list_examples'))
    return render_template('new_example.html', form=form)


# Error handlers #####
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

