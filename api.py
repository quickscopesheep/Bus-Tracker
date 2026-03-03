import flask

import json

import timetables.db as tdb
import busmap.db as mdb

from datetime import datetime

#declare blueprint containing all API routes. This will add prefix /api to any routes it contains
api_bp = flask.Blueprint('api', __name__, url_prefix = '/api')

#api routes used internally to retrieve database data
#all routes return a json object containg fields ok and the response of the query
#where ok = true/false

#returns number of results found for a search query
#request args:
#   q : string, search query
#response:
#   num_results: int, number of results
@api_bp.route('/search-num-results')
def api_search_num_results():
    result, ok = tdb.instance.get_search_num_results(
        flask.request.args.get('q')
    )

    return json.dumps({
        'ok': ok,
        'num_results': result
    })

#returns search results found for a search query
#request args:
#   q : string, search query
#   offset : int, what index responses should startfrom
#   size : int, how many results should be returned, max = MAX_PAGE_SIZE
#response:
#   data : array, json array of results
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
            'data': {}
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

#returns info about a route
#request args:
#   id : string, route id
#response:
#   data : dict, dictionary of different attributes
@api_bp.route('/route/info')
def api_route_info_route():
    result, ok = tdb.instance.get_route_data(flask.request.args.get('id'))

    return json.dumps({
        'ok': ok,
        'data': result
    })

#returns info about a stop
#request args:
#   id : string, stop id
#response:
#   data : dict, dictionary of different attributes
@api_bp.route('/stop/info')
def api_stop_info_route():
    result, ok = tdb.instance.get_stop_data(flask.request.args.get('id'))
    
    return json.dumps({
        'ok': ok,
        'data': result
    })

#returns route timetable
#request args:
#   id : string, route id
#response:
#   data : array, array of times
@api_bp.route('/route/timetable')
def api_route_timetable_route():
    result, ok = tdb.instance.get_route_times(flask.request.args.get('id'))

    return json.dumps({
        'ok': ok,
        'data': result
    })


#returns stop timetable
#request args:
#   id : string, stop id
#response:
#   data : array, array of times
@api_bp.route('/stop/timetable')
def api_stop_timetable_route():
    result, ok = tdb.instance.get_stop_times(flask.request.args.get('id'))

    return json.dumps({
        'ok': ok,
        'data': result
    })

#returns all stops a route visits
#request args:
#   id : string, route id
#response:
#   data : array, array of stops
@api_bp.route('/map/stops')
def api_get_stops_on_route():
    result, ok = tdb.instance.get_stops_on_route(flask.request.args.get('id'))

    return json.dumps({
        'ok': ok,
        'data': result
    })

#returns live bus positions
#request args:
#   id : string, route id
#response:
#   data : array, array of vehicle positions
@api_bp.route('/map/livedata')
def api_map_livedata():
    result, ok = mdb.instance.get_vehicle_positions(flask.request.args.get('id'))

    return json.dumps({
        'ok': ok,
        'result': result
    })