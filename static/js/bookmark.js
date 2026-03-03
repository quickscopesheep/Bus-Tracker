export class Bookmarks {
    //inititalises map from local storage
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

    //returns hashmap of bookmarks
    get_map() {
        return this.bookmarks
    }

    //adds bookmark to map
    //id : string, entity id
    //name : string, entity name
    //url : string, url for entity
    add_bookmark(id, name, url) {
        this.bookmarks.set(id, {
            name: name,
            url: url
        })

        window.localStorage.setItem('bookmarks', JSON.stringify(
            Object.fromEntries(this.bookmarks)
        ))
    }

    //removes bookmark
    //id: string, bookmark to remove
    remove_bookmark(id){
        this.bookmarks.delete(id)
        
        window.localStorage.setItem('bookmarks', JSON.stringify(
            Object.fromEntries(this.bookmarks)
        ))
    }

    //gets if bookmark is present
    //id : string
    is_bookmarked(id){
        return this.bookmarks.has(id)
    }
}