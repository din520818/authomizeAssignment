"""
Author: Dinesh Bhusal
Date: 20th jan, 2023
Notes: Authomize assignment
"""
import os
import sys
import json
from typing import List, Tuple
script_root_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(script_root_path)
from graphUtils.graphUtils import Graph


def getPermissionsJsonList(permissionsJsonLFile: str) -> [int, List]:
    """
    :param permissionsJsonLFile: jsonL file location of GCP permissions policy
    :return: -response code of function
             -List of permissions json
    :Remarks: update this function only if you want to get data from other sources
    """
    permissionsJsonList = []
    if os.path.exists(permissionsJsonLFile):
        with open(permissionsJsonLFile, 'r') as permissionsJsonLContents:
            for jsonLine in permissionsJsonLContents:
                permissionsJson = json.loads(jsonLine)
                permissionsJsonList.append(permissionsJson)
        return 0, permissionsJsonList
    else:
        print(f"Permissions JSON lines file doesn't exist.\nPlease verify at '{permissionsJsonLFile}'")
        return 1, permissionsJsonList


def buildPermissionsGraph(permissionsJsonList: List) -> Graph:
    """
    :param permissionsJsonLFile: jsonL file location of GCP permissions policy
    :return: -Graph object with nodes and edges
    """

    graphObj = Graph()
    for permissionsJson in permissionsJsonList:
        resourceId = permissionsJson['name'].split("//cloudresourcemanager.googleapis.com/")[1]
        resourceType = permissionsJson['asset_type'].split("cloudresourcemanager.googleapis.com/")[1]
        resourceNode = graphObj.add_node(resourceId, resourceType)

        # create edges for resource -> parent resource
        # add edges for ancestor-child relationships
        for ancestorIndexCount in range(len(permissionsJson["ancestors"])-1):
            parentResourceId = permissionsJson["ancestors"][ancestorIndexCount + 1]
            parentResourceType = resourceType
            parentNode = graphObj.add_node(parentResourceId, parentResourceType)
            childResourceId = permissionsJson["ancestors"][ancestorIndexCount]
            childResourceType = resourceType
            childNode = graphObj.add_node(childResourceId, childResourceType)
            graphObj.add_edge(childNode, parentNode, "is-child-of")

        # create edges for resource -> identity with role
        for binding in permissionsJson['iam_policy']['bindings']:
            role = binding['roles']
            for member in binding['members']:
                identity_node = graphObj.add_node(member, "identity")
                graphObj.add_edge(identity_node, resourceNode, role)
    return graphObj


def getPermissionsTree(graphObj: Graph) -> None:
    """
    :param graphObj: Graph object with nodes and edges
    :return: None
    Remarks: Prints all the relationships between nodes
    """
    print("\nAll the relationships in the graph are:\n")
    for edge in graphObj.edges:
        fromNode = edge.from_node
        fromNodeId = fromNode._id
        toNode = edge.to_node
        toNodeId = toNode._id
        type = edge._type
        print(f"{fromNodeId}-{fromNode._type}----{type}-----{toNodeId}-{toNode._type}")
    print("-"*10)


def getResourceHierarchy(graph: Graph, resource_id: str) -> List[str]:
    """
    :param graph: Graph object with nodes and edges
    :param resource_id: Resource identifier
    :return: list of ancestors in the hierarchy
    """
    # DFS
    resourceNode = None
    resourceType = resource_id.split("/")[0].capitalize()
    for node in graph.nodes:
        if node._id == resource_id and node._type == resourceType:
            resourceNode = node
            break
    if resourceNode is None:
        return []

    ancestors = []
    stack = [resourceNode]
    while stack:
        current = stack.pop()
        for edge in graph.edges:
            if edge.from_node == current and edge._type == 'is-child-of':
                parent = edge.to_node
                ancestors.append(parent._id)
                stack.append(parent)
    return ancestors


def get_identity_permissions(graph: Graph, identity_id: str) -> List[Tuple[str, str, str]]:
    permissions = []
    queue = []
    visited = set()
    # find the identity node
    identityNode = next(node for node in graph.nodes
                        if node._id.split(":")[-1] == identity_id and node._type == 'identity')
    print(identityNode._id)
    queue.append(identityNode)
    visited.add(identityNode)
    while queue:
        current_node = queue.pop(0)
        for edge in graph.edges:
            if edge.from_node == current_node and "roles/" in edge._type and edge.to_node not in visited:
                resourceName = edge.to_node._id
                resourceType = edge.to_node._type
                role = edge._type.split("/")[-1]
                permissions.append((resourceName, resourceType, role))
                queue.append(edge.to_node)
                visited.add(edge.to_node)
    return permissions


def authomizeMain() -> int:
    """
    :return: status code
    """
    try:
        # initialize the GCP permissions json lines file location
        permissionsJsonLFile = f"{script_root_path}/data/permissions.jsonl"
        # update the getPermissionsJsonList function if you want to get data from other sources
        getPermissionsStat, permissionsJsonList = getPermissionsJsonList(permissionsJsonLFile)
        if getPermissionsStat == 0:
            # Task 1
            permissionsGraph = buildPermissionsGraph(permissionsJsonList)
            getPermissionsTree(permissionsGraph)
            print(f"Graph generated: {permissionsGraph}")
            print("__Task 1 completed__")
            resourceId = "folders/6"
            resourceHierarchy = getResourceHierarchy(permissionsGraph, resourceId)
            print(f"resourceHierarchy of {resourceId} is {resourceHierarchy} ")
            print("__Task 2 completed__")
            userName = "ron@test.authomize.com"
            resourcePermissions = get_identity_permissions(permissionsGraph, userName)
            print(f"resourcePermissions of {userName} is {resourcePermissions} ")
            print("__Task 3 completed__")
            return 0
        else:
            return 1
    except KeyboardInterrupt:
        print("Flow interrupted by user.")
        return 1


if __name__ == "__main__":
    authomizeMain()
