import sqlite3

import requests
from google.transit import gtfs_realtime_pb2

import os
import time
import dotenv

import dbhelpers

from pathlib import Path

GTFS_REALTIME_URL = 'https://data.bus-data.dft.gov.uk/api/v1/gtfsrtdatafeed/'

IMPORT_CHUNK_SIZE = 1000
UPDATE_FREQUENCY = 20

dotenv.load_dotenv()
API_KEY = os.environ.get('BODS_API_KEY')

class MapDB:
    def __init__(self, path : Path):
        self.path = path
        self.currentFeed = None

        self._init_db()

    #crates tables if not already existing
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

    #reads from gtfs rt protobuf
    #returned tuple contains (id, route, trip, lon, lat, bearing, licencePlate, timestamp)
    def _handle_vehicle_message(self) -> tuple:
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
                    vehicle.vehicle.license_plate,
                    vehicle.timestamp
                )

    #fetches feed and uplodas data to DB
    def fetch_feed(self):
        response = requests.get(f'{GTFS_REALTIME_URL}?api_key={API_KEY}&')

        if not response.ok:
            print(response.status_code, response.reason)
            return

        self.currentFeed = gtfs_realtime_pb2.FeedMessage()
        self.currentFeed.ParseFromString(response.content)

        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        dbhelpers.parse_and_import(cur, self._handle_vehicle_message, """
            INSERT OR REPLACE INTO Vehicles (id, route, trip, lon, lat, bearing, licencePlate, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """)

        cur.execute("DELETE FROM vehicles WHERE timestamp < ?;", (int(time.time())-300,))

        conn.commit()

    #returns all vehicles on a route
    #returned tuple contains (vehicle_id, trip_id, timestamp, lon, lat, bearing)
    def get_vehicle_positions(self, route_id : str) -> tuple[list[dict], bool]:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.execute("""
            SELECT id, trip, timestamp, lon, lat, bearing
                FROM Vehicles
                WHERE route = :route_id;
        """, {'route_id':route_id})


        return [dbhelpers.result_to_dict(row, ('vehicle_id', 'trip_id', 'timestamp', 'lon', 'lat', 'bearing')) for row in cur.fetchall()], True

instance = MapDB('db/map.db')