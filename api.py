import flask

import json

import timetables.db as tdb
import busmap.db as mdb

from datetime import datetime

api_bp = flask.Blueprint('api', __name__, url_prefix = '/api')

@api_bp.route('/search')
def api_search_route():
    return json.dumps(tdb.instance.get_search_result(flask.request.args.get('q')))

@api_bp.route('/route/info')
def api_route_info_route():
    return json.dumps(tdb.instance.get_route_data(flask.request.args.get('id')))

@api_bp.route('/stop/info')
def api_stop_info_route():
    return json.dumps(tdb.instance.get_stop_data(flask.request.args.get('id')))

@api_bp.route('/route/timetable')
def api_route_timetable_route():
    return json.dumps(
        tdb.instance.get_route_times(flask.request.args.get('id'))
    )

@api_bp.route('/stop/timetable')
def api_stop_timetable_route():
    return json.dumps(
        tdb.instance.get_stop_times(flask.request.args.get('id'))
    )

@api_bp.route('/map/livedata')
def api_map_live_route():
    return json.dumps(
        mdb.instance.get_vehicle_positions(flask.request.args.get('id'))
    )