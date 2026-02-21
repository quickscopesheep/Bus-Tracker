import sqlite3

from dotenv import load_dotenv
import os
import json

import dbhelpers

from .gtfs import GTFSFeed
from .naptan import NaptanImporter

from pathlib import Path

load_dotenv()

IMPORT_CHUNK_SIZE = 1000

class TimetableDatabase:
    def __init__(self, path):
        self.path = path
        self._init_db()

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

    def _parse_and_import(self, cur, parse_func, sql):
        chunk = []

        for stop in parse_func():
            chunk.append(stop)

            if len(chunk) == IMPORT_CHUNK_SIZE:
                cur.executemany(sql, chunk)
                chunk.clear()
            
        if len(chunk) > 0:
            cur.executemany(sql, chunk)

    def import_local(self, gtfs_path, naptan_path):
        feed = GTFSFeed(gtfs_path)

        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        #clear all tables

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

        naptan = NaptanImporter(naptan_path, feed.parse_stops())

        print('parsing data')
        dbhelpers.parse_and_import(cur, naptan.parse_stops,
            """INSERT OR IGNORE INTO Stops (id, atco, name, name_short, indicator, bearing, lat, lon, street, landmark, town, nptg_locality, locality_name)
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
        
        print('creating indices')
        cur.execute('CREATE INDEX TripsRoute ON Trips(route)')
        cur.execute('CREATE INDEX TimesTrip ON Times(trip)')
        cur.execute('CREATE INDEX TimesStop ON Times(stop)')

        conn.commit()

    def get_search_num_results(self, search_body):
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

    def get_search_result(self, search_body, page_offset, page_size):
        #def should escape body for special chars to avoid SQL injection
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        pattern = f'%{search_body}%'

        cur.execute("""
            SELECT DISTINCT 'route' as type, r.id as id, r.name as name, r.origin as origin, r.dst as dst, a.name as agency_name, a.url as agency_url, '' as stop_code
	            FROM Routes r
	            JOIN Agencies a ON r.agency = a.id
	            WHERE r.name LIKE ?
            UNION
            SELECT DISTINCT 'stop' as type, s.id as id, s.name as name, '' as origin, '' as dst, '' as agency_name, '' as agency_url, s.atco as stop_code
	            FROM Stops s
	            WHERE s.name LIKE ?
            LIMIT ? OFFSET ?;
        """, (pattern, pattern, page_size, page_offset))

        results = cur.fetchall()
        #can return zero here as may be empty search
        if results == None: return [], True

        schema = ('type', 'id', 'name', 'origin', 'dst', 'agency_name', 'agency_url', 'stop_code')

        return [dbhelpers.result_to_dict(result, schema) for result in results], True

    # (code, name, lat, long)
    def get_stop_data(self, stop_id):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.execute('SELECT name, name_short, lat, lon, atco, indicator, bearing, landmark, town, locality_name FROM Stops WHERE id=:stop_id', {'stop_id':stop_id})

        result = cur.fetchone()
        if result == None: return {}, False

        schema = ('name', 'name2', 'stop_lat', 'stop_lon', 'stop_code',
                    'stop_indicator', 'stop_bearing', 'stop_landmark', 'stop_town', 'stop_locality')

        return dbhelpers.result_to_dict(result, schema), True
    
    # (name, desc, agency_name, agency_url)
    def get_route_data(self, route_id):
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

    def get_stop_times(self, stop_id):
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

    def get_route_times(self, route_id):
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

instance = TimetableDatabase('db/timetables.db')