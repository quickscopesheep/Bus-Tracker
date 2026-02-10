IMPORT_CHUNK_SIZE = 1000

def parse_and_import(cur, parse_func, sql):
    chunk = []
    for stop in parse_func():
        chunk.append(stop)
        if len(chunk) == IMPORT_CHUNK_SIZE:
            cur.executemany(sql, chunk)
            chunk.clear()
        
    if len(chunk) > 0:
        cur.executemany(sql, chunk)

def result_to_dict(result, schema):
        return {
            schema[i]: result[i] for i in range(len(schema))
        }