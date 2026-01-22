import flask

import json
import timetables.db as tdb

api_bp = flask.Blueprint('api', __name__, url_prefix = '/api')

@api_bp.route('/search')
def api_search_route():
    return json.dumps(tdb.instance.get_search_result(flask.request.args.get('q')))

#TODO use json for arguments rather than url
@api_bp.route('/route')
def api_route_route():
    route_id = flask.request.args.get('id')
    service_day = flask.request.args.get('service-day')
    timing_status = flask.request.args.get('timing-status')

    timing_points = tdb.instance.get_route_times(route_id, service_day, timing_status)

    response = {
        'info': tdb.instance.get_route_data(route_id),
        'timing_points': timing_points
    }

    return json.dumps(response)

@api_bp.route('/stop')
def api_stop_route():
    stop_id = flask.request.args.get('id')
    service_day = flask.request.args.get('service_day')
    timing_status = flask.request.args.get('timing_status')

    response = {
        'info': tdb.instance.get_stop_data(stop_id),
        'timing_points': tdb.instance.get_stop_times(stop_id, service_day, timing_status)
    }

    return json.dumps(response)