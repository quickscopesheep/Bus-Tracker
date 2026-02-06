import sqlite3

import requests
from google.transit import gtfs_realtime_pb2

from apscheduler.schedulers.background import BackgroundScheduler

import os
import dotenv

GTFS_REALTIME_URL = 'https://data.bus-data.dft.gov.uk/api/v1/gtfsrtdatafeed/'

IMPORT_CHUNK_SIZE = 1000
UPDATE_FREQUENCY = 20

dotenv.load_dotenv()
API_KEY = os.environ.get('BODS_API_KEY')

class MapDB:
    def __init__(self, path):
        self.path = path
        self.currentFeed = None

        self._init_db()

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.fetch_feed, "interval", seconds=UPDATE_FREQUENCY)
        self.scheduler.start()
        pass

    def _init_db(self):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.executescript("""
            PRAGMA journal_mode=WAL;
            
            CREATE TABLE IF NOT EXISTS Vehicles(
                id TEXT PRIMARY KEY,
                route TEXT,
                trip TEXT,
                timestamp INTEGER,
                lon TEXT,
                lat TEXT,
                bearing TEXT,
                licencePlate TEXT
            );
        """)

        pass

    def _parse_and_import(self, cur, parse_func, sql):
        chunk = []

        for stop in parse_func():
            chunk.append(stop)

            if len(chunk) == IMPORT_CHUNK_SIZE:
                cur.executemany(sql, chunk)
                chunk.clear()
            
        if len(chunk) > 0:
            cur.executemany(sql, chunk)

    #(id, route, trip, lon, lat, bearing, licencePlate)
    def _handle_vehicle_message(self):
        for entity in self.currentFeed.entity:
            if entity.HasField('vehicle'):
                vehicle = entity.vehicle
                yield (
                    vehicle.vehicle.id,
                    vehicle.trip.route_id,
                    vehicle.trip.trip_id,
                    str(vehicle.position.longitude),
                    str(vehicle.position.latitude),
                    str(vehicle.position.bearing),
                    vehicle.vehicle.license_plate
                )

    def fetch_feed(self):
        response = requests.get(f'{GTFS_REALTIME_URL}?api_key={API_KEY}&')

        if not response.ok:
            print(response.status_code, response.reason)
            return

        self.currentFeed = gtfs_realtime_pb2.FeedMessage()
        self.currentFeed.ParseFromString(response.content)

        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        self._parse_and_import(cur, self._handle_vehicle_message, """
            INSERT OR REPLACE INTO Vehicles (id, route, trip, lon, lat, bearing, licencePlate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
        """)

        #cur.execute("DELETE FROM vehicles WHERE timestamp < unixepoch() - 300;")

        conn.commit()
        pass


instance = MapDB('db/map.db')