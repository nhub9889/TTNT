import heapq
import math


class Node:
    __slots__ = ('name', 'parent', 'g', 'h', 'battery', 'x', 'y')  # Tối ưu bộ nhớ

    def __init__(self, name, parent=None, g=0, h=0, battery=100, x=None, y=None):
        self.name = name
        self.parent = parent
        self.g = g
        self.h = h
        self.battery = battery
        self.x = x
        self.y = y

    def f(self):
        return self.g + self.h

    def __lt__(self, other):
        return self.f() < other.f()


def euclidean_distance(G, node1, node2):
    x1, y1 = G.nodes[node1]['x'], G.nodes[node1]['y']
    x2, y2 = G.nodes[node2]['x'], G.nodes[node2]['y']
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def uniform_cost_search(G, start, goal, charging_stations, max_battery=100, consumption_rate=0.001):
    # Khởi tạo trạng thái ban đầu
    start_x, start_y = G.nodes[start]['x'], G.nodes[start]['y']
    start_node = Node(start, g=0, battery=max_battery, x=start_x, y=start_y)

    # Dictionary lưu trạng thái tốt nhất (node, battery_level) -> chi phí g
    best_state = {}
    rounded_battery = round(start_node.battery, 2)
    best_state[(start_node.name, rounded_battery)] = start_node.g

    open_set = [(start_node.g, start_node)]  # (Ưu tiên theo g, node)
    heapq.heapify(open_set)

    while open_set:
        current_cost, current_node = heapq.heappop(open_set)

        # Kiểm tra đích
        if current_node.name == goal:
            path = []
            while current_node:
                path.append((current_node.name, current_node.battery, (current_node.x, current_node.y)))
                current_node = current_node.parent
            return path[::-1]

        # Xử lý sạc tại trạm (nếu là trạm sạc và pin chưa đầy)
        if current_node.name in charging_stations and current_node.battery < max_battery:
            charged_node = Node(
                name=current_node.name,
                parent=current_node,  # SỬA: parent phải là current_node
                g=current_node.g,
                battery=max_battery,
                x=current_node.x,
                y=current_node.y
            )
            # Kiểm tra trạng thái sau khi sạc
            rounded_battery = round(charged_node.battery, 2)
            state_key = (charged_node.name, rounded_battery)

            # Chỉ thêm nếu trạng thái mới tốt hơn
            if state_key not in best_state or best_state[state_key] > charged_node.g:
                best_state[state_key] = charged_node.g
                heapq.heappush(open_set, (charged_node.g, charged_node))

        # Duyệt các node kế tiếp
        for neighbor in G.neighbors(current_node.name):
            # SỬA: xử lý multiple edges
            edge_data = min(
                G[current_node.name][neighbor].values(),
                key=lambda x: x.get('length', 1.0)
            )
            distance = edge_data.get('length', 1.0)
            battery_needed = distance * consumption_rate

            # Kiểm tra pin đủ để đi
            if current_node.battery < battery_needed:
                continue  # Bỏ qua nếu không đủ pin

            new_battery = current_node.battery - battery_needed
            new_g = current_node.g + distance
            nx, ny = G.nodes[neighbor]['x'], G.nodes[neighbor]['y']

            neighbor_node = Node(
                name=neighbor,
                parent=current_node,
                g=new_g,
                battery=new_battery,
                x=nx,
                y=ny
            )

            # Kiểm tra trạng thái mới
            rounded_battery = round(neighbor_node.battery, 2)
            state_key = (neighbor_node.name, rounded_battery)

            # Chỉ thêm nếu chưa tồn tại hoặc tốt hơn
            if state_key not in best_state or best_state[state_key] > neighbor_node.g:
                best_state[state_key] = neighbor_node.g
                heapq.heappush(open_set, (neighbor_node.g, neighbor_node))

    return None

def a_star(G, start, goal, charging_stations, max_battery=100, consumption_rate=1):
    # Khởi tạo trạng thái ban đầu
    start_x, start_y = G.nodes[start]['x'], G.nodes[start]['y']
    start_node = Node(start, g=0, battery=max_battery, x=start_x, y=start_y)
    start_node.h = euclidean_distance(G, start, goal)

    # Dictionary lưu trạng thái tốt nhất
    best_state = {}
    rounded_battery = round(start_node.battery, 2)
    best_state[(start_node.name, rounded_battery)] = start_node.g

    open_set = [start_node]  # Ưu tiên theo f = g + h
    heapq.heapify(open_set)

    while open_set:
        current_node = heapq.heappop(open_set)

        # Kiểm tra đích
        if current_node.name == goal:
            path = []
            while current_node:
                path.append((current_node.name, current_node.battery, (current_node.x, current_node.y)))
                current_node = current_node.parent
            return path[::-1]

        # Xử lý sạc tại trạm
        if current_node.name in charging_stations and current_node.battery < max_battery:
            charged_node = Node(
                name=current_node.name,
                parent=current_node.parent,
                g=current_node.g,
                h=current_node.h,  # h giữ nguyên do cùng vị trí
                battery=max_battery,
                x=current_node.x,
                y=current_node.y
            )
            rounded_battery = round(charged_node.battery, 2)
            state_key = (charged_node.name, rounded_battery)

            if state_key not in best_state or best_state[state_key] > charged_node.g:
                best_state[state_key] = charged_node.g
                heapq.heappush(open_set, charged_node)

        # Duyệt các node kế tiếp
        for neighbor in G.neighbors(current_node.name):
            edge_data = G[current_node.name][neighbor][0]
            distance = edge_data.get('length', 1.0)
            battery_needed = distance * consumption_rate

            if current_node.battery < battery_needed:
                continue

            new_battery = current_node.battery - battery_needed
            new_g = current_node.g + distance
            nx, ny = G.nodes[neighbor]['x'], G.nodes[neighbor]['y']
            new_h = euclidean_distance(G, neighbor, goal)

            neighbor_node = Node(
                name=neighbor,
                parent=current_node,
                g=new_g,
                h=new_h,
                battery=new_battery,
                x=nx,
                y=ny
            )

            rounded_battery = round(neighbor_node.battery, 2)
            state_key = (neighbor_node.name, rounded_battery)

            if state_key not in best_state or best_state[state_key] > neighbor_node.g:
                best_state[state_key] = neighbor_node.g
                heapq.heappush(open_set, neighbor_node)

    return None