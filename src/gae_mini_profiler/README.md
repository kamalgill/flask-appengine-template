# Google App Engine Mini Profiler

gae_mini_profiler is a quick drop-in WSGI app that provides ubiquitous profiling of your existing GAE projects. It exposes RPC statistics and CPU profiling output for users of your choosing on your production site. Only requests coming from users of your choosing will be profiled, and others will not suffer any performance degradation, so you can use this profiler to learn about production performance without stressing about slowing users down. See screenshots and features below.

This project is heavily inspired by the Stack Exchange team's impressive [mini-profiler](http://miniprofiler.com/).

* <a href="#demo">See it in action</a>
* <a href="#screens">Screenshots</a>
* <a href="#start">Getting Started</a>
* <a href="#features">Features</a>
* <a href="#dependencies">Dependencies</a>
* <a href="#bonus">Bonus</a>
* <a href="#faq">FAQ</a>

## <a name="demo">See it in action</a>

Play around with a demo App Engine applications with gae_mini_profiler enabled at [http://mini-profiler.appspot.com](http://mini-profiler.appspot.com/).

## <a name="screens">Screenshots</a>

<strong>All profiled pages have total milliseconds in corner, which can be expanded...</strong><br/>
<img src="http://i.imgur.com/Nqdtu.png"/><br/><br>
<strong>...to show more details...</strong><br/>
<img src="http://i.imgur.com/sjxE7.png"/><br/><br/>
<strong>...about remote procedure call performance...</strong><br/>
<img src="http://i.imgur.com/C29gC.png"/><br/><br>
<strong>...or CPU profiler output.</strong><br/>
<img src="http://i.imgur.com/XcBxG.png"/><br/><br/>
<strong>Choose between an instrumented CPU profiler (above) or a sampling
profiler (below).</strong><br/>
<img src="http://i.imgur.com/KiwHv.png"><br><br>
<strong>Ajax requests and redirects are also profiled and added to the corner of your page.</strong><br/>
<img src="http://i.imgur.com/8gS4D.png"/><br/><br>
<strong>Any Python logging module output is also available for easy access.</strong>
<img src="http://i.imgur.com/6382r.png"/><br/>

## <a name="start">Getting Started</a>

1. Download this repository's source and copy the `gae_mini_profiler/` folder into your App Engine project's root directory.

2. Add the following two handler definitions to `app.yaml`:

        handlers:
        - url: /gae_mini_profiler/static
          static_dir: gae_mini_profiler/static
        - url: /gae_mini_profiler/.*
          script: gae_mini_profiler.main.application

3. Modify the WSGI application you want to profile by wrapping it with the gae_mini_profiler WSGI application.

        import gae_mini_profiler.profiler
        ...
        application = webapp.WSGIApplication([...])
        application = gae_mini_profiler.profiler.ProfilerWSGIMiddleware(application)

4. Modify your template to include our javascript and stylesheets just before your ending body tag.

    There is a profiler_includes() function in gae_mini_profiler.templatetags that spits out the right code for these scripts and stylesheets.
        
    Using any template engine of your choice, call this function at the end of your template:
    
                ...
                {% profiler_includes %}
            </body>
        </html>

    Note that these resources will not be loaded on requests when the profiler is disabled, so you don't need to worry about extra HTTP requests slowing down your users.

    Using Django?
        You can register a simple_tag to expose this to your templates:
        
        register = template.create_template_register()
        @register.simple_tag
        def profiler_includes():
            return gae_mini_profiler.templatetags.profiler_includes()
                    
    Using jinja2?
        You can expose this function to your templates easily:
        
        webapp2_extras.jinja2.default_config = {
            "globals": {
                "profiler_includes": gae_mini_profiler.templatetags.profiler_includes
            }
        }
                
    Using anything else to generate your HTML?
        Just find some way to spit the results of profiler_includes() into your HTML. Doesn't have to be anything fancy.

5. You're all set! Now you just need to choose when you want to enable the profiler by overriding a simple function. By default it's enabled on the dev server and disabled in production. To enable it for App Engine admins in production, add the following to appengine_config.py:

        def gae_mini_profiler_should_profile_production():
                from google.appengine.api import users
                return users.is_current_user_admin()
                
    In appengine_config.py you can override both of the following...
    
        def gae_mini_profiler_should_profile_production(): pass
        def gae_mini_profiler_should_profile_development(): pass
        
    ...with any logic you want to choose when the profiler should be enabled.


## <a name="features">Features</a>

* Production profiling without impacting normal users
* Easily profile all requests, including ajax calls
* Summaries of RPC call types and their performance so you can quickly figure out whether datastore, memcache, or urlfetch is your bottleneck
* Redirect chains are tracked -- quickly examine the profile of not just the currently rendered request, but any preceding request that issued a 302 redirect leading to the current page.
* Share individual profile results with others by sending link
* Duplicate RPC calls are flagged for easy spotting in case you're repeating memcache or datastore queries
* Choose from either an instrumented or sampling CPU profiler to quickly figure out where your requests are spending time

## <a name="dependencies">Dependencies</a>

* jQuery must be included somewhere on your page.
* (Optional) If you want the fancy slider selector for the Logs output, jQuery UI must also be included with its Slider plugin.

## <a name="bonus">Bonus</a>

gae_mini_profiler is currently in production use at [Khan Academy](http://khanacademy.org). If you make good use of it elsewhere, please lemme know.

## <a name="faq">FAQ</a>

1. What's the license? [MIT licensed](http://en.wikipedia.org/wiki/MIT_License).
2. I had my appstats_RECORD_FRACTION variable set to 0.1, which means only 10% of my queries were getting profiles generated.  This meant that most of the time gae_mini_profiler was failing with a javascript error, because the appstats variable was null.

    If you are using appengine_config.py to customize Appstats behavior you should add this to the top of your "appstats_should_record" method.
<pre>def appstats_should_record(env):
        from gae_mini_profiler.config import should_profile
        if should_profile(env):
            return True
</pre>
