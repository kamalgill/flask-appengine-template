
from flask import Flask
import settings

app = Flask(__name__)
app.config.from_object('application.settings')

import views
