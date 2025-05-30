from flask import Flask, request, jsonify, render_template
import osmnx as ox
from osmnx import distance
from algo import a_star, uniform_cost_search
import requests

app = Flask(__name__)

G = ox.graph_from_place("Vietnam", network_type='drive')
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
    try:
        data = request.get_json()


        if not data or 'start' not in data or 'end' not in data:
            return jsonify({'error': 'Invalid request data'}), 400

        lat1, lon1 = data['start']
        lat2, lon2 = data['end']

        orig = ox.nearest_nodes(G, lon1, lat1)
        dest = ox.nearest_nodes(G, lon2, lat2)

        if orig is None or dest is None:
            return jsonify({'error': 'Không tìm thấy điểm bắt đầu/kết thúc'}), 404

        route = a_star(G, orig, dest, charging_stations=charging_nodes)

        if route is None:
            return jsonify({'error': 'Không tìm được đường đi phù hợp'}), 404

        # Tạo danh sách tọa độ cho bản đồ
        route_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n, _, _ in route]

        steps = []
        total_distance = 0
        prev_node = None

        for i, (node, battery, (x, y)) in enumerate(route):
            distance = 0
            if prev_node:
                try:
                    # Tính khoảng cách giữa 2 node liên tiếp
                    distance = ox.distance.great_circle_vec(
                        G.nodes[prev_node]['y'], G.nodes[prev_node]['x'],
                        G.nodes[node]['y'], G.nodes[node]['x']
                    )
                    total_distance += distance
                except:
                    pass

            is_charging = node in charging_nodes and battery == 100 and i > 0

            steps.append({
                'name': f"Node {node}",
                'battery': battery,
                'distance': distance,
                'lat': G.nodes[node].get('y', y),
                'lng': G.nodes[node].get('x', x),
                'is_charging': is_charging
            })

            prev_node = node

        return jsonify({
            'route': route_coords,
            'steps': steps,
            'total_distance': total_distance
        })

    except Exception as e:
        print("A-Star Error:", str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/ucs', methods=['POST'])
def ucs():
    try:
        data = request.get_json()

        if not data or 'start' not in data or 'end' not in data:
            return jsonify({'error': 'Invalid request data'}), 400

        lat1, lon1 = data['start']
        lat2, lon2 = data['end']

        orig = ox.nearest_nodes(G, lon1, lat1)
        dest = ox.nearest_nodes(G, lon2, lat2)

        if orig is None or dest is None:
            return jsonify({'error': 'Không tìm thấy điểm bắt đầu/kết thúc'}), 404

        # Debug: in các trạm sạc gần điểm bắt đầu/kết thúc
        print("Charging stations near start:", [
            station for station in charging_nodes
            if ox.distance.great_circle_vec(
                G.nodes[station]['y'], G.nodes[station]['x'],
                G.nodes[orig]['y'], G.nodes[orig]['x']
            ) < 5000  # trong bán kính 5km
        ])


        route = uniform_cost_search(
            G,
            orig,
            dest,
            charging_stations=charging_nodes,
            consumption_rate=10
        )

        route_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n, _, _ in route]
        steps = []
        prev_node = None

        for i, (node, battery, (x, y)) in enumerate(route):
            # Tính khoảng cách từ bước trước
            distance = 0
            if prev_node:
                try:
                    distance = ox.distance.great_circle_vec(
                        G.nodes[prev_node]['y'], G.nodes[prev_node]['x'],
                        G.nodes[node]['y'], G.nodes[node]['x']
                    )
                except Exception as e:
                    print(f"Distance calculation error: {e}")

            # Kiểm tra có phải là trạm sạc không
            is_charging = node in charging_nodes and battery == 100 and i > 0

            steps.append({
                'name': node,
                'battery': battery,
                'distance': distance,
                'lat': G.nodes[node].get('y', y),
                'lon': G.nodes[node].get('x', x),
                'is_charging': is_charging
            })

            prev_node = node

        return jsonify({
            'route': route_coords,
            'steps': steps
        })

    except Exception as e:
        print("UCS Error:", str(e))
        return jsonify({'error': str(e)}), 500

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
