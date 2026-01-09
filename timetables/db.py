import sqlite3
import zipfile
import xml.etree.cElementTree as ET

import parse
import api

connection = sqlite3.connect('db/timetables.db')

def append_dataset(dataset : api.TimetableDataSet):
    print(f'parsing data set: {dataset.get_id()}')

    with zipfile.ZipFile(dataset.get_path()) as zip:
        for info in zip.infolist():
            if info.is_dir(): continue

            with zip.open(info) as file:
                p = parse.DataSetParser(file, connection.cursor())
                p.parse()


if __name__ == '__main__':
    req = api.BODSTimetableRequest(
        atcos = None,
        nocs = None,
        search = "",
        limit = 1
    )

    dataset = req.get()[0]
    append_dataset(dataset)