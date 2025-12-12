import os
import requests

from dotenv import load_dotenv

BODS_API_URL = 'https://data.bus-data.dft.gov.uk/api/v1/dataset/?'

load_dotenv()

class BODSTimetableRequest:
    def __init__(self, atco : str, noc : str, search : str, limit : str):
        self.atco = atco
        self.noc = noc
        self.search = search
        self.limit = limit

        self.api_key = os.environ.get('bods-api-key')

        self.response = None
        pass

    def send(self):
        self.response = requests.get(BODS_API_URL, {
            'api_key': 
        })