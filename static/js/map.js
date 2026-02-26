import { fetch_json_or_error, send_to_errorpage } from "./helpers.js"

const ACCESS_TOKEN = 'pk.eyJ1Ijoibm9haHdoZXdhbGwiLCJhIjoiY21sYXNzd2VkMGcyZDNkcXV0aGF1Y3hmZyJ9.hyH7YmrvYgdgV8uq_S529g'

class Vehicle {
    constructor(id, trip, lon, lat, bearing, timestamp){
        this.id = id
        this.trip = trip

        let element = document.createElement('div')
        element.className = 'bg-blue-500 rounded-xl p-1 z-[5]'
        element.innerHTML = '<img src="static/img/bus.svg">'
        //element.src = 'static/img/bus.svg'
        element.w = 32
        element.h = 32

        this.marker = new mapboxgl.Marker({
            element: element,
            rotationAlignment: 'map'
        }).setLngLat([lon, lat]).addTo(app_state.map)

        this.setPos(lon, lat, bearing, timestamp)
    }

    setPos(lon, lat, bearing, timestamp){
        this.lon = lon
        this.lat = lat
        this.bearing = bearing
        this.timestamp = timestamp

        this.marker.setLngLat([lon, lat])
        //this.marker.setRotation(bearing)
    }

    dispose(){
        this.marker.remove()
    }
}

let app_state = {
    route: null,
    map: null,
    vehicles: new Map()
}

async function update_vehicle_positions(){
    await fetch_json_or_error(`/api/map/livedata?id=${app_state.route}`, (json) => {
        if(!json.ok)
            send_to_errorpage("invalid vehicle position query")

        let vehicle_updates = new Map()
        Array.from(json.result).forEach(e => {
            vehicle_updates.set(e.vehicle_id, e)
        })

        vehicle_updates.values().forEach(v => {
            if(app_state.vehicles.has(v.vehicle_id))
                app_state.vehicles.get(v.vehicle_id).setPos(v.lon, v.lat, v.bearing, v.timestamp)
            else
                //TODO: handle when vehicle switches trip, doesnt matter much for now
                app_state.vehicles.set(v.vehicle_id, new Vehicle(
                    v.vehicle_id,
                    v.trip_id,
                    v.lon, v.lat,
                    v.bearing, v.timestamp
                ))
        })

        let removeList = new Array()
        app_state.vehicles.forEach(v => {
            if(!vehicle_updates.has(v.id)){
                v.dispose()
                removeList.push(v.id)
            }
        })

        removeList.forEach(toRemove => {
            app_state.vehicles.delete(toRemove)
        })

        console.log(app_state.vehicles)
    })
}

function create_stop_markers() {
    fetch_json_or_error(`/api/map/stops?id=${app_state.route}`, (json) => {
        const stops = Array.from(json.data)
        stops.forEach(stop => {

            console.log(stop)

            let element = document.createElement('div')
            element.className = 'bg-amber-500 rounded-xl p-1 z-[0] hover:cursor-pointer'
            element.innerHTML = '<img class="size-full" src="static/img/stop.svg">'
            element.onclick = () => {
                window.location.href = `/timetable?type=stop&id=${stop.id}`
            }

            new mapboxgl.Marker({
                element: element,
                rotationAlignment: 'map'
            }).setLngLat([parseFloat(stop.lon), parseFloat(stop.lat)]).addTo(app_state.map)
        })
    })    
}

$(document).ready(() => {
    const params = new URLSearchParams(window.location.search)
    app_state.route = params.get('id')

    mapboxgl.accessToken = ACCESS_TOKEN
    app_state.map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/standard',
        projection: 'mercator'
    })

    create_stop_markers()

    const update_loop = async () => {
        await update_vehicle_positions()
        setTimeout(update_loop, 10*1000)
    }

    update_loop().then(() => {
        let sum = [0, 0]
        app_state.vehicles.forEach((v, k) => {
            sum[0] += parseFloat(v.lon)
            sum[1] += parseFloat(v.lat)
        })

        sum[0] /= app_state.vehicles.size
        sum[1] /= app_state.vehicles.size

        app_state.map.setCenter(sum)
        app_state.map.setZoom(10)
    })
})