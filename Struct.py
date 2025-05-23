import heapq
import math
from collections import defaultdict

#Trang Thai tai node
class Node:
    def __init__(self, name, parent=None, g=0, h=0, battery=100, x=None, y=None):
        self.name = name
        self.parent = parent
        self.g = g  
        self.h = h  
        self.battery = battery 
        self.x = x  # Tọa độ x
        self.y = y  # Tọa độ y
        
    def f(self):
        return self.g + self.h
    
    def __lt__(self, other):
        return self.f() < other.f()

#Do thi
class Graph:
    def __init__(self):
        self.edges = defaultdict(dict) 
        self.charging_stations = set() 
        self.coordinates = {}  
    
    def add_node(self, name, x, y):
        self.coordinates[name] = (x, y)
    
    def add_edge(self, node1, node2, actual_distance):
        self.edges[node1][node2] = actual_distance
        self.edges[node2][node1] = actual_distance
    
    def add_charging_station(self, node):
        self.charging_stations.add(node)
    
    def euclidean_distance(self, node1, node2):
        x1, y1 = self.coordinates[node1]
        x2, y2 = self.coordinates[node2]
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)