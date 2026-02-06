import requests

from pathlib import Path
import os
from datetime import datetime

import timetables.db as tdb

#BODS_DATASET_URL = 'https://data.bus-data.dft.gov.uk/timetable/download/gtfs-file/all/'
BODS_DATASET_URL = 'https://data.bus-data.dft.gov.uk/timetable/download/gtfs-file/yorkshire/'
NAPTAN_URL = 'https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=csv'

DOWNLOADS_PATH = 'temp/'

def download_data(url, output_path : Path):
    r = requests.get(url, stream=True)

    chunk_size = 1024*8
    downloaded = 0
    timer = 0

    with open(output_path, 'wb') as file:
        for chunk in r.iter_content(chunk_size):
            file.write(chunk)
            downloaded += chunk_size
            timer += 1
            if timer == 1000:
                timer = 0
                print(f'downloading {url} {downloaded / 1_000_000}MB')


if __name__ == '__main__':
    if not Path(DOWNLOADS_PATH).exists(): os.mkdir(DOWNLOADS_PATH)

    bods_path = Path(DOWNLOADS_PATH+'timetables.zip')
    naptan_path = Path(DOWNLOADS_PATH+'stops.csv')

    if not bods_path.exists():
        download_data(BODS_DATASET_URL, bods_path)
    if not naptan_path.exists():
        download_data(NAPTAN_URL, naptan_path)

    tdb.instance.import_local(bods_path, naptan_path)