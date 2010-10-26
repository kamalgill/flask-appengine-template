
Flask on App Engine Project Template
====================================

Boilerplate project template for running a Flask-based application on 
Google App Engine (Python)


About Flask
-----------
[Flask][flask] is a BSD-licensed microframework for Python based on 
[Werkzeug][wz], [Jinja 2][jinja2] and good intentions.

See <http://flask.pocoo.org> for more info.


Setup/Configuration
-------------------
1. Download this repository via 
   `git clone git@github.com:kamalgill/flask-appengine-template.git` 
   or download the tarball at 
   <http://github.com/kamalgill/flask-appengine-template/tarball/master>
2. Copy the src/ folder to your application's root folder
3. Set the application id in `src/app.yaml`
4. Configure datastore models at `src/application/models.py`
5. Configure application views at `src/application/views.py`
6. Configure URL routes at `src/application/urls.py`
7. Configure forms at `src/application/forms.py`
8. Add a `secret_keys.py` file at `src/application/secret_keys.py`, with 
   the following contents:

<pre class="console">
	CSRF_SECRET_KEY = '{MY_SECRET_CSRF_KEY}'
	SESSION_KEY = '{MY_SECRET_SESSION_KEY}'
</pre>

where the keys are a randomized string of characters.

Or, run the `generate_keys.py` script at `src/application/generate_keys.py` 
to generate the keys file.

Note: Copy the .gitignore file from the tarball folder's root to your git 
repository root to keep the secret_keys module out of version control.


Front-end Customization
-----------------------
1. Customize the main HTML template at 
   `src/application/static/templates/base.html`
2. Customize CSS styles at `src/application/static/css/main.css`
3. Add custom JavaScript code at `src/application/static/js/main.js`
4. Customize favicon at `src/application/static/img/favicon.ico`
5. Customize 404 page at `src/aplication/templates/404.html`


Testing the Application
-----------------------
To test the application using App Engine's development server, 
use [dev_appserver.py][devserver]

<pre class="console">
	dev_appserver.py src/
</pre>

Assuming the latest App Engine SDK is installed, the test environment is 
available at <http://localhost:8080>


Deploying the Application
-------------------------
To deploy the application to App Engine, use [appcfg.py update][appcfg]
<pre class="console">
	appcfg.py update src/
</pre>

The application should be visible at http://{YOURAPPID}.appspot.com


Folder structure
----------------
The App Engine app's root folder is located at `src/`.

<pre class="console">
	src/
	|-- application (application code)
	|-- flask (flask core)
	|-- flaskext (flask extensions, inc. Flask-WTF)
	|-- jinja2 (template engine)
	|-- simplejson (required by Jinja2)
	|-- werkzeug (WSGI utilities for Python-based web development)
	`-- wtforms (Jinja2-compatible web form utility)
</pre>

The application code is located at `src/application`.

<pre class="console">
	application/
	|-- __init__.py (initializes flask app)
	|-- decorators.py (decorators for URL handlers)
	|-- forms.py (web form models and validators)
	|-- models.py (App Engine datastore models)
	|-- settings.py (settings for flask app)
	|-- static
	|	|-- css
	|	|	|-- main.css (custom styles)
	|	|	`-- style.css (base CSS from HTML5 boilerplate)
	|	|-- img
	|	|	|-- favicon.ico (replace with custom favicon)
	|	|	`-- favicon.png
	|	`-- js
	|		|-- main.js (custom javascript)
	|		`-- modernizr-1.6.min.js (HTML5 enabling and detection)
	|-- templates
	|	|-- 404.html (not found page)
	|	|-- base.html (master template)
	|	|-- list_examples.html (example list-based template)
	|	`-- new_example.html (example form-based template)
	|-- tests.py (unit tests)
	|-- views.py (Handlers for URL routes defined at urls.py)
	`-- urls.py (URL dispatch routes)
</pre>


Removing Extended Attributes (@ flag)
-------------------------------------
A few of the files in the source tree were uploaded (with apologies) to 
GitHub with extended attributes (notice the '@' symbol when running ls -al).

To remove the extended attributes, use `xattr -rd` at the root of the 
src/ folder.

<pre class='console'>
	xattr -rd com.apple.quarantine .
	xattr -rd com.macromates.caret .
</pre>

Note: Windows users may safely ignore the xattr fix


Licenses
--------
See licenses/ folder


Credits
-------
Project template layout was heavily inspired by Francisco Souza's 
[gaeseries flask project][gaeseries]

HTML5-based main template (templates/base.html) and base CSS styles 
(static/css/style.css) extracted from [HTML5 Boilerplate][html5]


[flask]: http://flask.pocoo.org
[wz]: http://werkzeug.pocoo.org/
[jinja2]: http://jinja.pocoo.org/2/documentation/
[devserver]: http://code.google.com/appengine/docs/python/tools/devserver.html
[appcfg]: http://code.google.com/appengine/docs/python/tools/uploadinganapp.html
[gaeseries]: http://github.com/franciscosouza/gaeseries/tree/flask
[html5]: http://html5boilerplate.com/



