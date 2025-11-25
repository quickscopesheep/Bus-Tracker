dummy_data = {
    '123': {
        'a': '',
        'b': '',
        'opperator': '',
    },
    '456': {
        'a': '',
        'b': '',
        'opperator': '',
    },
    '459': {
        'a': '',
        'b': '',
        'opperator': '',
    },
    '127': {
        'a': '',
        'b': '',
        'opperator': '',
    },
}

def build_search_result(search_body):
    results = []
    for k in dummy_data:
        if search_body in k:
            results += {
                'label': k,
                'href' : f'/timetable?route={k}'
            }

    return results