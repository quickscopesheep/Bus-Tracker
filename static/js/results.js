function get_search_element_html(row){
    if(row.type == 'stop'){
        return `
            <span class='result-field result-name'> ${row.name} </span>
            <span class='result-field result-info'> atco: ${row.stop_code} </span>
            <span class='result-field result-type'> Stop </span>
        `
    }else {
       return `
            <span class='result-field result-name'> ${row.name} </span>
            <span class='result-field result-info'> operated by: ${row.agency_name} </span>
            <span class='result-field result-type'> Route </span>
        `
    }
}

function render_search(results){
    results_container = document.getElementById('results-container')

    results_container.innerHTML = ''

    results.forEach(result => {
        const element = document.createElement('button')
        element.className = 'result'

        element.innerHTML = get_search_element_html(result)
        results_container.appendChild(element)

        element.addEventListener('click', () => {
            const url = new URL('/timetable', window.location.origin)
            url.searchParams.set('type', result.type)
            url.searchParams.set('id', result.id)

            window.location.assign(url)
        })
    });
}

function submit_search(search_body) {
    //should prob escape search body
    const url = new URL('/api/search', window.location.origin)
    url.searchParams.set('q', search_body)

    fetch(url).then(response => {
        if(!response.ok){
            throw new Error(`error fetching search: ${response.status}`);
        }
        return response.json()
    }).then(results =>{
        render_search(results)
    })
}

window.addEventListener('load', () => {
    //set search input to be url search value
    const params = new URLSearchParams(window.location.search)

    q = params.get('q')
    document.getElementById('search-text').value = q

    document.getElementById('search-submit-button').addEventListener('click', () => 
        submit_search(document.getElementById('search-text').value)
    )

    if(q != ''){
        submit_search(q)
    }
})

