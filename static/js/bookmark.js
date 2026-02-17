export class Bookmarks {
    constructor(){
        let storage = window.localStorage.getItem('bookmarks')
        if(storage == null){
            storage = '{}'
            window.localStorage.setItem('bookmarks', storage)
        }

        this.bookmarks = new Map(
            Object.entries(JSON.parse(
                window.localStorage.getItem('bookmarks')
            ))
        )
    }

    get_map() {
        return this.bookmarks
    }

    add_bookmark(id, name, url) {
        this.bookmarks.set(id, {
            name: name,
            url: url
        })

        window.localStorage.setItem('bookmarks', JSON.stringify(
            Object.fromEntries(this.bookmarks)
        ))
    }

    remove_bookmark(id){
        this.bookmarks.delete(id)
        
        window.localStorage.setItem('bookmarks', JSON.stringify(
            Object.fromEntries(this.bookmarks)
        ))
    }

    is_bookmarked(id){
        return this.bookmarks.has(id)
    }
}