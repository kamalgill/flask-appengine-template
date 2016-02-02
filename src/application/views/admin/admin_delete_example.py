# -*- coding: utf-8 -*-

from flask.views import View

from flask import flash, redirect, url_for, request

from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError

from models import ExampleModel

from decorators import login_required


class AdminDeleteExample(View):

    @login_required
    def dispatch_request(self, example_id):
        example = ExampleModel.get_by_id(example_id)
        if request.method == "POST":
            try:
                example.key.delete()
                flash(u'Example %s successfully deleted.' % example_id, 'success')
                return redirect(url_for('list_examples'))
            except CapabilityDisabledError:
                flash(u'App Engine Datastore is currently in read-only mode.', 'info')
                return redirect(url_for('list_examples'))
