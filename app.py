from flask import *

app = Flask(__name__)

@app.route("/search")
def search_page():
    return app.send_static_file('search.html')

@app.route("/results")
def results_page():
    return app.send_static_file('results.html')