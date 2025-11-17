dummy_data = {
    "254": {
        'a': 'huddersfield',
        'b': 'leeds',
        'operator': 'arriva'
    }
}

def build_search_result(search_body):
    if search_body in dummy_data:
        return dummy_data[search_body]
    return {}