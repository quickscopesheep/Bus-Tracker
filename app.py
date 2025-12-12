from flask import *
import json

import timetable_api

#use templates for static stuff. use API route for dynamic stuff eg. autocomplete, bus locations

app = Flask(import_name='backend')

@app.route('/search')
@app.route('/')
def search_route():
    return app.send_static_file('search.html')

@app.route('/results')
def results_route():
    return app.send_static_file('results.html')

@app.route('/timetable')
def timetable_route():
    return app.send_static_file('timetable.html')

@app.route('/timetable_api')
def api_route():
    search_body = request.args.get('body', '')
    response_struct = timetable_api.build_search_result(search_body)

    return json.dumps(response_struct)