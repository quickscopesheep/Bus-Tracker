function get_result_html(row){
    if(row.type == 'stop')
        return `
            <span class='result-field result-name'> ${row.name} </span>
            <span class='result-field result-info'> atco: ${row.stop_code} </span>
            <span class='result-field result-type'> Stop </span>
        `
    else
        return `
            <span class='result-field result-name'> ${row.name} </span>
            <span class='result-field result-info'> operated by: ${row.agency_name} </span>
            <span class='result-field result-type'> Route </span>
        `
}

function render_results(data) {
    $('.result').remove()

    if(data.length == 0){
        $('#no-results-warning').show()
        return;
    }else
        $('#no-results-warning').hide()

    data.forEach((result) => {
        el = $('<button>')
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

function submit_search(q) {
    $.get(`/api/search?q=${q}`, (data, status) => {
        if(status != 'success'){
            //window.location.replace(`/error?code=400&msg=search request failed`)
        }else {
            console.log(data)

            json = JSON.parse(data)
            if(!json.ok){
                //window.location.replace(`/error?code=400&msg=invalid search response`)
            }

            render_results(json.data)
        }
    })
}

$(document).ready(() => {
    const params = new URLSearchParams(window.location.search)
    q = params.get('q')
    
    $('#no-results-warning').hide()

    $('#search-submit-button').click(() => {
        submit_search($('#search-text').val())
    })

    submit_search(q)
})