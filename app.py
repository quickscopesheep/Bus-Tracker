from flask import *
import json
import sys

import timetable_api

#use templates for static stuff. use API route for dynamic stuff eg. autocomplete, bus locations

app = Flask(__name__)

@app.route('/search')
@app.route('/')
def search_route():
    return render_template('search.html')

@app.route('/results')
def results_route():
    res = timetable_api.build_search_result(request.args.get('q', ''))
    return render_template('results.html', matches = res)

@app.route('/timetable')
def timetable_route():
    return render_template('timetable.html')

@app.route('/api')
def api_route():
    search_body = request.args.get('body', '')
    response_struct = timetable_api.build_search_result(search_body)

    return json.dumps(response_struct)