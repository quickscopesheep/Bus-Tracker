import flask

from flask_apscheduler import APScheduler

from api import api_bp

from busmap import db as mdb

app = flask.Flask(__name__)
app.register_blueprint(api_bp)

scheduler = APScheduler()
scheduler.init_app(app)

scheduler.add_job(id='update_vehicle_poisitions', func=mdb.instance.fetch_feed, trigger='interval', seconds = 10)

scheduler.start()

@app.route('/search')
@app.route('/')
def search_route():
    return flask.render_template('search.html')

@app.route('/results')
def results_route():
    return flask.render_template('results.html')

@app.route('/timetable')
def timetable_template():
    return flask.render_template('timetable.html')

@app.route('/map')
def map_template():
    return flask.render_template('map.html')

@app.route('/error')
def error_template():
    return flask.render_template('errorpage.html')