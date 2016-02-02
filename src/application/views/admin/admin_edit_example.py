# -*- coding: utf-8 -*-

from flask.views import View

from flask import flash, redirect, url_for, render_template, request

from forms import ExampleForm
from models import ExampleModel

from decorators import login_required


class AdminEditExample(View):

    @login_required
    def dispatch_request(self, example_id):
        example = ExampleModel.get_by_id(example_id)
        form = ExampleForm(obj=example)
        if request.method == "POST":
            if form.validate_on_submit():
                example.example_name = form.data.get('example_name')
                example.example_description = form.data.get('example_description')
                example.put()
                flash(u'Example %s successfully saved.' % example_id, 'success')
                return redirect(url_for('list_examples'))
        return render_template('edit_example.html', example=example, form=form)
