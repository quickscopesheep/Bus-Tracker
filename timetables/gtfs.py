from pathlib import Path

import zipfile
import csv
import io

class GTFSFeed:
    def __init__(self, path : Path):
        self.path = path

        self.zf = zipfile.ZipFile(self.path)

        self._validate_zip(self.zf.namelist())

    def _validate_zip(self, names):
        if 'agency.txt' not in names: return False
        #Technically optional but shall enforce mandatory stops file for simplicity
        if 'stops.txt' not in names: return False
        if 'routes.txt' not in names: return False
        if 'trips.txt' not in names: return False
        if 'stop_times.txt' not in names: return False

        #TODO: callender dates

        return True

    def _get_csv_reader(self, file_name):
        file = self.zf.open(file_name)
        stream = io.TextIOWrapper(file, encoding='utf-8', newline='')
        reader = csv.DictReader(stream)

        return reader

    # (id, atco, name, lat, long)
    def parse_stops(self):
        reader = self._get_csv_reader('stops.txt')

        for row in reader:
            yield (
                row.get('stop_id',''),
                #NAPTAN?
                row.get('stop_code', ''),
                row.get('stop_name', ''),
                row.get('stop_lat'),
                row.get('stop_lon'),
            )

    #(id, name, url)
    def parse_agencies(self):
        reader = self._get_csv_reader('agency.txt')

        for row in reader:
            yield (
                row.get('agency_id', ''),
                row.get('agency_name', ''),
                row.get('agency_url', '')
            )

    #(id, agency, name, longer name, desc)
    def parse_routes(self):
        reader = self._get_csv_reader('routes.txt')
        for row in reader:
            yield (
                row.get('route_id', ''),
                row.get('agency_id', ''),
                row.get('route_short_name', ''),
                row.get('route_long_name', ''),
                row.get('route_desc', '')
            )

    def parse_service(self):
        reader = self._get_csv_reader('calendar.txt')

        for row in reader:
            yield (
                row.get('service_id', ''),
                row.get('monday', '0'),
                row.get('tuesday', '0'),
                row.get('wednesday', '0'),
                row.get('thursday', '0'),
                row.get('friday', '0'),
                row.get('saturday', '0'),
                row.get('sunday', '0'),
                row.get('start_date', ''),
                row.get('end_date', '')
            )
    
    def parse_service_dates(self):
        reader = self._get_csv_reader('calendar_dates.txt')

        for row in reader:
            yield (
                row.get('service_id', ''),
                row.get('date', ''),
                # 1=service added, 2=service removed
                row.get('exception_type', '')
            )

    #(id, route, direction, service)
    def _parse_trips(self):
        reader = self._get_csv_reader('trips.txt')

        self.trips = {}

        for row in reader:
            trip = (
                row.get('trip_id', ''),
                row.get('route_id', ''),
                row.get('direction_id', ''),
                row.get('service_id', '')
            )
            self.trips[trip[0]] = trip
            yield trip

    # handle interpolated times
    # (route_id, trip_id, stop_id, arrival_time, departure_time, index, direction, service)
    def parse_times(self):
        trips = {}
        for trip in self._parse_trips(): trips[trip[0]] = trip

        reader = self._get_csv_reader('stop_times.txt')
        
        for row in reader:
            trip = trips.get(row.get('trip_id'))
            if trip == None: continue
            
            #TODO: handle services
            yield (
                trip[1], # Route ID
                trip[3], # Service ID
                row.get('stop_id', ''),
                row.get('arrival_time', '00:00:00'),
                row.get('departure_time', '00:00:00'),
                int(row.get('stop_sequence', '')),
                trip[2], # Direction
                row.get('timepoint', '0')
            )
    
if __name__ == '__main__':
    feed = GTFSFeed('datasets/itm_yorkshire_gtfs.zip')
    for route in feed.parse_routes():
        print(route)
    
    