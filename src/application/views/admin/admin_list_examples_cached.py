# -*- coding: utf-8 -*-

from flask.views import View

from flask import render_template

from models import ExampleModel

from decorators import login_required

from flask_cache import Cache

from application import app

cache = Cache(app)


class AdminListExamplesCached(View):

    @login_required
    @cache.cached(timeout=60)
    def dispatch_request(self):

        examples = ExampleModel.query()
        return render_template('list_examples_cached.html', examples=examples)
