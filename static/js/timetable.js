function render_timetable(table_element, type, timing_points, direction) {
    table_element.innerHTML = ''

    const entities = {}
    const entity_names = {}

    //sort times
    //sort by sequence
    
    Array.from(timing_points).forEach(point => {
        if(point.direction != direction)
            return
        if(point.entity_id in entities) {
            entities[point.entity_id].push(point.arrival_time)
        }else{
            entities[point.entity_id] = [point.arrival_time]
            entity_names[point.entity_id] = [point.name]
        }
    })

    const table_header_element = table_element.appendChild(document.createElement('tr'))

    table_header_element.appendChild(document.createElement('th')).textContent = type
    table_header_element.appendChild(document.createElement('th')).textContent = 'Times'

    for(const entity in entities){
        const current_row = table_element.appendChild(document.createElement('tr'))
        current_row.appendChild(document.createElement('td')).textContent = entity_names[entity]

        times_array = Array.from(entities[entity])

        times_array.forEach(time => {
            current_row.appendChild(document.createElement('td')).textContent = time
        })
    }
}

function render_stop_info(info){
    document.title = info.stop_name
    document.getElementById('timetable-title').innerText = `Stop: ${info.stop_name}`

    atco_element = document.getElementById('atco')
    atco_element.textContent = `atco:${info.stop_code}`
}

function render_route_info(info){
    document.title = info.route_name
    document.getElementById('timetable-title').innerText = `Route: ${info.route_name}`

    operator_element = document.getElementById('operator')
    operator_element.style.display = 'inline'
    operator_element.textContent = `Operator: ${info.agency_name}`
    operator_element.href = `${info.agency_url}`
}

function on_recieve_timetable(type, data) {
    if(type == 'stop')
        render_stop_info(data.info)
    else
        render_route_info(data.info)

    render_timetable(document.getElementById('timetable'), type, data.timing_points, 0)
}

function fetch_timetable() {
    service_day = document.getElementById('service-day').value
    timing_status = document.getElementById('timing-status').value

    const params = new URLSearchParams(window.location.search)
    type = params.get('type')
    id = params.get('id')

    const url = new URL(`/api/${type}`, window.location.origin)
    url.searchParams.set('id', id)
    url.searchParams.set('service-day', service_day)
    url.searchParams.set('timing-status', timing_status)

    fetch(url).then(response => {
        if(!response.ok)
            throw new Error(`error fetching search: ${response.status}`)
        return response.json()
    }).then(data =>{
        on_recieve_timetable(type, data)
    })
}

window.addEventListener('load', () => {
    Array.from(document.getElementById('timetable-info').children).forEach(e => {
        e.style.display = 'none'
    })

    document.getElementById('service-day').addEventListener('change', fetch_timetable)
    document.getElementById('timing-status').addEventListener('change', fetch_timetable)

    fetch_timetable()
})