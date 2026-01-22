import sqlite3

from dotenv import load_dotenv
import os
import json

from .gtfs import GTFSFeed

load_dotenv()
db_loc = os.environ['DB_PATH']

IMPORT_CHUNK_SIZE = 1000

class TimetableDatabase:
    def __init__(self, path):
        self.path = path

        self.times_schema = ('entity_id', 'name', 'arrival_time', 'departure_time', 'sequence', 'direction',
                              'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')

        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS Stops (
                id TEXT PRIMARY KEY,
                code TEXT,
                name TEXT,
                lat TEXT,
                long TEXT
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
                desc TEXT
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
                route TEXT,
                service TEXT,
                stop TEXT,
                arrival_time TEXT,
                departure_time TEXT,
                sequence INTEGER,
                direction INTEGER,
                timepoint TEXT
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

    def import_local(self, path):
        feed = GTFSFeed(path)

        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        self._parse_and_import(cur, feed.parse_stops,
            'INSERT OR IGNORE INTO Stops (id, code, name, lat, long) VALUES(?, ?, ?, ?, ?)'
        )
        self._parse_and_import(cur, feed.parse_agencies,
            'INSERT OR IGNORE INTO Agencies (id, name, url) VALUES(?, ?, ?)'
        )
        self._parse_and_import(cur, feed.parse_routes,
            'INSERT OR IGNORE INTO Routes (id, agency, name, name_long, desc) VALUES(?, ?, ?, ?, ?)'
        )
        self._parse_and_import(cur, feed.parse_service,"""
            INSERT OR IGNORE INTO Services (id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        self._parse_and_import(cur, feed.parse_service_dates,
            'INSERT OR IGNORE INTO ServiceDates (id, date, exception_type) VALUES(?, ?, ?)'                       
        )
        self._parse_and_import(cur, feed.parse_times,""" 
            INSERT OR IGNORE INTO Times (route, service, stop, arrival_time, departure_time,
                sequence, direction, timepoint) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """)
        
        conn.commit()

    def download_and_import(self):
        #TODO
        pass
    
    def _result_to_dict(self, result, schema):
        return {
            schema[i]: result[i] for i in range(len(schema))
        }

    def get_search_result(self, search_body):
        #def should escape body for special chars to avoid SQL injection
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        pattern = f'%{search_body}%'

        cur.execute("""
            SELECT DISTINCT 'route' as type, r.id as id, r.name as name, a.name as agency_name, a.url as agency_url, '' as stop_code
	            FROM Routes r
	            JOIN Agencies a ON r.agency = a.id
	            WHERE r.name LIKE ?
            UNION
            SELECT DISTINCT 'stop' as type, s.id as id, s.name as name, '' as agency_name, '' as agency_url, s.code as stop_code
	            FROM Stops s
	            WHERE s.name LIKE ?;
        """, (pattern, pattern))

        results = [
            self._result_to_dict(result, ['type', 'id', 'name', 'agency_name', 'agency_url', 'stop_code'])for result in cur.fetchall()
        ]

        return results

    # (code, name, lat, long)
    def get_stop_data(self, stop_id):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.execute('SELECT name, lat, long, code from Stops where id=:stop_id', {'stop_id':stop_id})
        return self._result_to_dict(cur.fetchone(), ('stop_name', 'stop_lat', 'stop_lon', 'stop_code'))
    
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

        return self._result_to_dict(cur.fetchone(), ('route_name', 'route_desc', 'agency_name', 'agency_url'))


    def get_stop_times(self, stop_id):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.execute(f"""
            
            SELECT t.stop AS entity_id, r.name as name, t.arrival_time AS arrival_time, t.departure_time AS departure_time,
                    t.sequence AS sequence, t.direction AS direction,
                    s.monday as monday, s.tuesday as tuesday, s.wednesday as wednesday,
                    s.thursday as thursday, s.friday as friday, s.saturday as saturday,
                    s.sunday as sunday

                FROM Times t
                JOIN Services s ON t.service = s.id
                JOIN Routes st ON t.stop = r.id
                WHERE t.route = :route_id
        """, {'stop_id': stop_id})

        return [self._result_to_dict(res, self.times_schema) for res in cur.fetchall()]

    def get_route_times(self, route_id):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.execute(f"""
            SELECT t.stop AS entity_id, st.name as name, t.arrival_time AS arrival_time, t.departure_time AS departure_time,
                    t.sequence AS sequence, t.direction AS direction,
                    s.monday as monday, s.tuesday as tuesday, s.wednesday as wednesday,
                    s.thursday as thursday, s.friday as friday, s.saturday as saturday,
                    s.sunday as sunday

                FROM Times t
                JOIN Services s ON t.service = s.id
                JOIN Stops st ON t.stop = st.id
                WHERE t.route = :route_id
        """, {'route_id': route_id})

        return [self._result_to_dict(res, self.times_schema) for res in cur.fetchall()]



instance = TimetableDatabase(db_loc + 'timetables.db')