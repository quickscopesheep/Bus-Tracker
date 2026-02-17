import { Bookmarks } from "./bookmark.js"

let app_state = {
    bookmarks : null,
    bookmarks_visible : false
}

function render_bookmarks() {
    if(app_state.bookmarks.get_map().size != 0) $('#no-bookmarks-text').hide()

    app_state.bookmarks.get_map().values().forEach((info) => {
        $(`<a href="${info.url}">${info.name}</a>`).appendTo('#bookmarks-container')
    })
}

$(document).ready(() => {
    app_state.bookmarks = new Bookmarks()
    $('#bookmarks-container').hide()

    render_bookmarks()

    $('#bookmarks-button').click(() => {
        if(!app_state.bookmarks_visible){
            app_state.bookmarks_visible = true
            $('#bookmarks-container').show()
        }else{
            app_state.bookmarks_visible = false
            $('#bookmarks-container').hide()
        }
    })

})