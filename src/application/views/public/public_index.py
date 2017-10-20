# -*- coding: utf-8 -*-

from flask import redirect, url_for
from flask.views import View


class PublicIndex(View):

    def dispatch_request(self):
        return redirect(url_for('list_examples'))
