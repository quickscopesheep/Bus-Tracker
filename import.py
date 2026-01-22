import timetables.db as tdb

if __name__ == '__main__':
    tdb.instance.import_local('datasets/itm_yorkshire_gtfs.zip')