"""
urls.py

URL dispatch route mappings and error handlers

"""

from flask import render_template

from application import app
from application import views


## URL dispatch rules
# Home page
app.add_url_rule('/', view_func=views.home)
# Say hello
app.add_url_rule('/hello/<username>', view_func=views.say_hello)
# Examples list page
app.add_url_rule('/examples', view_func=views.list_examples)
# Add new example via web form
app.add_url_rule('/example/new', view_func=views.new_example, methods=['GET', 'POST'])


## Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

