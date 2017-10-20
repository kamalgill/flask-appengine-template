# -*- coding: utf-8 -*-

from flask import flash, redirect, url_for, request
from flask.views import View
from flask_cache import Cache

from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError

from application import app
from models import ExampleModel
from decorators import login_required

cache = Cache(app)


class AdminDeleteExample(View):

    @login_required
    def dispatch_request(self, example_id):
        example = ExampleModel.get_by_id(example_id)
        if request.method == "POST":
            try:
                example.key.delete()
                cache.clear()
                flash(u'Example %s successfully deleted.' % example_id, 'success')
                return redirect(url_for('list_examples'))
            except CapabilityDisabledError:
                flash(u'App Engine Datastore is currently in read-only mode.', 'info')
                return redirect(url_for('list_examples'))
