export class Bookmarks {
    constructor(){
        this.bookmarks = new Map(
            Object.entries(JSON.parse(
                window.localStorage.getItem('bookmarks')
            ))
        )
    }

    get_bookmarks() {
        return this.bookmarks
    }

    add_bookmark(id, info) {
        this.bookmarks.set(id, info)

        console.log(this.bookmarks)
        window.localStorage.setItem('bookmarks', JSON.stringify(
            Object.fromEntries(this.bookmarks)
        ))
    }

    remove_bookmark(id){
        this.bookmarks.delete(id)
        
        console.log(this.bookmarks)
        window.localStorage.setItem('bookmarks', JSON.stringify(
            Object.fromEntries(this.bookmarks)
        ))
    }

    is_bookmarked(id){
        return this.bookmarks.has(id)
    }
}