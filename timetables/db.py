import sqlite3

from dotenv import load_dotenv
import os
import json

import dbhelpers

from .gtfs import GTFSFeed
from .naptan import NaptanImporter

from pathlib import Path

load_dotenv()

class TimetableDatabase:
    def __init__(self, path : Path):
        self.path = path
        self._init_db()

    #creates tables if they do not already exist
    def _init_db(self):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS Stops (
                id TEXT PRIMARY KEY,
                atco TEXT,
                name TEXT,
                name_short TEXT,
                indicator TEXT,
                bearing TEXT,
                lon TEXT,
                lat TEXT,
                street TEXT,
                landmark TEXT,
                town TEXT,
                nptg_locality TEXT,
                locality_name TEXT
            );
            CREATE TABLE IF NOT EXISTS Agencies (
                id TEXT PRIMARY KEY,
                name TEXT,
                url TEXT
            );
            CREATE TABLE IF NOT EXISTS Routes (
                id TEXT PRIMARY KEY,
                agency TEXT,
                name TEXT,
                name_long TEXT,
                desc TEXT,
                origin TEXT,
                dst TEXT  
            );
            CREATE TABLE IF NOT EXISTS Trips (
                id TEXT PRIMARY KEY,
                route TEXT,
                direction TEXT,
                service TEXT
            );
            CREATE TABLE IF NOT EXISTS Services (
                id TEXT PRIMARY KEY,
                monday TEXT,
                tuesday TEXT,
                wednesday TEXT,
                thursday TEXT,
                friday TEXT,
                saturday TEXT,
                sunday TEXT,
                start_date TEXT,
                end_date TEXT
            );
            CREATE TABLE IF NOT EXISTS ServiceDates (
                id TEXT PRIMARY KEY,
                date TEXT,
                exception_type TEXT
            );
            CREATE TABLE IF NOT EXISTS Times (
                trip TEXT,
                stop TEXT,
                arrival_time TEXT,
                departure_time TEXT,
                sequence INTEGER,
                timepoint TEXT,
                PRIMARY KEY (trip, stop)
            );
        """)

    #clears tables and imports the datasets with the paths specified
    def import_local(self, gtfs_path : Path, naptan_path : Path):
        feed = GTFSFeed(gtfs_path)

        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        #clear all tables and clear indices
        print('clearing db')
        cur.execute('DROP INDEX IF EXISTS TripsRoute')
        cur.execute('DROP INDEX IF EXISTS TimesTrip')
        cur.execute('DROP INDEX IF EXISTS TimesStop')

        cur.execute('DELETE FROM Stops')
        cur.execute('DELETE FROM Agencies')
        cur.execute('DELETE FROM Trips')
        cur.execute('DELETE FROM Routes')
        cur.execute('DELETE FROM Services')
        cur.execute('DELETE FROM ServiceDates')
        cur.execute('DELETE FROM Times')

        #parse stops from naptan dataset
        naptan = NaptanImporter(naptan_path, feed.parse_stops())

        #parse data and add to database
        print('parsing data')
        dbhelpers.parse_and_import(cur, naptan.parse_stops,
            """INSERT OR IGNORE INTO Stops (id, atco, name, name_short, indicator, bearing, lon, lat, street, landmark, town, nptg_locality, locality_name)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        )
        dbhelpers.parse_and_import(cur, feed.parse_agencies,
            'INSERT OR IGNORE INTO Agencies (id, name, url) VALUES(?, ?, ?)'
        )
        self._parse_and_import(cur, feed.parse_trips,
            'INSERT OR IGNORE INTO Trips (id, route, direction, service) VALUES(?, ?, ?, ?)'
        )
        self._parse_and_import(cur, feed.parse_routes,
            'INSERT OR IGNORE INTO Routes (id, agency, name, name_long, desc, origin, dst) VALUES(?, ?, ?, ?, ?, ?, ?)'
        )
        self._parse_and_import(cur, feed.parse_service,"""
            INSERT OR IGNORE INTO Services (id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        dbhelpers.parse_and_import(cur, feed.parse_service_dates,
            'INSERT OR IGNORE INTO ServiceDates (id, date, exception_type) VALUES(?, ?, ?)'                       
        )
        dbhelpers.parse_and_import(cur, feed.parse_times,""" 
            INSERT OR IGNORE INTO Times (trip, stop, arrival_time, departure_time,
                sequence, timepoint) VALUES(?, ?, ?, ?, ?, ?)
        """)
        
        #create indices for quick queries
        print('creating indices')
        cur.execute('CREATE INDEX TripsRoute ON Trips(route)')
        cur.execute('CREATE INDEX TimesTrip ON Times(trip)')
        cur.execute('CREATE INDEX TimesStop ON Times(stop)')

        #ensure all changes are saved to disk
        conn.commit()

    #returns number of search results for a given search query
    def get_search_num_results(self, search_body : str) -> tuple[int, bool]:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        pattern = f'%{search_body}%'
        total = 0

        cur.execute("""
            SELECT DISTINCT COUNT(*)
	            FROM Routes r
	            WHERE r.name LIKE :pattern;
        """, {
            "pattern": pattern
        })

        total += int(cur.fetchone()[0])

        cur.execute("""
            SELECT DISTINCT COUNT(*)
	            FROM Stops s
	            WHERE s.name LIKE :pattern;
        """, {
            "pattern": pattern
        })

        total += int(cur.fetchone()[0])
        
        return total, True

    #gets results for a search query
    #dict keys:
    #   type = route/stop
    #   id = id of entity
    #   name = name
    #   origin = (for route) starting location
    #   dst = (for route) end location
    #   agency_name = (for route) operating agency
    #   agency_url = (for route) operating agency url
    #   stop_code = (for stop) atco/naptan code
    #   bearing = (for stop) direction stop faces
    #   locality = (for stop) locality of stop

    def get_search_result(self, search_body : str, page_offset : int, page_size : int) -> tuple[list[dict], bool]:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        pattern = f'%{search_body}%'

        cur.execute("""
            SELECT DISTINCT 'route' as type, r.id as id, r.name as name, r.origin as origin, r.dst as dst, a.name as agency_name, a.url as agency_url, '' as stop_code, '' as bearing, '' as locality
	            FROM Routes r
	            JOIN Agencies a ON r.agency = a.id
	            WHERE r.name LIKE :search_query
                OR r.origin LIKE :search_query
                OR r.dst LIKE :search_query
            UNION
            SELECT DISTINCT 'stop' as type, s.id as id, s.name as name, '' as origin, '' as dst, '' as agency_name, '' as agency_url, s.atco as stop_code, s.bearing as bearing, s.locality_name as locality
	            FROM Stops s
	            WHERE s.name LIKE :search_query
            LIMIT :size OFFSET :offset;
        """, {
            'search_query': pattern,
            'offset': page_offset,
            'size': page_size
        })

        results = cur.fetchall()
        #can return zero here as may be empty search
        if results == None: return [], True

        schema = ('type', 'id', 'name', 'origin', 'dst', 'agency_name', 'agency_url', 'stop_code', 'bearing', 'locality')

        return [dbhelpers.result_to_dict(result, schema) for result in results], True

    #gets info about a stop
    #dict keys:
    #   name = name
    #   name2 = short name
    #   stop_lat = latitude
    #   stop_lon = longitude
    #   stop_code = ATCO or naptan code
    #   stop_indicator = misclaneous info about stop
    #   stop_bearing = direction the stop faces eg NW, SE
    #   stop_landmark = landmark stop is near
    #   stop_town = town
    #   stop_locality = name of locality

    def get_stop_data(self, stop_id : str) -> dict:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.execute('SELECT name, name_short, lat, lon, atco, indicator, bearing, landmark, town, locality_name FROM Stops WHERE id=:stop_id', {'stop_id':stop_id})

        result = cur.fetchone()
        if result == None: return {}, False

        schema = ('name', 'name2', 'stop_lat', 'stop_lon', 'stop_code',
                    'stop_indicator', 'stop_bearing', 'stop_landmark', 'stop_town', 'stop_locality')

        return dbhelpers.result_to_dict(result, schema), True
    
    #gets info about a route
    #dict keys:
    #   name = name
    #   name2 = short name
    #   agency_name = operator name
    #   agency_url = url for agency

    def get_route_data(self, route_id : str) -> dict:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.execute("""
            SELECT r.name as route_name, r.desc as route_desc, a.name as agency_name, a.url as agency_url
                FROM Routes r
                JOIN Agencies a ON r.agency = a.id 
                WHERE r.id = :route_id
        """, {'route_id': route_id})

        result = cur.fetchone()
        if result == None: return {}, False

        schema = ('name', 'name2', 'agency_name', 'agency_url')

        return dbhelpers.result_to_dict(result, schema), True

    #get stop times
    #dict keys:
    #   trip = trip id
    #   arrival_time = arrival time
    #   departure_time = departure time
    #   sequence = sequence
    #   timing_status = (0/1) timing point or not
    #   direction = (0/1) outbound/inbound
    #   entity_id = route id
    #   entity_name = route name
    #   service_days = operating days
    #   service_start = start of service
    #   service_end = end of service

    def get_stop_times(self, stop_id : str) -> tuple[list[dict], bool]:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.execute(f"""
            SELECT trip, arrival_time, departure_time, sequence, timepoint,
                Trips.direction,
                Routes.id, Routes.name,
                Services.monday || Services.tuesday || Services.wednesday || Services.thursday || Services.friday || Services.saturday || Services.sunday,
                Services.start_date, Services.end_date
            FROM Times
            JOIN Trips ON Times.trip = Trips.id
            JOIN Routes ON Trips.route = Routes.id
            JOIN Services ON Trips.service = Services.id
            WHERE Times.stop = :stop_id
        """, {'stop_id': stop_id})    

        results = cur.fetchall()
        if results == None: return {}, False
        
        schema = ('trip', 'arrival_time', 'departure_time', 'sequence', 'timing_status',
                                'direction', 'entity_id', 'entity_name', 'service_days', 'service_start',
                                'service_end')

        return [dbhelpers.result_to_dict(result, schema) for result in results], True

    #get route times
    #dict keys:
    #   trip = trip id
    #   arrival_time = arrival time
    #   departure_time = departure time
    #   sequence = sequence
    #   timing_status = (0/1) timing point or not
    #   direction = (0/1) outbound/inbound
    #   entity_id = stop id
    #   entity_name = stop name
    #   service_days = operating days
    #   service_start = start of service
    #   service_end = end of service

    def get_route_times(self, route_id : str) -> tuple[list[dict], bool]:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.execute(f"""
            SELECT trip, arrival_time, departure_time, sequence, timepoint,
                Trips.direction,
                Stops.id, Stops.name_short,
                Services.monday || Services.tuesday || Services.wednesday || Services.thursday || Services.friday || Services.saturday || Services.sunday,
                Services.start_date, Services.end_date
            FROM Times
            JOIN Trips ON Times.trip = Trips.id
            JOIN Stops ON Times.stop = Stops.id
            JOIN Services ON Trips.service = Services.id
            WHERE Trips.route = :route_id
        """, {'route_id': route_id})

        results = cur.fetchall()
        if results == None: return {}, False

        schema = ('trip', 'arrival_time', 'departure_time', 'sequence', 'timing_status',
                                'direction', 'entity_id', 'entity_name', 'service_days', 'service_start',
                                'service_end')

        return [dbhelpers.result_to_dict(res, schema) for res in results], True

    #get all stops a route goes to
    #dict keys:
    #   id = id of stop
    #   name = name of stop
    #   lon = longitude of stop
    #   lat = latitude of stop
    #   direction = direction of the stop (inbound/outbound)

    def get_stops_on_route(self, route_id : str) -> tuple[list[dict], bool]:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT Stops.id, Stops.name_short, Stops.lon, Stops.lat, Trips.direction
                FROM Stops
                JOIN Times ON Times.stop = Stops.id
                JOIN Trips ON Times.trip = Trips.id
                JOIN Routes ON Trips.route = Routes.id
                WHERE Routes.id = :route;
        """, {
            'route': route_id
        })

        results = cur.fetchall()
        if results == None: return {}, False

        schema = ('id', 'name', 'lon', 'lat', 'direction')

        return [dbhelpers.result_to_dict(res, schema) for res in results], True

instance = TimetableDatabase('db/timetables.db')