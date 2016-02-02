# -*- coding: utf-8 -*-

from flask.views import View

from decorators import admin_required


class AdminSecret(View):

    @admin_required
    def dispatch_request(self):

        return 'Super-seekrit admin page.'
