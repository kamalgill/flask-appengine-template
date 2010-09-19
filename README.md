
Flask on App Engine Project Template
====================================

Boilerplate project template for running a Flask-based application on Google App Engine (Python)


About Flask
-----------
Flask is a BSD-licensed microframework for Python based on Werkzeug, Jinja 2 and good intentions.

Flask runs incredibly well on Google App Engine.

See <http://flask.pocoo.org> for more info.


Setup Instructions
------------------
1. Download this repository via `git clone git@github.com:kamalgill/flask-appengine-template.git` 
   or download the tarball at <http://github.com/kamalgill/flask-appengine-template/tarball/master>
2. Set the application id in `src/app.yaml`
3. Configure datastore models at src/application/models.py
4. Configure application views and URL routes at src/application/views.py
5. Configure forms at src/application/forms.py
6. Add a `secret_keys.py` file at `src/application/secret_keys.py`, with the following contents:

<pre class="console">
	CSRF_SECRET_KEY = '{MY_SECRET_CSRF_KEY}'
	SESSION_KEY = '{MY_SECRET_SESSION_KEY}'
</pre>

where the keys are a randomized string of characters


Front-end Customization Instructions
------------------------------------
1. Customize the main HTML template at src/application/static/templates/base.html
2. Customize CSS styles at src/application/static/css/main.css
3. Add custom JavaScript code at src/application/static/js/main.js


Testing the Application (Development Server)
-----------------------
Using App Engine's development server:
<pre class="console">
	dev_appserver.py src/
</pre>
Assuming the latest App Engine SDK is installed, the test environment is available at <http://localhost:8080>


Deploying the Application
-------------------------
<pre class="console">
	appcfg.py update src/
</pre>


Credits
-------
Project template layout was heavily inspired by Francisco Souza's [gaeseries flask project][1]

HTML5-based main template (templates/base.html) and base CSS styles (static/css/style.css) extracted from [HTML5 Boilerplate][2]


[1]: http://github.com/franciscosouza/gaeseries/tree/flask
[2]: http://html5boilerplate.com/
