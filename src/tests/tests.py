#!/usr/bin/env python
# encoding: utf-8
"""
tests.py

"""
import os
import unittest

from google.appengine.ext import testbed

import main
from application import models

class DemoTestCase(unittest.TestCase):
    def setUp(self):
        # Flask apps testing. See: http://flask.pocoo.org/docs/testing/
        main.app.config['TESTING'] = True
        main.app.config['CSRF_ENABLED'] = False
        self.app = main.app.test_client()
        # Setups app engine test bed. See: http://code.google.com/appengine/docs/python/tools/localunittesting.html#Introducing_the_Python_Testing_Utilities
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_user_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def setCurrentUser(self, email, user_id, is_admin=False):
        os.environ['USER_EMAIL'] = email or ''
        os.environ['USER_ID'] = user_id or ''
        os.environ['USER_IS_ADMIN'] = '1' if is_admin else '0'

    def logoutCurrentUser():
        setCurrentUser(None, None)

    def test_home_redirects(self):
        rv = self.app.get('/')
        assert rv.status == '302 FOUND'    

    def test_says_hello(self):
        rv = self.app.get('/hello/world')
        assert 'Hello world' in rv.data

    def test_displays_no_data(self):
        rv = self.app.get('/examples')
        assert 'No examples yet' in rv.data

    def test_inserts_data(self):
        self.setCurrentUser(u'john@example.com', u'123')
        rv = self.app.post('/example/new', data=dict(
            example_id='42',
            example_title='An example'
        ), follow_redirects=True)
        assert 'Example successfully saved' in rv.data

        rv = self.app.get('/examples')
        assert 'No examples yet' not in rv.data
        assert 'An example' in rv.data
    
    def test_admin_login(self):
        #Anonymous
        rv = self.app.get('/admin_only')
        assert rv.status == '302 FOUND'
        #Normal user
        self.setCurrentUser(u'john@example.com', u'123')
        rv = self.app.get('/admin_only')
        assert rv.status == '302 FOUND'
        #Admin
        self.setCurrentUser(u'john@example.com', u'123', True)
        rv = self.app.get('/admin_only')
        assert rv.status == '200 OK'

    def test_404(self):
        rv = self.app.get('/missing')
        assert rv.status == '404 NOT FOUND'
        assert '<h1>Not found</h1>' in rv.data

    
if __name__ == '__main__':
    unittest.main()
