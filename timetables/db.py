import sqlite3

from dotenv import load_dotenv
import os

from gtfs import GTFSFeed

load_dotenv()
db_loc = os.environ['DB_PATH']

IMPORT_CHUNK_SIZE = 1000

class TimetableDatabase:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.init_db()

    def init_db(self):
        cur = self.conn.cursor()
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
                operational_days TEXT,
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
                direction INTEGER
            );
        """)

    def _parse_and_import(self, cur, parse_func : function, sql):
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

        cur = self.conn.cursor()

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
            INSERT OR IGNORE INTO Services (id, operational_days, start_date, end_date)
                VALUES(?, ?, ?, ?)
        """)
        self._parse_and_import(cur, feed.parse_service_dates,
            'INSERT OR IGNORE INTO ServiceDates (id, date, exception_type) VALUES(?, ?, ?)'                       
        )
        self._parse_and_import(cur, feed.parse_times,""" 
            INSERT OR IGNORE INTO Times (route, service, stop, arrival_time, departure_time,
                sequence, direction) VALUES(?, ?, ?, ?, ?, ?, ?)
        """)
        
        self.conn.commit()

    def download_and_import(self):
        #TODO
        pass

    def get_search_result(self, search_body):
        cur = self.conn.cursor()

        pattern = f'%{search_body}%'

        

        pass

instance = TimetableDatabase(db_loc + 'timetables.db')

if __name__ == '__main__':
    instance.import_local('datasets/itm_yorkshire_gtfs.zip')