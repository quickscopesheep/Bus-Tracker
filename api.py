import flask

import json

import timetables.db as tdb
import busmap.db as mdb

from datetime import datetime

api_bp = flask.Blueprint('api', __name__, url_prefix = '/api')

@api_bp.route('/search-num-results')
def api_search_num_results():
    result, ok = tdb.instance.get_search_num_results(
        flask.request.args.get('q')
    )

    return json.dumps({
        'ok': ok,
        'page_size': result
    })

@api_bp.route('/search')
def api_search_route():
    MAX_PAGE_SIZE = 20

    offset = None
    size = None

    try:
        offset = int(flask.request.args.get('offset'))
        size = min(int(flask.request.args.get('size')), MAX_PAGE_SIZE)
    except:
        return json.dumps({
            'ok': False,
            'page_size': {}
        })

    result, ok = tdb.instance.get_search_result(
        flask.request.args.get('q'),
        offset,
        size
    )

    return json.dumps({
        'ok': ok,
        'data': result
    })

@api_bp.route('/route/info')
def api_route_info_route():
    result, ok = tdb.instance.get_route_data(flask.request.args.get('id'))

    return json.dumps({
        'ok': ok,
        'data': result
    })

@api_bp.route('/stop/info')
def api_stop_info_route():
    result, ok = tdb.instance.get_stop_data(flask.request.args.get('id'))
    
    return json.dumps({
        'ok': ok,
        'data': result
    })

@api_bp.route('/route/timetable')
def api_route_timetable_route():
    result, ok = tdb.instance.get_route_times(flask.request.args.get('id'))

    return json.dumps({
        'ok': ok,
        'data': result
    })

@api_bp.route('/stop/timetable')
def api_stop_timetable_route():
    result, ok = tdb.instance.get_stop_times(flask.request.args.get('id'))

    return json.dumps({
        'ok': ok,
        'data': result
    })