# -*- coding: utf-8 -*-

from flask.views import View


class PublicWarmup(View):

    def dispatch_request(self):
        return "I'm ready"
