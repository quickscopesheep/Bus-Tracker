import { Bookmarks } from "./bookmark.js"

let app_state = {
    bookmarks : null,
    bookmarks_visible : false
}

//render bookmarks to list
function render_bookmarks() {
    if(app_state.bookmarks.get_map().size != 0) $('#no-bookmarks-text').hide()

    app_state.bookmarks.get_map().values().forEach((info) => {
        $(`<a href="${info.url}">${info.name}</a>`)
        .addClass('p-2 bg-blue-500 hover:bg-blue-400 rounded-xl text-white font-bold')
        .appendTo('#bookmarks-container')
    })
}

$(document).ready(() => {
    app_state.bookmarks = new Bookmarks()
    $('#bookmarks-box').hide()

    render_bookmarks()

    $('#bookmarks-button').click(() => {
        console.log("hello")
        if(!app_state.bookmarks_visible){
            app_state.bookmarks_visible = true
            $('#bookmarks-box').show()
        }else{
            app_state.bookmarks_visible = false
            $('#bookmarks-box').hide()
        }
    })

})