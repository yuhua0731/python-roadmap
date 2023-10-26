import networkx as nx
from typing import NamedTuple
from queues import Queue, Stack
# from collections import deque

# define a class to store the City information
# City is a node in the graph
class City(NamedTuple):
    name: str
    country: str
    year: int | None
    latitude: float
    longitude: float

    @classmethod
    def from_dict(cls, attrs):
        return cls(
            name=attrs["xlabel"],
            country=attrs["country"],
            year=int(attrs["year"]) or None, # If the conversion is successful, it will store the integer value in year; otherwise, it will assign None.
            latitude=float(attrs["latitude"]),
            longitude=float(attrs["longitude"]),
        )
    
    # __str__ is used to print the object in a human-readable format, if not overriden, it will use the superclass's __str__ method
    # def __str__(self) -> str:
    #     return "bazinga"
    
    # __repr__ is used to print the object, if not overriden, it will use the superclass's __repr__ method
    # by default, __repr__ will print the object's memory address
    def __repr__(self) -> str:
        return f"City: {self.name} ({self.country})\nYear: {self.year}\nPosition: {self.latitude}, {self.longitude}"

# input: a file name in dot format | return: a graph
get_graph_from_dot = lambda file_name: nx.nx_agraph.read_dot(file_name)
graph = get_graph_from_dot("roadmap.dot")

# input: a graph node | return: a City object
create_city_from_graph_node = lambda node: City.from_dict(node)
london = create_city_from_graph_node(graph.nodes['london'])

def create_cities_from_graph(graph, node_factory=create_city_from_graph_node):
    return {
        name: node_factory(attributes)
        for name, attributes in graph.nodes(data=True)
    }

nodes = create_cities_from_graph(graph)
print(nodes['london'])

def load_graph(file_name, node_factory):
    """ The function takes a filename and a callable factory for the node objects, 
        such as your City.from_dict() class method.

    Args:
        file_name (str): a filename, format is .dot
        node_factory (callable factory): a callable factory for the node objects

    Returns:
        dict, Graph: a mapping of nodes and a new graph comprising nodes and weighted edges
    """
    graph = nx.nx_agraph.read_dot(file_name)
    # <class 'dict'> 
    nodes = {
        name: node_factory(attributes)
        for name, attributes in graph.nodes(data=True)
    }
    # <class 'networkx.classes.graph.Graph'>
    return nodes, nx.Graph(
        (nodes[name1], nodes[name2], weights)
        for name1, name2, weights in graph.edges(data=True)
    )

nodes, network = load_graph("roadmap.dot", City.from_dict)
print(network)

get_neighbors_of_node = lambda network, node: network.neighbors(node)
print([i.name for i in get_neighbors_of_node(network, nodes['london'])])

def get_neighbors_and_distance_of_node(network, node):
    
    def sort_by(items, strategy):
        return sorted(items, key=lambda x: strategy(x[1]))

    def by_distance(item):
        return int(item["distance"])

    return [[weights["distance"], neighbor.name] for neighbor, weights in sort_by(network[node].items(), by_distance)]

print(get_neighbors_and_distance_of_node(network, nodes['london']))

def traverse_network_bfs(network, root):
    q = Queue(root)
    visited = {root}
    while q:
        yield (node := q.dequeue())
        # equivalent to:
        # node = q.dequeue()
        # yield node
        neighbors = get_neighbors_of_node(network, node)
        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                q.enqueue(neighbor)

is_twentieth_century = lambda year: year and 1901 <= year <= 2000

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

# even with bfs, the search order can vary a lot depends on the order you traverse the neighbors
# networkx provide a key arg "sort_neighbors", allowing you to define the order of the neighbors
def order(neighbors):
    by_latitude = lambda city: city.latitude
    return iter(sorted(neighbors, key=by_latitude, reverse=True))

built_in_bfs_sort_neighbors = []
for node in nx.bfs_tree(network, nodes["edinburgh"], sort_neighbors=order):
    built_in_bfs_sort_neighbors.append(node.name)

assert built_in_bfs_sort_neighbors != built_in_bfs, "The implementation is wrong"
print("🎉🎉🎉🎉🎉🎉🎉🎉🎉 BFS with sorted neighbors")

def traverse_network_dfs(network, root):
    """
    创建neighbors的iterator并存放在stack中，每次访问是使用next()方法获取下一个neighbor
    如果没有下一个neighbor，就从stack中移除该node
    使用该方式可以节省首次调用的时间，当外部调用需要获取下一个node时，函数内部才会遍历到下一个
    """
    q = Stack((root, iter(get_neighbors_of_node(network, root))))
    visited = {root}
    yield root
    while q:
        _, neighbors = q.peak() # get the peak element, while do not removing it
        try:
            nxt = next(neighbors)
            if nxt not in visited:
                yield nxt
                visited.add(nxt)
                q.enqueue((nxt, iter(get_neighbors_of_node(network, nxt))))
        except StopIteration:
            q.dequeue() # once neighbors are fully iterated, remove the element from the stack

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
