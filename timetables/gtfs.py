from pathlib import Path

import zipfile
import csv
import io


class TripHeadsign:
    def __init__(self, name, direction):
        self.name = name
        self.direction = direction
        self.frequency = 1

class GTFSFeed:
    def __init__(self, path : Path):
        self.path = path

        self.zf = zipfile.ZipFile(self.path)

        self._validate_zip(self.zf.namelist())

        self._route_headsigns = None

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
        f = self.zf.open(file_name)
        stream = io.TextIOWrapper(f, encoding='utf-8', newline='')
        reader = csv.DictReader(stream)

        return reader

    def parse_stops(self):
        reader = self._get_csv_reader('stops.txt')
        return {row.get('stop_code', '') : row.get('stop_id', '') for row in reader}

    #(id, name, url)
    def parse_agencies(self):
        reader = self._get_csv_reader('agency.txt')

        for row in reader:
            yield (
                row.get('agency_id', ''),
                row.get('agency_name', ''),
                row.get('agency_url', '')
            )

    def _add_headsign(self, route_id, headsign, direction):
        if route_id not in self._route_headsigns:
            self._route_headsigns[route_id] = {}
        
        if(headsign not in self._route_headsigns[route_id]):
            self._route_headsigns[route_id][headsign] = TripHeadsign(headsign, direction)
        
        self._route_headsigns[route_id][headsign].frequency += 1

    #(id, route, direction, service, headsign)
    def parse_trips(self):
        reader = self._get_csv_reader('trips.txt')

        self._route_headsigns = {}

        for row in reader:
            self._add_headsign(row.get('route_id'), row.get('trip_headsign'), row.get('direction_id'))

            trip = (
                row.get('trip_id', ''),
                row.get('route_id', ''),
                row.get('direction_id', ''),
                row.get('service_id', ''),
                row.get('trip_headsign', '')
            )
            yield trip


    def _process_headsigns(self):
        computed_headsigns = {}

        for route_id, route_headsigns in self._route_headsigns.items():
            outbound_headsigns = filter(lambda x : x.direction == '0', list(route_headsigns.values()))
            outbound_headsigns = sorted(outbound_headsigns, key=lambda x : x.frequency, reverse=True)
            
            inbound_headsigns = filter(lambda x : x.direction == '1', list(route_headsigns.values()))
            inbound_headsigns = sorted(inbound_headsigns, key=lambda x : x.frequency, reverse=True)

            if len(inbound_headsigns) == 0 or len(outbound_headsigns) == 0:
                continue

            computed_headsigns[route_id] = (inbound_headsigns[0], outbound_headsigns[0])
        
        #remove reference as no longer need the large amount of data stored
        self._route_headsigns = None

    #(id, agency, name, longer name, desc)
    def parse_routes(self):
        reader = self._get_csv_reader('routes.txt')

        if self._route_headsigns == None:
            raise Exception("Must parse trips before routes")

        headsigns = self._process_headsigns()

        for row in reader:
            yield (
                row.get('route_id', ''),
                row.get('agency_id', ''),
                row.get('route_short_name', ''),
                row.get('route_long_name', ''),
                row.get('route_desc', ''),
                headsigns.get(row.get('route_id'), '')
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

    # handle interpolated times
    # (trip_id, stop_id, arrival_time, departure_time, index, timing_status)
    def parse_times(self):
        reader = self._get_csv_reader('stop_times.txt')
        
        for row in reader:
            yield (
                row.get('trip_id', ''),
                row.get('stop_id', ''),
                row.get('arrival_time', '00:00:00'),
                row.get('departure_time', '00:00:00'),
                int(row.get('stop_sequence', '')),
                row.get('timepoint', '0')
            )
    
if __name__ == '__main__':
    feed = GTFSFeed('datasets/itm_yorkshire_gtfs.zip')
    for route in feed.parse_routes():
        print(route)
    
    