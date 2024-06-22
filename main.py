import json
import os

import folium
import requests
from dotenv import load_dotenv
from flask import Flask
from geopy import distance


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection'][
        'featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def calculate_distance(coords1, coords2):
    return distance.distance(
        (float(coords1[1]), float(coords1[0])),
        (float(coords2[1]), float(coords2[0]))
    ).km


def get_coffee_distance(cafes):
    return sorted(cafes, key=lambda cafe: cafe['distance'])[:5]


def hello_world():
    with open('cafes_map.html', "r", encoding="utf-8") as file:
        return file.read()


def main():
    load_dotenv()
    path_file = os.getenv("PATH_FILE")
    api_key = os.getenv("API_KEY")

    address = input("Где вы находитесь ? ")
    coords = fetch_coordinates(api_key, address)

    with open(path_file, "r", encoding="cp1251") as my_file:
        cafes = my_file.read()

    cafes = json.loads(cafes)

    results = []
    for cafe in cafes:
        cafe_coords = (str(cafe['geoData']['coordinates'][0]),
                       str(cafe['geoData']['coordinates'][1]))
        dist = calculate_distance(coords, cafe_coords)
        results.append({
            "title": cafe["Name"],
            "distance": dist,
            "latitude": cafe['geoData']['coordinates'][1],
            "longitude": cafe['geoData']['coordinates'][0]
        })

    closest_cafes = get_coffee_distance(results)

    m = folium.Map(location=(float(coords[1]), float(coords[0])),
                   zoom_start=13)

    folium.Marker(
        location=(float(coords[1]), float(coords[0])),
        popup='Вы здесь',
        icon=folium.Icon(color='blue')
    ).add_to(m)

    for cafe in closest_cafes:
        folium.Marker(
            location=(cafe['latitude'], cafe['longitude']),
            popup=f"{cafe['title']}<br>Расстояние: {cafe['distance']:.2f} км",
            icon=folium.Icon(color='red')
        ).add_to(m)

    m.save('cafes_map.html')

    app = Flask(__name__)
    app.add_url_rule('/', 'hello', hello_world)
    app.run('0.0.0.0')


if __name__ == "__main__":
    main()
