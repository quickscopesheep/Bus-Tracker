const ACCESS_TOKEN = "pk.eyJ1Ijoibm9haHdoZXdhbGwiLCJhIjoiY21sYXNzd2VkMGcyZDNkcXV0aGF1Y3hmZyJ9.hyH7YmrvYgdgV8uq_S529g"

class Vehicle {
    constructor(id, trip, lon, lat, bearing, timestamp){
        this.id = id
        this.trip = trip

        let element = document.createElement('img')
        element.src = "static/img/bus.svg"
        element.w = 32
        element.h = 32

        this.marker = new mapboxgl.Marker({
            element: element,
            rotationAlignment: 'map'
        }).setLngLat([lon, lat]).addTo(map)

        this.setPos(lon, lat, bearing, timestamp)
    }

    setPos(lon, lat, bearing, timestamp){
        this.lon = lon
        this.lat = lat
        this.bearing = bearing
        this.timestamp = timestamp

        this.marker.setLngLat([lon, lat])
        this.marker.setRotation(bearing)
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

function fetchVehiclePositions(){
    $.get(`/api/map/livedata?id=${app_state.route}`, (data, status) => {
        if(status != 'success')
            throw new Error('could not fetch info')

        let vehicle_updates = new Map()
        JSON.parse(data).forEach(e => {
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
    })
}

$(document).ready(() => {
    const params = new URLSearchParams(window.location.search)
    app_state.route = params.get('id')

    mapboxgl.accessToken = ACCESS_TOKEN
    map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/standard',
        projection: 'mercator'
    })

    fetchVehiclePositions()
})