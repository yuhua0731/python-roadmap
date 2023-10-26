import networkx as nx
from typing import NamedTuple
from queues import Queue, Stack
from collections import deque

# define a class to store the City information
# City is a node in the graph
# 自定义节点类，用于存储城市信息，使用NamedTuple作为基类，可以保证实例化后的对象是不可变的
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
# 输入一个dot文件，返回一个graph
get_graph_from_dot = lambda file_name: nx.nx_agraph.read_dot(file_name)

# input: a graph, a node | return: a list of neighbors of the node
# 输入一个graph和一个node，返回一个list，包含该node的所有neighbors
get_neighbors_of_node = lambda network, node: network.neighbors(node)

# input: a graph node | return: a City object
# 输入一个graph node，返回一个City对象
create_city_from_graph_node = lambda node: City.from_dict(node)

# input: a graph | return: a dict, key is the node name, value is the corresponding City object
# 输入一个graph，返回一个dict，key为节点名称，value为对应的City对象
def create_cities_from_graph(graph, node_factory=create_city_from_graph_node) -> dict:
    """ 获取graph中的所有节点并通过指定的node_factory创建对应的对象，以dict的形式返回

    Args:
        graph (nx graph): 由networkx读取的graph
        node_factory (callable function, optional): 可以为自定义的方法，用于将graph中的节点转换成自定义类的对象. Defaults to create_city_from_graph_node.

    Returns:
        dict: key为节点名称，value为对应的对象
    """
    return {
        name: node_factory(attributes)
        for name, attributes in graph.nodes(data=True)
    }

# 整合上述两个方法，输入一个dot文件
# 返回一个dict，key为节点名称，value为对应的对象
# 额外返回一个nx.Graph，包含节点和加权边
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

# input: a graph, a node | return: a list of neighbors of the node and the distance between them, sorted by distance
# 输入一个graph和一个node，返回一个list，包含该node的所有neighbors和距离，且按照距离排序
def get_neighbors_and_distance_of_node(network, node):
    
    def sort_by(items, strategy):
        return sorted(items, key=lambda x: strategy(x[1]))

    def by_distance(item):
        return int(item["distance"])

    return [[weights["distance"], neighbor.name] for neighbor, weights in sort_by(network[node].items(), by_distance)]

# even with bfs, the search order can vary a lot depends on the order you traverse the neighbors
# networkx provide a key arg "sort_neighbors", allowing you to define the order of the neighbors
def order(neighbors):
    by_latitude = lambda city: city.latitude
    return iter(sorted(neighbors, key=by_latitude, reverse=True))

# 输入一个graph和一个起始节点，返回一个生成器，以BFS顺序遍历所有节点
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

# 输入一个graph和一个起始节点，返回一个生成器，以DFS顺序遍历所有节点
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

def retrace(previous, source, destination):
    path = deque()

    current = destination
    while current != source:
        path.appendleft(current)
        current = previous.get(current)
        if current is None:
            return None

    path.appendleft(source)
    return list(path)

# 输入一个graph、起始节点、和目标节点，返回一个list，包含从起始节点到目标节点的最短路径
def shortest_path(network, source, destination, order_by=None):
    """search the shortest path between two nodes in a graph, if there are multiple shortest paths, return the first one

    Args:
        network (networkx Graph): a graph
        start (_type_): start node
        end (_type_): end node
        order_by (_type_, optional): Defaults to None.
    """
    queue = Queue(source)
    visited = {source}
    previous = {} # used for retrace
    while queue:
        node = queue.dequeue()
        neighbors = get_neighbors_of_node(network, node)
        if order_by:
            neighbors.sort(key=order_by)
        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.enqueue(neighbor)
                previous[neighbor] = node
                if neighbor == destination:
                    return retrace(previous, source, destination)
    return []