def uniform_cost_search(graph, start, goal, max_battery=100, consumption_rate=1):

    
    open_set = []
    closed_set = set()
    
    start_x, start_y = graph.coordinates[start]
    start_node = Node(start, g=0, battery=max_battery, x=start_x, y=start_y)
    heapq.heappush(open_set, (start_node.g, start_node))
    
    while open_set:
        current_cost, current_node = heapq.heappop(open_set)
        
        if current_node.name == goal:
            path = []
            while current_node:
                path.append((current_node.name, current_node.battery, (current_node.x, current_node.y)))
                current_node = current_node.parent
            return path[::-1]
        
        if current_node.name in closed_set:
            continue
            
        closed_set.add(current_node.name)
        
        for neighbor, actual_distance in graph.edges[current_node.name].items():
            if neighbor in closed_set:
                continue
            
            neighbor_x, neighbor_y = graph.coordinates[neighbor]
            
            battery_consumed = actual_distance * consumption_rate
            new_battery = current_node.battery - battery_consumed
            
            if new_battery < 0:
                if current_node.name in graph.charging_stations:
                    new_battery = max_battery
                    battery_consumed = 0
                    new_battery = max_battery - actual_distance * consumption_rate
                else:
                    continue
            
            new_g = current_node.g + actual_distance
            
            neighbor_node = Node(
                name=neighbor,
                parent=current_node,
                g=new_g,
                battery=new_battery,
                x=neighbor_x,
                y=neighbor_y
            )
            
            heapq.heappush(open_set, (new_g, neighbor_node))
    
    return None