$(document).ready(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const msg = params.get('msg')

    $('#error').text(`code: ${code}, ${msg}`)
})