from flask import Flask, request, jsonify, render_template
import osmnx as ox
from osmnx import distance
from algo import a_star, uniform_cost_search
import requests
import numpy as np
import math

from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)

G = ox.graph_from_place("Ho Chi Minh City, Vietnam", network_type='drive')
distance.add_edge_lengths(G)


def load_charging_stations(filename="charging.txt"):
    stations = []
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split()
            lat = float(parts[0])
            lon = float(parts[1])
            stations.append({
                "lat": lat,
                "lon": lon
            })
    return stations


# Tải trạm sạc và di chuyển chúng đến node gần nhất
original_charging = load_charging_stations()
charging = []  # Danh sách mới với vị trí đã điều chỉnh
charging_nodes = set()


def haversine(lat1, lon1, lat2, lon2):
    """Tính khoảng cách giữa hai điểm tọa độ (mét)"""
    R = 6371.0 * 1000  # Bán kính Trái đất (mét)
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (sin(dlat / 2) * sin(dlat / 2) +
         cos(lat1_rad) * cos(lat2_rad) *
         sin(dlon / 2) * sin(dlon / 2))

    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def geocode_address(address):
    if not address:
        return None

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "TTNT/1.0"
    }
    response = requests.get(url, params=params, headers=headers, timeout=10)
    data = response.json()
    if data:
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return lat, lon
if G is not None and original_charging:
    for station in original_charging:
        # Tìm node gần nhất với trạm sạc
        node_id = ox.distance.nearest_nodes(G, station["lon"], station["lat"])
        node_data = G.nodes[node_id]

        # Tạo bản ghi trạm sạc mới với vị trí đã điều chỉnh
        adjusted_station = {
            "original_lat": station["lat"],
            "original_lon": station["lon"],
            "lat": node_data['y'],
            "lon": node_data['x'],
            "node_id": node_id
        }
        charging.append(adjusted_station)
        charging_nodes.add(node_id)
@app.route('/charging_nodes', methods=['GET'])
def get_charging_nodes():
    nodes = []
    for station in charging:
        nodes.append({
            'id': station['node_id'],
            'lat': station['lat'],
            'lon': station['lon'],
            'original_lat': station['original_lat'],
            'original_lon': station['original_lon']
        })
    return jsonify(nodes)




@app.route('/')
def index():
    return render_template('index.html')


@app.route('/a_star', methods=['POST'])
def aStar():
    data = request.get_json()
    lat1, lon1 = data['start']
    lat2, lon2 = data['end']

    orig = ox.distance.nearest_nodes(G, lon1, lat1)
    dest = ox.distance.nearest_nodes(G, lon2, lat2)

    route_nodes = a_star(
        G, orig, dest,
        charging_stations=charging_nodes
    )

    if route_nodes is None:
        return jsonify({'error': 'Không tìm được đường đi phù hợp'}), 404

    route_coords = [[node.y, node.x] for node in route_nodes]
    steps = []
    total_distance = 0
    charging_time = 0

    for i, node in enumerate(route_nodes):
        step = {
            'node': node.name,
            'battery': node.battery,
            'lat': node.y,
            'lon': node.x,
            'action': node.action,
            'is_charging_station': node.name in charging_nodes
        }

        if i > 0:
            prev_node = route_nodes[i - 1]
            distance_val = haversine(
                prev_node.y, prev_node.x,
                node.y, node.x
            )
            total_distance += distance_val
            step['distance'] = distance_val
        else:
            step['distance'] = 0

        if node.action == "charge":
            charge_time = node.charge_amount
            charging_time += charge_time
            step['charge_info'] = {
                'amount': node.charge_amount,
                'time': charge_time,
                'from_battery': route_nodes[i - 1].battery,
                'to_battery': node.battery
            }

        steps.append(step)

    return jsonify({
        'route': route_coords,
        'steps': steps,
        'total_distance': total_distance,
        'charging_time': charging_time,
        'travel_time': total_distance / 10  # Giả sử tốc độ 10m/s (36km/h)
    })
@app.route('/ucs', methods=['POST'])
def ucs():

    data = request.get_json()

    lat1, lon1 = data['start']
    lat2, lon2 = data['end']

    orig = ox.nearest_nodes(G, lon1, lat1)
    dest = ox.nearest_nodes(G, lon2, lat2)

    route_nodes = uniform_cost_search(
        G, orig, dest,
        charging_stations=charging_nodes
    )

    if route_nodes is None:
        return jsonify({'error': 'Không tìm được đường đi phù hợp'}), 404

    route_coords = [[node.y, node.x] for node in route_nodes]
    steps = []
    total_distance = 0
    charging_time = 0

    for i, node in enumerate(route_nodes):
        step = {
            'node': node.name,
            'battery': node.battery,
            'lat': node.y,
            'lon': node.x,
            'action': node.action,
            'is_charging_station': node.name in charging_nodes
        }

        if i > 0:
            prev_node = route_nodes[i - 1]
            distance_val = haversine(
                prev_node.y, prev_node.x,
                node.y, node.x
            )
            total_distance += distance_val
            step['distance'] = distance_val
        else:
            step['distance'] = 0

        if node.action == "charge":
            charge_time = node.charge_amount
            charging_time += charge_time
            step['charge_info'] = {
                'amount': node.charge_amount,
                'time': charge_time,
                'from_battery': route_nodes[i - 1].battery,
                'to_battery': node.battery
            }

        steps.append(step)

    return jsonify({
        'route': route_coords,
        'steps': steps,
        'total_distance': total_distance,
        'charging_time': charging_time,
        'travel_time': total_distance / 10
    })


@app.route('/geocode', methods=['POST'])
def geocode():
    data = request.get_json()
    if not data or 'address' not in data:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400

    address = data['address']
    coords = geocode_address(address)
    if coords:
        return jsonify({"lat": coords[0], "lon": coords[1]})
    else:
        return jsonify({"error": "Không tìm thấy địa chỉ"}), 404


@app.route('/charging', methods=['GET'])
def load_charging():
    return jsonify(charging)


if __name__ == '__main__':
    app.run(debug=True, port=5000)