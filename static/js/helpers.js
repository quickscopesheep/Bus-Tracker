export function send_to_errorpage (msg){
    //window.location.replace(`/error?msg=${msg}`)
    console.log("should redirect, error:" + msg)
}

export async function fetch_json_or_error (url, cb) {
    const res = await fetch(url)
    if(!res.ok){
        send_to_errorpage(`couldnt fetch ${url} : code: ${res.status}, info: ${res.statusText}`)
    }
    const json = await(res.json())
    cb(json)
}