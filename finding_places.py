API_KEY = 'AIzaSyBix8XpBniYgiAPnwYSuY9s3aN1QOdo-d4'

import sys
import pandas
import googlemaps
import gmaps
import time
import pprint
import requests
from ipywidgets.embed import embed_minimal_html
from IPython.display import Image 

def main(arg):
    placemaps = googlemaps.Client(key = API_KEY)
    [mylat, mylong] = arg.split(" ")
    mylat = float(mylat)
    mylong = float(mylong)
    # mylat = 9.9144942418604
    # mylong = 78.08978803904138
    coordi_str = str(mylat) + ' ' + str(mylong)
    place_result = placemaps.places_nearby(location = coordi_str, radius = 4000, type = 'lodging', open_now = False)

    lat = [mylat]
    lng = [mylong]
    placenames = []

    for place in place_result['results']:
        my_place_id = place['place_id']
        my_fields = ['name', 'geometry/location/lng', 'geometry/location/lat', 'type']
        place_detail = placemaps.place(place_id = my_place_id, fields = my_fields)
        placenames.append(place_detail['result']['name'])
        lat.append(place_detail['result']['geometry']['location']['lat'])
        lng.append(place_detail['result']['geometry']['location']['lng'])

    count = 1
    for i in placenames:
        print(str(count) + " --> " + i)
        count += 1
    print("\n")
    flag = 0
    while(flag == 0):
        print("Choose a location")
        index = int(input())
        if(index >0 and index<=count):
            flag = 1
    print("\n")

    origin = (mylat, mylong)
    destlat = lat[index:index+1]
    destlng = lng[index:index+1]
    destination = (destlat[0], destlng[0])

    from datetime import datetime

    now = datetime.now()
    gmaps.configure(api_key = API_KEY)
    fig = gmaps.figure()
    layer = gmaps.directions.Directions(origin, destination, mode = 'car', api_key = API_KEY, departure_time = now)
    fig.add_layer(layer)
    embed_minimal_html('export.html', views=[fig])
    print(fig)
    Image(fig)
    print("\n")

    current = datetime.now()
    direct = placemaps.directions(origin, destination, mode = 'driving', departure_time = current)
    print(placenames[index-1])
    print(direct[0]['legs'][0]['distance']['text'])
    print(direct[0]['legs'][0]['duration']['text'])
    print(direct[0]['legs'][0]['end_address'])


if __name__ == "__main__":
    main(sys.argv[1])