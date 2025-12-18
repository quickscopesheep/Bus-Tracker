import os
import uuid

from typing import List
from pathlib import Path
from zipfile import ZipFile

import requests

from dotenv import load_dotenv

BODS_API_URL = 'https://data.bus-data.dft.gov.uk/api/v1/dataset/?'

BODS_API_KEY = os.environ.get('BODS_API_KEY')
DATASET_SAVE_PATH = os.environ.get('DATASET_SAVE_LOCATION')

load_dotenv()

class TimetableDataSet:
    def __init__(self, metadata : dict):
        self.metadata = metadata
        self.url = metadata['url']
        self.id = metadata['id']

        self.path = Path(DATASET_SAVE_PATH + str(self.id) + '.zip')

        self.download_dataset()
        self.convert_dataset()

    def download_dataset(self):
        if self.path.exists() and not self.path.is_dir():
            print(f'Dataset already cached: {self.url}')
            return

        print('Downloading dataset: ', self.url)
        response = requests.get(self.url)

        #TODO: support raw xml
        with open(self.path, 'wb') as file:
            file.write(response.content)
        return
    
    def convert_dataset(self):     
        return
    
    def get_path(self):
        return self.path
    
    def get_id(self):
        return self.id

class BODSTimetableRequest:
    def __init__(self, atcos : List[str], nocs : List[str], search : str, limit : int):
        self.atcos = atcos
        self.nocs = nocs
        self.search = search
        self.limit = limit

        self.api_key = BODS_API_KEY

        self.response = None
        pass

    def get(self):
        print('Requesting API Data')
        self.response = requests.get(BODS_API_URL, {
            'api_key': self.api_key,
            'search': self.search,
            'limit': str(self.limit)
        })

        response_body = self.response.json()
        timetable_datasets = [TimetableDataSet(meta) for meta in response_body["results"]]

        return timetable_datasets