import timetables.db as tdb

if __name__ == '__main__':
    timing_points = tdb.instance.get_route_times('33298', 'monday', '1')
    print(timing_points)