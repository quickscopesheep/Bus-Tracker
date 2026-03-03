import sqlite3
from typing import Callable, Tuple

IMPORT_CHUNK_SIZE = 1000

#itterates over a function generator and adds the results to the database using the sql statement provided. adds in chunks of IMPORT_CHUNK_SIZE
def parse_and_import(cur : sqlite3.Cursor, parse_func : Callable, sql : str):
    chunk = []
    for stop in parse_func():
        chunk.append(stop)
        if len(chunk) == IMPORT_CHUNK_SIZE:
            cur.executemany(sql, chunk)
            chunk.clear()
        
    if len(chunk) > 0:
        cur.executemany(sql, chunk)

#takes tuple of columns and constructs a dictionary
def result_to_dict(result : Tuple, schema : Tuple) -> dict:
    return {
        schema[i]: result[i] for i in range(len(schema))
    }