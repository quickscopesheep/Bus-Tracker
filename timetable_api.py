import os

import naptan

from dotenv import load_dotenv

load_dotenv()

import timetables

LIMIT = 10_000
BODS_API_URL = 'https://data.bus-data.dft.gov.uk/api/v1/dataset/?'

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
    req = timetables.api.BODSTimetableRequest(
        atcos = None,
        nocs = None,
        search = "",
        limit = 10
    )

    req.send()