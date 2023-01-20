class Node:
    def __init__(self, type: str, id: str):
        self.id = id
        self.type = type


class Edge:
    def __init__(self, from_node: Node, to_node: Node, type: str):
        self.from_node = from_node
        self.to_node = to_node
        self.type = type


class Graph:
    def __init__(self):
        self.edges = []
        self.nodes = []

    def add_node(self, _id, _type):
        node = Node(_id, _type)
        self.nodes.append(node)
        return node

    def add_edge(self, from_node, to_node, _type):
        edge = Edge(from_node, to_node, _type)
        self.edges.append(edge)
        return edge

    def remove_node(self, node: Node):
        self.nodes.remove(node)

    def remove_edge(self, edge: Edge):
        self.edges.remove(edge)
