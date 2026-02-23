
//function render_results(data) {
//    $('.result').remove()
//
//    if(data.length == 0){
//        $('#no-results-warning').show()
//        return;
//    }else
//        $('#no-results-warning').hide()
//
//    data.forEach((result) => {
//        el = $('<button>')
//            .addClass('result')
//            .appendTo('#results-container')
//        el.html(get_result_html(result))
//        el.click(() => {
//            const url = new URL('/timetable', window.location.origin)
//            url.searchParams.set('type', result.type)
//            url.searchParams.set('id', result.id)
//
//            window.location.assign(url)
//        })
//    })
//}
//
//function submit_search(q) {
//    $.get(`/api/search?q=${q}`, (data, status) => {
//        console.log(status)
//        if(status != 'success'){
//            window.location.replace(`/error?code=400&msg=search request failed`)
//        }else {
//            console.log(data)
//
//            json = JSON.parse(data)
//            if(!json.ok){
//                window.location.replace(`/error?code=400&msg=invalid search response`)
//            }
//
//            render_results(json.data)
//        }
//    })
//}
//
//$(document).ready(() => {
//    const params = new URLSearchParams(window.location.search)
//    q = params.get('q')
//    
//    $('#search-task').val(q)
//
//    $('#no-results-warning').hide()
//
//    $('#search-submit-button').click(() => {
//        submit_search($('#search-text').val())
//    })
//
//    submit_search(q)
//})

import {send_to_errorpage, fetch_json_or_error} from "./helpers.js"

const app_state = {
    search_body: null,

    num_results: null,

    page_size: 20,
    page_no: 1,

    pages : new Map()
}

function get_result_html(row){
    if(row.type == 'stop')
        return `
            <span class='result-field result-name'> ${row.name} </span>
            <span class='result-field result-info'> atco: ${row.stop_code} </span>
            <span class='result-field result-info'> bearing: ${row.bearing} </span>
            <span class='result-field result-info'> ${row.locality} </span>
            <span class='result-field result-type'> Stop </span>
        `
    else
        return `
            <span class='result-field result-name'> ${row.name} </span>
            ${row.orign != "" && row.dst != "" ? `<span class='result-field result-sub-name'> (${row.origin + ' - ' + row.dst}) </span>` : ""}
            <span class='result-field result-info'> operated by: ${row.agency_name} </span>
            <span class='result-field result-type'> Route </span>
        `
}

async function render_page() {
    if(!app_state.pages.has(app_state.page_no)){
        const offset = (app_state.page_no-1) * app_state.page_size
        await fetch_json_or_error(`/api/search?q=${app_state.search_body}&offset=${offset}&size=${app_state.page_size}`,
            (json) => {
                if(!json.ok) send_to_errorpage('invalid search query')
                app_state.pages.set(app_state.page_no, json.data)
            }
        )
    }

    const data = app_state.pages.get(app_state.page_no)

    $('.result').remove()

    if(data.length == 0){
        $('#no-results-warning').show()
        return;
    }else
        $('#no-results-warning').hide()

    data.forEach((result) => {
        let el = $('<button>')
            .addClass('result')
            .appendTo('#results-container')
        el.html(get_result_html(result))
        el.click(() => {
            const url = new URL('/timetable', window.location.origin)
            url.searchParams.set('type', result.type)
            url.searchParams.set('id', result.id)
        
            window.location.assign(url)
        })
    })
}

$(document).ready(() => {
    const params = new URLSearchParams(window.location.search)
    app_state.search_body = params.get('q', '')

    $('#search-text').val(app_state.search_body)

    $('#search-submit-button').click(() => {
        window.location.href = `/results?q=${$('#search-text').val()}`
    })


    $('#page-number-input').change(() => {
        app_state.page_no = parseInt($('#page-number-input').val())
        render_page()
    })

    fetch_json_or_error(`/api/search-num-results?q=${app_state.search_body}`, (json) => {
        if(!json.ok)
            send_to_errorpage('could not fetch number of results')
        app_state.num_results = json.num_results
        $('#page-number-input').attr('max', Math.ceil(app_state.num_results/app_state.page_size))
    }).then(render_page)
})