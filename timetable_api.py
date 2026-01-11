import os

import naptan

from dotenv import load_dotenv

load_dotenv()

from timetables import api as tapi
from timetables import parse

LIMIT = 10_000

dummy_data = {
    "254": {
        'a': 'huddersfield',
        'b': 'leeds',
        'operator': 'arriva'
    }
}

def _get_atco_codes():
    return naptan.ATCO_CODES.query('Area == "West Yorkshire"')['Code'].to_list()

def pull_timetable():
    pass

def build_search_result(search_body):
    if search_body in dummy_data:
        return dummy_data[search_body]
    return {}

#testing
if __name__ == '__main__':
    #codes = _get_atco_codes()
    req = tapi.BODSTimetableRequest(
        atcos = None,
        nocs = None,
        search = "",
        limit = 10
    )

    datasets = req.get()

    #cheesing shit
    parser = parse.DataSetParser(open('datasets/transx_464/BODS_PF0007157_1_20250921_37.xml'))
    parser.parse()

    tt = parser.journeys[0].get_timetable()
    for tp in iter(tt.values()): print(tp)
