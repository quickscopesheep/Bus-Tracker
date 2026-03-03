import flask

from flask_apscheduler import APScheduler

from api import api_bp

from busmap import db as mdb

app = flask.Flask(__name__)

#add API blueprint
app.register_blueprint(api_bp)

scheduler = APScheduler()
scheduler.init_app(app)

#add job to periodicaly fetch GTFS RT feed
scheduler.add_job(id='update_vehicle_poisitions', func=mdb.instance.fetch_feed, trigger='interval', seconds = 10)

scheduler.start()

#home page route
@app.route('/search')
@app.route('/')
def search_route():
    return flask.render_template('search.html')

#results route
@app.route('/results')
def results_route():
    return flask.render_template('results.html')

#timetable route
@app.route('/timetable')
def timetable_template():
    return flask.render_template('timetable.html')

#map route
@app.route('/map')
def map_template():
    return flask.render_template('map.html')

#error route
@app.route('/error')
def error_template():
    return flask.render_template('errorpage.html')