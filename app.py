import flask

from api import api_bp

#use templates for static stuff. use API route for dynamic stuff eg. autocomplete, bus locations

app = flask.Flask(__name__)
app.register_blueprint(api_bp)

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