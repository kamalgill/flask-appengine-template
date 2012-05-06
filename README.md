Flask on App Engine Project Template
====================================

Boilerplate project template for running a Flask-based application on 
Google App Engine (Python)


About Flask
-----------
[Flask][flask] is a BSD-licensed microframework for Python based on 
[Werkzeug][wz], [Jinja2][jinja2] and good intentions.

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
8. Add the secret keys for CSRF protection by running the `generate_keys.py`
   script at `src/application/generate_keys.py`, which will generate the
   secret keys module at src/application/secret_keys.py

Note: Copy the .gitignore file from the tarball folder's root to your git 
repository root to keep the secret_keys module out of version control.

Or, add the following to your .(git|hg|bzr)ignore file

<pre class="console">
  # Keep secret keys out of version control
  secret_keys.py
</pre>


Front-end Customization
-----------------------
1. Customize the main HTML template at 
   `src/application/static/templates/base.html`
2. Customize CSS styles at `src/application/static/css/main.css`
3. Add custom JavaScript code at `src/application/static/js/main.js`
4. Customize favicon at `src/application/static/img/favicon.ico`
5. Customize 404 page at `src/aplication/templates/404.html`


Previewing the Application
--------------------------
To preview the application using App Engine's development server, 
use [dev_appserver.py][devserver]

<pre class="console">
  dev_appserver.py src/
</pre>

Assuming the latest App Engine SDK is installed, the test environment is 
available at <http://localhost:8080>


Running Unit Tests
------------------
To run unit tests, use
<pre class="console">
    python testrunner.py APPENGINE_SDK_PATH
</pre>

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
  |-- app.yaml (App Engine config file)
  |-- application (application code)
  |-- index.yaml (App Engine query index definitions)
  |-- main.py (Main App Engine handler)
  |-- packages (Flask and third-party zip packages)
  |   |-- blinker.zip (library for event/signal support)
  |   |-- flask.zip (Flask core)
  |   |-- flaskext (Flask extensions go here; wtforms and gae_mini_profiler are provided)
  |   |-- jinja2.zip (template engine)
  |   |-- simplejson.zip (JSON utility required by Jinja2)
  |   |-- werkzeug (WSGI utilities for Python-based web development)
  |   |-- werkzeug_debugger_appengine (enables Werkzeug's interactive debugger for App Engine)
  |   `-- wtforms.zip (Jinja2-compatible web form utility)
  `-- tests/ (unit tests)
</pre>

The application code is located at `src/application`.

<pre class="console">
  application/
  |-- __init__.py (initializes Flask app)
  |-- decorators.py (decorators for URL handlers)
  |-- forms.py (web form models and validators)
  |-- models.py (App Engine datastore models)
  |-- settings.py (settings for Flask app)
  |-- static
  | |-- css
  | | `-- main.css (custom styles)
  | |-- img
  | | |-- favicon.ico (replace with custom favicon)
  | | `-- favicon.png
  | `-- js
  |   |-- main.js (custom javascript)
  |   `-- modernizr-2.min.js (HTML5 enabling and detection)
  |-- templates
  | |-- 404.html (not found page)
  | |-- 500.html (server error page)
  | |-- base.html (master template)
  | |-- list_examples.html (example list-based template)
  | `-- new_example.html (example form-based template)
  |-- urls.py (URL dispatch routes)
  `-- views.py (Handlers for URL routes defined at urls.py)
</pre>


Profiling with AppStats
-----------------------
Thanks to contributions from [jbochi][jbochi], and the 
excellent [Flask-GAE_Mini_Profiler][profiler] extension, 
AppStats-based profiling is enabled for admin users.


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


Package Versions
----------------
- Blinker: 1.1
- Flask: 0.8
- Flask-WTF: 0.5.2
- Jinja2: 2.5.5
- simplejson: 2.2.1
- Werkzeug: 0.8.1
- WTForms: 0.6.2
- Modernizr: 2.0


Credits
-------
Project template layout was heavily inspired by Francisco Souza's 
[gaeseries Flask project][gaeseries]

HTML5-based main template (templates/base.html) 
extracted from [HTML5 Boilerplate][html5]

HTML5 detection provided by [Modernizr 2][modernizr] (configured with all features)

CSS reset, fonts, grids, and base styles provided by [YUI 3][yui3]

Project layout improvements (zip archives/zipimport) contributed by 
Stochastic Technologies.

Werkzeug's Interactive Debugger enabled for App Engine using
Naitik Shah's [werkzeug-debugger-appengine][wzda] utility.

Testing and Profiling improvements provided by [Juarez Bochi][jbochi]


[flask]: http://flask.pocoo.org
[wz]: http://werkzeug.pocoo.org/
[jinja2]: http://jinja.pocoo.org/2/documentation/
[devserver]: http://code.google.com/appengine/docs/python/tools/devserver.html
[appcfg]: http://code.google.com/appengine/docs/python/tools/uploadinganapp.html
[gaeseries]: http://github.com/franciscosouza/gaeseries/tree/flask
[html5]: http://html5boilerplate.com/
[yui3]: http://developer.yahoo.com/yui/3/
[modernizr]: http://www.modernizr.com/
[wzda]: https://github.com/nshah/werkzeug-debugger-appengine
[jbochi]: https://github.com/jbochi
[profiler]: http://packages.python.org/Flask-GAE-Mini-Profiler/

