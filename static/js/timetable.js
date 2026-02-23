import { Bookmarks } from "./bookmark.js"
import {send_to_errorpage, fetch_json_or_error} from "./helpers.js"

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
    timetable_data: null,
    info: null,
    bookmarks: null
}

function organise_timetable_data(data){
    let entities_map = new Map()

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
            .append(`<td>${e.name}</td>`)

        trips.forEach((t) => {
            $('<td></td>')
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

function update_bookmark_image(){
    if(app_state.bookmarks.is_bookmarked(app_state.id)){
        $('#bookmark-button img').attr('src', 'static/img/bookmark_checked.svg')
    }else{
        $('#bookmark-button img').attr('src', 'static/img/bookmark.svg')
    }
}

function toggle_bookmarked(){
    if(app_state.bookmarks.is_bookmarked(app_state.id)){
        app_state.bookmarks.remove_bookmark(app_state.id)
    }else{
        app_state.bookmarks.add_bookmark(app_state.id, app_state.info.name, window.location.toString())
    }

    update_bookmark_image()
}

$(document).ready(() => {
    const params = new URLSearchParams(window.location.search)
    app_state.type = params.get('type')
    app_state.id = params.get('id')

    app_state.bookmarks = new Bookmarks()
    update_bookmark_image()

    $('#bookmark-button').click(toggle_bookmarked)
    
    $('#map-button').click(() => {
        window.location.href = `/map?id=${app_state.id}`
    })

    $('#timetable-title').text('Loading...')
    $('#table-header').hide()

    if(app_state.type === 'stop') {
        $('#timing-status').hide()
        $('#direction').hide()
    }

    const refresh_timetable = () => {
        $('.generated-table-row').remove()
        render_timetable()
    }

    $('#service-day').change(() => refresh_timetable())
    $('#timing-status').change(() => refresh_timetable())
    $('#direction').change(() => refresh_timetable())
    
    fetch_json_or_error(`/api/${app_state.type}/info?id=${app_state.id}`, (json) => {
        if(!json.ok) send_to_errorpage('invalid request parameters')

        app_state.info = json.data
        render_header()
    })
    fetch_json_or_error(`/api/${app_state.type}/timetable?id=${app_state.id}`, (json) => {
        if(!json.ok) send_to_errorpage('invalid request parameters')
        
        app_state.timetable_data = json.data
        render_timetable()
    })
})
