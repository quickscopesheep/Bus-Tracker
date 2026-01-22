import flask

import json
import timetables.db as tdb

api_bp = flask.Blueprint('api', __name__, url_prefix = '/api')

@api_bp.route('/search')
def api_search_route():
    return json.dumps(tdb.instance.get_search_result(flask.request.args.get('q')))

def build_timetable(timing_points):
    entities = {}
    for t in timing_points:
        if t['entity_id'] not in entities:
            entities[t['entity_id']] = {
                'name': t['name'],
                'id': t['entity_id'],
                'sequence': t['sequence'],
                'times': []
            }
        
        entities[t['entity_id']]['times'].append({
            'time': t['arrival_time'],
            'direction': t['direction'],
            'monday': t['monday'],
            'tuesday': t['tuesday'],
            'wednesday': t['wednesday'],
            'thursday': t['thursday'],
            'friday': t['friday'],
            'saturday': t['saturday'],
            'sunday': t['sunday'],
        })

    return list(entities.values())

#TODO use json for arguments rather than url
@api_bp.route('/route')
def api_route_route():
    route_id = flask.request.args.get('id')

    response = {
        'info': tdb.instance.get_route_data(route_id),
        'timing_points': build_timetable(tdb.instance.get_route_times(route_id))
    }

    return json.dumps(response)

@api_bp.route('/stop')
def api_stop_route():
    stop_id = flask.request.args.get('id')

    response = {
        'info': tdb.instance.get_stop_data(stop_id),
        'timing_points': build_timetable(tdb.instance.get_stop_times(stop_id))
    }

    return json.dumps(response)