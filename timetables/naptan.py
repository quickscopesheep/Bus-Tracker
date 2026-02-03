from pathlib import Path
import csv

class NaptanImporter:
    def __init__(self, path: Path, ids):
        self.path = path
        self.ids = ids

    def _parse_stop(self, gtfs_id, row):
        return (
                gtfs_id,
                row.get('ATCOCode'),
                row.get('CommonName', ''),
                row.get('ShortCommonName', ''),
                row.get('Indicator', ''),
                row.get('Bearing', ''),
                row.get('Longitude', ''),
                row.get('Latitude', ''),
                row.get('Street', ''),
                row.get('Landmark', ''),
                row.get('Town', ''),
                row.get('NptgLocalityCode', ''),
                ','.join([row.get('LocalityName', ''), row.get('ParentLocalityName')]),
            )

    #(Name, ShortName, Indicator, Bearing, Lon, Lat, Street, Landmark, Town, Nptg, LocalityName)
    def parse_stops(self):
        f = open(self.path)
        reader = csv.DictReader(f)

        for row in reader:
            atco_id = row.get('ATCOcode', '')
            naptan_id = row.get('NaptanCode', '')
            result = ()

            if atco_id in self.ids:
                result = self._parse_stop(self.ids[atco_id], row)
            elif naptan_id in self.ids:
                result = self._parse_stop(self.ids[naptan_id], row)
            else:
                continue

            yield result