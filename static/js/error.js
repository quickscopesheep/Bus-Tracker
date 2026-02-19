$(document).ready(() => {
    const params = new URLSearchParams(window.location.search)
    const msg = params.get('msg')

    $('#error').text(`code: ${msg}`)
})