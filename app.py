from flask import Flask, request, jsonify, render_template
import osmnx as ox
from osmnx import distance
from algo import a_star, uniform_cost_search
import requests

app = Flask(__name__)

G = ox.graph_from_place("Ho Chi Minh City, Vietnam", network_type='drive')
distance.add_edge_lengths(G)

def load_charging_stations(filename="charging.txt"):
    stations = []
    with open(filename, 'r') as f:
        for line in f:
            lat_str, lon_str = line.strip().split()
            lat = float(lat_str)
            lon = float(lon_str)
            stations.append({
                "lat": lat,
                "lon": lon
            })

    return stations

charging = load_charging_stations()
charging_nodes = {
    ox.distance.nearest_nodes(G, station["lon"], station["lat"])
    for station in charging
}

def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "TTNT/1.0"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    if data:
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return lat, lon
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/a_star', methods=['POST'])
def aStar():
    data = request.get_json()
    lat1, lon1 = data['start']
    lat2, lon2 = data['end']

    orig = ox.nearest_nodes(G, lon1, lat1)
    dest = ox.nearest_nodes(G, lon2, lat2)

    route = a_star(G, orig, dest, charging_stations=charging_nodes)

    if route is None:
        return jsonify({'error': 'Không tìm được đường đi phù hợp'}), 404

    route_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n, _, _ in route]
    return jsonify({'route': route_coords})


@app.route('/ucs', methods=['POST'])
def ucs():
    data = request.get_json()
    lat1, lon1 = data['start']
    lat2, lon2 = data['end']

    orig = ox.nearest_nodes(G, lon1, lat1)
    dest = ox.nearest_nodes(G, lon2, lat2)

    route = uniform_cost_search(G, orig, dest, charging_stations=charging_nodes)

    if route is None:
        return jsonify({'error': 'Không tìm được đường đi phù hợp'}), 404

    route_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n, _, _ in route]
    return jsonify({'route': route_coords})

@app.route('/geocode', methods=['POST'])
def geocode():
    data = request.get_json()
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
    app.run(debug=True)
