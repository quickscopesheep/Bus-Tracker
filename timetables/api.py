import os
import requests

from typing import List

from dotenv import load_dotenv

BODS_API_URL = 'https://data.bus-data.dft.gov.uk/api/v1/dataset/?'

load_dotenv()

class BODSTimetableRequest:
    def __init__(self, atcos : List[str], nocs : List[str], search : str, limit : int):
        self.atcos = atcos
        self.nocs = nocs
        self.search = search
        self.limit = limit

        self.api_key = os.environ.get('bods-api-key')

        self.response = None
        pass

    def send(self):
        self.response = requests.get(BODS_API_URL, {
            'api_key': self.api_key,
            'search': self.search
            'limit': str(self.limit)
        })

        print(self.response)