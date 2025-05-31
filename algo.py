from math import radians, sin, cos, sqrt, atan2
import heapq
import itertools
import networkx as nx

class Node:
    __slots__ = (
        'name', 'parent', 'g', 'h', 'battery', 'x', 'y', 'action',
        'charge_amount', 'is_emergency_charge', 'target'
    )

    def __init__(self, name, parent=None, g=0, h=0, battery=100, x=None, y=None,
                 action="move", charge_amount=0, is_emergency_charge=False, target=None):
        self.name = name
        self.parent = parent
        self.g = g
        self.h = h
        self.battery = battery
        self.x = x
        self.y = y
        self.action = action
        self.charge_amount = charge_amount
        self.is_emergency_charge = is_emergency_charge
        self.target = target  # 'goal' hoặc 'charging_station'

    def f(self):
        return self.g + self.h

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 * 1000
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

def load_charging_stations(G, filename="charging.txt", max_distance=10.0):
    stations = set()
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split()
            lat = float(parts[0])
            lon = float(parts[1])
            min_dist = float('inf')
            min_node = None
            for node_id, data in G.nodes(data=True):
                if 'x' in data and 'y' in data:
                    d = haversine(lat, lon, data['y'], data['x'])
                    if d < min_dist:
                        min_dist = d
                        min_node = node_id
            if min_dist <= max_distance and min_node is not None:
                stations.add(min_node)
    return stations

def calculate_distance(G, node1, node2):

    data1 = G.nodes[node1]
    data2 = G.nodes[node2]
    return haversine(data1['y'], data1['x'], data2['y'], data2['x'])


def find_nearest_charging_station(G, current_node, charging_stations, consumption_rate):
    """Tìm trạm sạc gần nhất có thể đến được với pin hiện tại"""
    nearest_station = None
    min_distance = float('inf')
    min_battery_needed = float('inf')

    for station in charging_stations:
        if station == current_node.name:
            continue

        distance = calculate_distance(G, current_node.name, station)
        battery_needed = distance * consumption_rate

        if battery_needed <= current_node.battery and distance < min_distance:
            min_distance = distance
            min_battery_needed = battery_needed
            nearest_station = station

    if nearest_station:

        return nearest_station, min_distance, min_battery_needed

    return None, float('inf'), float('inf')

def a_star_to_charging(G, start, charging_stations, max_battery=100, consumption_rate=0.25):
    """
    Tìm đường đến trạm sạc gần nhất bằng thuật toán A*
    Trả về đường đi đến trạm sạc gần nhất
    """

    start_data = G.nodes[start]
    start_node = Node(
        name=start,
        g=0,
        battery=max_battery,
        x=start_data['x'],
        y=start_data['y'],
        target='charging_station'
    )

    station, _, _ = find_nearest_charging_station(G, start_node, charging_stations, consumption_rate)
    if not station:
        return None

    start_node.h = calculate_distance(G, start, station)

    best_state = {}
    rounded_battery = round(start_node.battery, 1)
    best_state[(start_node.name, rounded_battery)] = start_node.g

    counter = itertools.count()
    open_set = []
    heapq.heappush(open_set, (start_node.f(), next(counter), start_node))

    while open_set:
        current_f, _, current_node = heapq.heappop(open_set)

        if current_node.name in charging_stations:
            path = []
            while current_node:
                path.append(current_node)
                current_node = current_node.parent
            return path[::-1]

        # Cập nhật heuristic nếu cần
        if current_node.h == 0 or current_node.name not in charging_stations:
            station, _, _ = find_nearest_charging_station(G, current_node, charging_stations, consumption_rate)
            if station:
                current_node.h = calculate_distance(G, current_node.name, station)

        # Duyệt hàng xóm
        for neighbor in G.neighbors(current_node.name):
            if neighbor not in G.nodes:
                continue

            edge_data = min(
                G[current_node.name][neighbor].values(),
                key=lambda x: x.get('length', float('inf')))
            distance_val = edge_data.get('length', float('inf'))
            if distance_val == float('inf'):
                distance_val = calculate_distance(G, current_node.name, neighbor)


            battery_needed = distance_val * consumption_rate

            if current_node.battery < battery_needed:
                continue

            new_battery = current_node.battery - battery_needed
            new_g = current_node.g + distance_val
            neighbor_data = G.nodes[neighbor]

            # Tính heuristic cho neighbor (khoảng cách đến trạm sạc gần nhất)
            station, _, _ = find_nearest_charging_station(G, current_node, charging_stations, consumption_rate)
            if station:
                h_value = calculate_distance(G, neighbor, station)
            else:
                h_value = float('inf')

            neighbor_node = Node(
                name=neighbor,
                parent=current_node,
                g=new_g,
                battery=new_battery,
                h=h_value,
                x=neighbor_data['x'],
                y=neighbor_data['y'],
                target='charging_station'
            )

            rounded_battery = round(neighbor_node.battery, 1)
            state_key = (neighbor_node.name, rounded_battery)

            if state_key not in best_state or best_state[state_key] > neighbor_node.g:
                best_state[state_key] = neighbor_node.g
                heapq.heappush(open_set, (neighbor_node.f(), next(counter), neighbor_node))

    return None

def a_star(G, start, goal, charging_stations, max_battery=100, consumption_rate=0.25):

        start_data = G.nodes[start]
        start_node = Node(
            name=start,
            g=0,
            battery=max_battery,
            x=start_data['x'],
            y=start_data['y'],
            target='goal'
        )
        start_node.h = calculate_distance(G, start, goal)

        best_state = {}
        rounded_battery = round(start_node.battery, 1)
        best_state[(start_node.name, rounded_battery)] = start_node.g

        counter = itertools.count()
        open_set = []
        heapq.heappush(open_set, (start_node.f(), next(counter), start_node))

        while open_set:
            current_f, _, current_node = heapq.heappop(open_set)


            if current_node.name == goal:
                path = []
                while current_node:
                    path.append(current_node)
                    current_node = current_node.parent
                return path[::-1]

            # Tích hợp sạc tại trạm như một phần của không gian trạng thái
            if current_node.name in charging_stations and current_node.battery < max_battery:
                needed_charge = max_battery - current_node.battery
                charged_battery = max_battery
                charged_node = Node(
                    name=current_node.name,
                    parent=current_node,
                    g=current_node.g,
                    battery=charged_battery,
                    h=current_node.h,
                    x=current_node.x,
                    y=current_node.y,
                    action="charge",
                    charge_amount=needed_charge,
                    target='goal'
                )

                rounded_battery = round(charged_node.battery, 1)
                state_key = (charged_node.name, rounded_battery)

                if state_key not in best_state or best_state[state_key] > charged_node.g:
                    best_state[state_key] = charged_node.g
                    heapq.heappush(open_set, (charged_node.f(), next(counter), charged_node))

                    continue

            # Kiểm tra nếu cần tìm trạm sạc
            required_battery_to_goal = current_node.h * consumption_rate * 1.2
            if current_node.battery < required_battery_to_goal:

                charging_path = a_star_to_charging(
                    G,
                    current_node.name,
                    charging_stations,
                    max_battery,
                    consumption_rate,
                )

                if charging_path:

                    full_path = []
                    temp = current_node
                    while temp:
                        full_path.append(temp)
                        temp = temp.parent
                    full_path.reverse()

                    full_path.extend(charging_path[1:])

                    last_node = charging_path[-1]
                    goal_path = a_star(
                        G,
                        last_node.name,
                        goal,
                        charging_stations,
                        max_battery,
                        consumption_rate,
                    )

                    if goal_path:
                        full_path.extend(goal_path[1:])
                        return full_path

            # Duyệt hàng xóm bình thường
            has_valid_neighbor = False
            for neighbor in G.neighbors(current_node.name):
                if neighbor not in G.nodes:
                    continue

                edge_data = min(
                    G[current_node.name][neighbor].values(),
                    key=lambda x: x.get('length', float('inf')))
                distance_val = edge_data.get('length', calculate_distance(G, current_node.name, neighbor))


                battery_needed = distance_val * consumption_rate

                if current_node.battery < battery_needed:
                    continue

                has_valid_neighbor = True
                new_battery = current_node.battery - battery_needed
                new_g = current_node.g + distance_val
                neighbor_data = G.nodes[neighbor]

                neighbor_node = Node(
                    name=neighbor,
                    parent=current_node,
                    g=new_g,
                    battery=new_battery,
                    h=calculate_distance(G, neighbor, goal),
                    x=neighbor_data['x'],
                    y=neighbor_data['y'],
                    target='goal'
                )

                rounded_battery = round(neighbor_node.battery, 1)
                state_key = (neighbor_node.name, rounded_battery)

                if state_key not in best_state or best_state[state_key] > neighbor_node.g:
                    best_state[state_key] = neighbor_node.g
                    heapq.heappush(open_set, (neighbor_node.f(), next(counter), neighbor_node))

            # Xử lý tình huống không có lối đi
            if not has_valid_neighbor and current_node.name not in charging_stations:

                station, distance, battery_needed = find_nearest_charging_station(
                    G, current_node, charging_stations, consumption_rate
                )

                if station and battery_needed <= current_node.battery:
                    new_battery = current_node.battery - battery_needed
                    new_g = current_node.g + distance
                    station_data = G.nodes[station]

                    emergency_node = Node(
                        name=station,
                        parent=current_node,
                        g=new_g,
                        battery=new_battery,
                        h=calculate_distance(G, station, goal),
                        x=station_data['x'],
                        y=station_data['y'],
                        action="emergency_charge",
                        is_emergency_charge=True,
                        target='goal'
                    )

                    rounded_battery = round(emergency_node.battery, 1)
                    state_key = (emergency_node.name, rounded_battery)

                    if state_key not in best_state or best_state[state_key] > emergency_node.g:
                        best_state[state_key] = emergency_node.g
                        heapq.heappush(open_set, (emergency_node.f(), next(counter), emergency_node))

        return None


def uniform_cost_search(G, start, goal, charging_stations, max_battery=100, consumption_rate=0.015):

        start_data = G.nodes[start]
        start_node = Node(
            name=start,
            g=0,
            battery=max_battery,
            x=start_data['x'],
            y=start_data['y']
        )

        best_state = {}
        rounded_battery = round(start_node.battery, 4)
        best_state[(start_node.name, rounded_battery)] = start_node.g

        counter = itertools.count()
        open_set = []
        heapq.heappush(open_set, (start_node.g, next(counter), start_node))

        while open_set:
            current_g, _, current_node = heapq.heappop(open_set)

            if current_node.name == goal:
                path = []
                while current_node:
                    path.append(current_node)
                    current_node = current_node.parent
                return path[::-1]

            # Tích hợp sạc tại trạm như một phần của không gian trạng thái
            if current_node.name in charging_stations:
                distance_to_goal = calculate_distance(G, current_node.name, goal)
                max_range = current_node.battery / consumption_rate
                required_battery = distance_to_goal * consumption_rate

                if current_node.battery < max_battery and required_battery > current_node.battery:
                    buffer = required_battery * 0.2
                    needed_charge = min(
                        max(required_battery + buffer - current_node.battery, 0),
                        max_battery - current_node.battery
                    )
                    if needed_charge > 0:
                        charged_battery = min(current_node.battery + needed_charge, max_battery)
                        charged_node = Node(
                            name=current_node.name,
                            parent=current_node,
                            g=current_node.g,
                            battery=charged_battery,
                            x=current_node.x,
                            y=current_node.y,
                            action="charge",
                            charge_amount=needed_charge
                        )

                        rounded_battery = round(charged_node.battery, 4)
                        state_key = (charged_node.name, rounded_battery)

                        if state_key not in best_state or best_state[state_key] > charged_node.g:
                            best_state[state_key] = charged_node.g
                            heapq.heappush(open_set, (charged_node.g, next(counter), charged_node))

                            continue

            # Duyệt hàng xóm
            has_valid_neighbor = False
            for neighbor in G.neighbors(current_node.name):
                if neighbor not in G.nodes:
                    continue

                edge_data = min(
                    G[current_node.name][neighbor].values(),
                    key=lambda x: x.get('length', float('inf')))
                distance_val = edge_data.get('length', calculate_distance(G, current_node.name, neighbor))

                battery_needed = distance_val * consumption_rate

                if current_node.battery < battery_needed:
                    continue
                has_valid_neighbor = True
                new_battery = current_node.battery - battery_needed
                new_g = current_node.g + distance_val
                neighbor_data = G.nodes[neighbor]

                neighbor_node = Node(
                    name=neighbor,
                    parent=current_node,
                    g=new_g,
                    battery=new_battery,
                    x=neighbor_data['x'],
                    y=neighbor_data['y']
                )

                rounded_battery = round(neighbor_node.battery, 4)
                state_key = (neighbor_node.name, rounded_battery)

                if state_key not in best_state or best_state[state_key] > neighbor_node.g:
                    best_state[state_key] = neighbor_node.g
                    heapq.heappush(open_set, (neighbor_node.g, next(counter), neighbor_node))

            # Xử lý tình huống không có lối đi
            if not has_valid_neighbor and current_node.name not in charging_stations:
                station, distance, battery_needed = find_nearest_charging_station(
                    G, current_node, charging_stations, consumption_rate
                )

                if station and battery_needed <= current_node.battery:
                    new_battery = current_node.battery - battery_needed
                    new_g = current_node.g + distance
                    station_data = G.nodes[station]

                    emergency_node = Node(
                        name=station,
                        parent=current_node,
                        g=new_g,
                        battery=new_battery,
                        x=station_data['x'],
                        y=station_data['y'],
                        action="emergency_charge",
                        is_emergency_charge=True
                    )

                    rounded_battery = round(emergency_node.battery, 4)
                    state_key = (emergency_node.name, rounded_battery)

                    if state_key not in best_state or best_state[state_key] > emergency_node.g:
                        best_state[state_key] = emergency_node.g
                        heapq.heappush(open_set, (emergency_node.g, next(counter), emergency_node))

        return None
