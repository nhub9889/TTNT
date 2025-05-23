import folium
import requests
import webbrowser
import os

# Hàm 1: Tạo bản đồ và vẽ marker tại một điểm
def draw_marker(lat, lon, map_object=None, popup="Vị trí", color="blue"):
    if map_object is None:
        map_object = folium.Map(location=[lat, lon], zoom_start=13)
    folium.Marker(
        [lat, lon],
        popup=popup,
        icon=folium.Icon(color=color, icon='info-sign')
    ).add_to(map_object)
    return map_object

# Hàm 2: Vẽ đường từ điểm A đến B sử dụng OSRM (hoặc API khác)
def draw_route(start_lat, start_lon, end_lat, end_lon, map_object=None):
    # Gọi API OSRM
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    response = requests.get(url)
    data = response.json()
    
    # Lấy danh sách tọa độ đường đi
    coords = data['routes'][0]['geometry']['coordinates']
    coords = [(lat, lon) for lon, lat in coords]  # Đảo lại theo [lat, lon]

    if map_object is None:
        mid_lat = (start_lat + end_lat) / 2
        mid_lon = (start_lon + end_lon) / 2
        map_object = folium.Map(location=[mid_lat, mid_lon], zoom_start=13)

    # Vẽ polyline
    folium.PolyLine(coords, color="blue", weight=5).add_to(map_object)
    
    # Vẽ marker A và B
    draw_marker(start_lat, start_lon, map_object, "Điểm A", color="red")
    draw_marker(end_lat, end_lon, map_object, "Điểm B", color="blue")
    return map_object

# Hàm 3: Trả về các đường đi có thể từ A đến B (nếu có)
def get_routes(start_lat, start_lon, end_lat, end_lon):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?alternatives=true&overview=full&geometries=geojson"
    response = requests.get(url)
    data = response.json()
    routes = []
    for route in data['routes']:
        coords = [(lat, lon) for lon, lat in route['geometry']['coordinates']]
        routes.append(coords)
    return routes

def draw_charging_stations(file_path, map_object):
    with open(file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            lat, lon = map(float, line.split(','))
            folium.Marker(
                [lat, lon],
                popup="Trạm sạc ⚡",
                icon=folium.Icon(color="green", icon="bolt", prefix='fa')
            ).add_to(map_object)




map2 = draw_route(10.862622, 106.660172, 10.7769, 106.7009)

draw_charging_stations("charging.txt", map2)

map2.save("route_map.html")

import webbrowser, os
webbrowser.open("file://" + os.path.realpath("route_map.html"))
