from prettytable import PrettyTable


class Node:
    def __init__(self, _id: str, _type: str):
        self._id = _id
        self._type = _type

    def __eq__(self, newNode):
        if not isinstance(newNode, Node):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return self._id == newNode._id and self._type == newNode._type

    def __hash__(self):
        # return a unique hash value for each instance of the class
        return hash(f"{self._id}-{self._type}")


class Edge:
    def __init__(self, from_node: Node, to_node: Node, _type: str):
        self.from_node = from_node
        self.to_node = to_node
        self._type = _type

    def __eq__(self, newEdge):
        if not isinstance(newEdge, Edge):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return self.from_node == newEdge.from_node and self.to_node == newEdge.to_node and self._type == newEdge._type

    def __hash__(self):
        # return a unique hash value for each instance of the class
        return hash(f"{self.from_node}-{self._type}-{self.to_node}")


class Graph:
    def __init__(self):
        self.edges = []
        self.nodes = []

    def __eq__(self, newGraph):
        if not isinstance(newGraph, Graph):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return len(self.edges) == len(newGraph.edges) and all(edg in self.edges for edg in newGraph.edges) and\
               len(self.nodes) == len(newGraph.nodes) and all(nod in self.nodes for nod in newGraph.nodes)

    def print_graph(self):
        # Create a new table
        table = PrettyTable()
        # Add the headers
        table.field_names = ["From Node", "Relationship", "To Node"]
        for edge in self.edges:
            fromNode = edge.from_node
            fromNodeId = fromNode._id
            toNode = edge.to_node
            toNodeId = toNode._id
            type = edge._type
            table.add_row([f"{fromNodeId}-{fromNode._type}", f"{type}", f"{toNodeId}-{toNode._type}"])
        # Print the table
        print(table)

    def add_node(self, _id, _type):
        node = Node(_id, _type)
        if node not in self.nodes:
            self.nodes.append(node)
        return node

    def add_edge(self, from_node, to_node, _type):
        new_edge = Edge(from_node, to_node, _type)
        if new_edge not in self.edges:
            self.edges.append(new_edge)
        return new_edge

    def remove_node(self, node: Node):
        if node in self.nodes:
            self.nodes.remove(node)
            # remove all edges that contain the node
            self.edges = [edge for edge in self.edges if edge.from_node != node and edge.to_node != node]

    def remove_edge(self, edge: Edge):
        if edge in self.edges:
            self.edges.remove(edge)

    def find_node(self, node_id: str):
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def find_edges_to_node(self, to_node_id: str):
        return [edg for edg in self.edges if edg.to_node._id == to_node_id]
