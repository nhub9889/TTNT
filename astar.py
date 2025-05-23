def a_star(graph, start, goal, max_battery=100, consumption_rate=1):

    open_set = []
    closed_set = set()
    
    start_x, start_y = graph.coordinates[start]
    start_node = Node(start, battery=max_battery, x=start_x, y=start_y)
    start_node.h = graph.euclidean_distance(start, goal)
    heapq.heappush(open_set, start_node)
    
    while open_set:
        current_node = heapq.heappop(open_set)
        
        if current_node.name == goal:
            path = []
            while current_node:
                path.append((current_node.name, current_node.battery, (current_node.x, current_node.y)))
                current_node = current_node.parent
            return path[::-1] 
        closed_set.add(current_node.name)
        
     
        for neighbor, actual_distance in graph.edges[current_node.name].items():
            if neighbor in closed_set:
                continue
            
            neighbor_x, neighbor_y = graph.coordinates[neighbor]
            
            battery_consumed = actual_distance * consumption_rate
            new_battery = current_node.battery - battery_consumed
            
            if new_battery < 0:
                if current_node.name in graph.charging_stations:
                    new_battery = max_battery  # Nạp đầy pin
                    battery_consumed = 0  # Reset sau khi nạp
                    new_battery = max_battery - actual_distance * consumption_rate
                else:
                    continue  

            new_g = current_node.g + actual_distance
            new_h = graph.euclidean_distance(neighbor, goal)
            
            neighbor_node = Node(
                name=neighbor,
                parent=current_node,
                g=new_g,
                h=new_h,
                battery=new_battery,
                x=neighbor_x,
                y=neighbor_y
            )
            

            heapq.heappush(open_set, neighbor_node)
    
    return None 