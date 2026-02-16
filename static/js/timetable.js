class Entity {
    constructor(id, name) {
        this.id = id
        this.name = name
        this.sequence = -1
    }

    update_sequence(new_sequence){
        this.sequence = Math.max(this.sequence, new_sequence)
    }
}

const time_to_seconds = (t) => t.split(':').reduce((acc, x) => acc * 60 + parseInt(x))

class Trip {
    constructor(){
        this.times = new Map()
        this.start_time = 999999999999
    }

    add_entity(id, time) {
        this.times.set(id, time)
        this.start_time = Math.min(this.start_time, time_to_seconds(time))
    }
}

//global variable for data
let app_state = {
    type: null,
    id: null,

    info: null,
    timetable_data: null
}

function organise_timetable_data(data){
    entities_map = new Map()

    data.forEach(t => {
        if(!entities_map.has(t.entity_id))
            entities_map.set(t.entity_id, new Entity(t.entity_id, t.entity_name))
        entities_map.get(t.entity_id).update_sequence(t.sequence)
    });

    const entities = Array.from(entities_map.values())
    entities.sort((a, b) => a.sequence - b.sequence)

    const trips_map = new Map()

    data.forEach(t => {
        if(!trips_map.has(t.trip))
            trips_map.set(t.trip, new Trip())
        trips_map.get(t.trip).add_entity(t.entity_id, t.arrival_time)
    })

    var trips = Array.from(trips_map.values())

    trips.sort((a, b) => a.start_time - b.start_time)

    return {entities, trips}
}

function render_timetable() {
    const service_day = $('#service-day').val()
    const timing_status = $('#timing-status').val()
    const direction = $('#direction').val()

    let data = app_state.timetable_data
    data = data.filter((t) => t.service_days[service_day] == '1')

    if(app_state.type == 'route'){
        data = data.filter((t) => timing_status == 0 || t.timing_status == timing_status)
        data = data.filter((t) => t.direction == direction)
    }

    const {entities, trips} = organise_timetable_data(data)

    entities.forEach((e) => {
        let row = $('<tr></tr>')
            .addClass('generated-table-row')
            .appendTo('#timetable')
        row.append(`<td>${e.name}</td>`)

        trips.forEach((t) => {
            time_element = $('<td></td>')
                .appendTo(row)
                .text(t.times.has(e.id) ? t.times.get(e.id) : '')
        })
    })

    $('#table-loading-text').hide()
    $('#table-header').show()
    $('#table-entity-header').text(app_state.type == 'route' ? 'Stop' : 'Route')
}

function render_header() {
    $('#timetable-title').html(`
        ${app_state.info.name}
        ${app_state.info.name2 != '' ? `<span>(${app_state.info.name2})</span>` : ''}
    `)

    if(app_state.type === 'stop'){
        $('#timetable-info').html(`
            <span>atco: ${app_state.info.stop_code}</span>
            <span>locality: ${app_state.info.stop_locality}</span>
            <span>town: ${app_state.info.stop_town}</span>
        `)
    }else{
        $('#timetable-info').html(`
            <span>operated by <a href=${app_state.info.agency_url}>${app_state.info.agency_name}</a></span>
        `)
    }
}

function refresh_timetable(){
    $('.generated-table-row').remove()
    render_timetable()
}

function is_bookmarked(){
}

function toggle_bookmarked() {
    
}

$(document).ready(() => {
    const params = new URLSearchParams(window.location.search)
    app_state.type = params.get('type')
    app_state.id = params.get('id')

    $('#timetable-title').text('Loading...')
    $('#table-header').hide()

    if(app_state.type === 'stop') {
        $('#timing-status').hide()
        $('#direction').hide()
    }

    $.get(`api/${app_state.type}/info?id=${app_state.id}`, (data, status) => {
        if(status != 'success'){
            window.location.replace(`/error?code=400&msg=${app_state.type} info request failed`)
        }else{
            json = JSON.parse(data)
            if(!json.ok) window.location.replace(`/error?code=400&msg=${app_state.type} invald info response`)
            
            app_state.info = json.data
            render_header()
        }
    })

    fetch_timetable = () => $.get(`api/${app_state.type}/timetable?id=${app_state.id}`, (data, status) => {
        if(status != 'success'){
            window.location.replace(`/error?code=400&msg=${app_state.type} timetable request failed`)
        }else{
            json = JSON.parse(data)
            if(!json.ok) window.location.replace(`/error?code=400&msg=${app_state.type} invald timetable response`)

            app_state.timetable_data = json.data
            render_timetable(app_state.timetable_data)
        }
    })

    refresh_timetable = () => {
        $('.generated-table-row').remove()
        render_timetable()
    }

    $('#service-day').change(() => refresh_timetable())
    $('#timing-status').change(() => refresh_timetable())
    $('#direction').change(() => refresh_timetable())

    fetch_timetable()
})
