import networkx as nx
from yuhua_graph_test import *

graph = get_graph_from_dot("roadmap.dot")
london = create_city_from_graph_node(graph.nodes['london'])

nodes = create_cities_from_graph(graph)
print(nodes['london'])

nodes, network = load_graph("roadmap.dot", City.from_dict)
print(network)

print([i.name for i in get_neighbors_of_node(network, nodes['london'])])
print(get_neighbors_and_distance_of_node(network, nodes['london']))

# 检验编写的BFS是否正确，与networkx自带的BFS进行比较
self_implementation = []
for node in traverse_network_bfs(network, nodes["edinburgh"]):
    # print("📍", node.name)
    self_implementation.append(node.name)

built_in_bfs = []
for node in nx.bfs_tree(network, nodes["edinburgh"]):
    # print("📍", node.name)
    built_in_bfs.append(node.name)

assert self_implementation == built_in_bfs, "The implementation is wrong"
print("🎉🎉🎉🎉🎉🎉🎉🎉🎉 BFS")

# networkx提供了一个sort_neighbors参数，可以用于定义neighbors的顺序
built_in_bfs_sort_neighbors = []
for node in nx.bfs_tree(network, nodes["edinburgh"], sort_neighbors=order):
    built_in_bfs_sort_neighbors.append(node.name)

assert built_in_bfs_sort_neighbors != built_in_bfs, "The implementation is wrong"
print("🎉🎉🎉🎉🎉🎉🎉🎉🎉 BFS with sorted neighbors")

# 检验编写的DFS是否正确，与networkx自带的DFS进行比较
self_implementation = []
for node in traverse_network_dfs(network, nodes["edinburgh"]):
    # print("📍", node.name)
    self_implementation.append(node.name)

built_in_dfs = []
for node in nx.dfs_tree(network, nodes["edinburgh"]):
    # print("📍", node.name)
    built_in_dfs.append(node.name)

assert self_implementation == built_in_dfs, "The implementation is wrong"
print("🎉🎉🎉🎉🎉🎉🎉🎉🎉 DFS")

# 检验编写的shortest_paths是否正确，与networkx自带的all_shortest_paths进行比较
city1 = nodes["aberdeen"]
city2 = nodes["perth"]

for i, path in enumerate(nx.all_shortest_paths(network, city1, city2), 1):
    print(f"{i}.", " → ".join(city.name for city in path))

self_implementation = " → ".join([i.name for i in shortest_path(network, city1, city2)])
built_in_shortest_paths = " → ".join([i.name for i in nx.shortest_path(network, city1, city2)])
assert self_implementation == built_in_shortest_paths, "The implementation is wrong"
print("🎉🎉🎉🎉🎉🎉🎉🎉🎉 the shortest path")