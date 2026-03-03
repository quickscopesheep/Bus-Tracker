//redirects to error page with msg
export function send_to_errorpage (msg){
    window.location.replace(`/error?msg=${msg}`)
}

//asynchronously fetches from URL parses as json and runs cb as function
//if error occurs redirect to error page with status code and info
export async function fetch_json_or_error (url, cb) {
    const res = await fetch(url)
    if(!res.ok){
        send_to_errorpage(`couldnt fetch ${url} : code: ${res.status}, info: ${res.statusText}`)
    }
    const json = await(res.json())
    cb(json)
}