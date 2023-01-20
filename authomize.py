"""
Author: Dinesh Bhusal
Date: 20th jan, 2023
Notes: Authomize assignment
"""
import os
import sys
import json
script_root_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(script_root_path)
from graphUtils.graphUtils import Graph, Node, Edge


def getPermissionsJsonList(permissionsJsonLFile: str):
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


def buildPermissionsGraph(permissionsJsonList):
    graphObj = Graph()
    for permissionsJson in permissionsJsonList:
        resourceId = permissionsJson['name'].split("//cloudresourcemanager.googleapis.com/")[1]
        resourceType = permissionsJson['asset_type'].split("cloudresourcemanager.googleapis.com/")[1].lower()
        resourceNode = graphObj.add_node(resourceId, resourceType)

        # create edges for resource -> parent resource
        # add edges for ancestor-child relationships
        for ancestorIndexCount in range(len(permissionsJson["ancestors"])-1):
            parentResourceId = permissionsJson["ancestors"][ancestorIndexCount + 1]
            parentResourceType = parentResourceId.split("/")[0]
            parentNode = graphObj.add_node(parentResourceId, parentResourceType)
            childResourceId = permissionsJson["ancestors"][ancestorIndexCount]
            childResourceType = childResourceId.split("/")[0]
            childNode = graphObj.add_node(childResourceId, childResourceType)
            graphObj.add_edge(childNode, parentNode, "is-child-of")

        # create edges for resource -> identity with role
        for binding in permissionsJson['iam_policy']['bindings']:
            role = binding['roles']
            for member in binding['members']:
                identity_node = graphObj.add_node(member, "identity")
                graphObj.add_edge(resourceNode, identity_node, role)
    return graphObj


def getPermissionsTree(graphObj):
    for edge in graphObj.edges:
        fromNode = edge.from_node
        fromNodeId = fromNode._id
        fromNodeType = fromNode._type

        toNode = edge.to_node
        toNodeId = toNode._id
        toNodeType = toNode._type

        type = edge._type
        print(f"{fromNodeId}----{type}-----{toNodeId}")


def getResourceHierarchy(graph: Graph, resource_id: str):
    # DFS
    resourceNode = None
    resourceType = resource_id.split("/")[0]
    for node in graph.nodes:
        if node._id == resource_id and node._type == resourceType:
            resourceNode = node
            break
    if resourceNode is None:
        return None

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


def get_user_permissions(graph: Graph, user_email: str):
    output = []
    for edge in graph.edges:
        for binding in edge.from_node.iam_policy["bindings"]:
            if user_email in binding["members"]:
                resource_name = edge.from_node.name
                resource_type = edge.from_node.asset_type
                role = binding["roles"]
                output.append((resource_name, resource_type, role))
    return output


def authomizeMain():
    try:
        # initialize the GCP permissions json lines file location
        permissionsJsonLFile = f"{script_root_path}/data/permissions.jsonl"
        # update the getPermissionsJsonList function if you want to get data from other sources
        getPermissionsStat, permissionsJsonList = getPermissionsJsonList(permissionsJsonLFile)
        if getPermissionsStat == 0:
            # Task 1
            permissionsGraph = buildPermissionsGraph(permissionsJsonList)
            #getPermissionsTree(permissionsGraph)
            print(f"Graph generated: {permissionsGraph}")
            print("__Task 1 completed__")
            resourceName = "folders/6"
            resourceHierarchy = getResourceHierarchy(permissionsGraph, resourceName)
            print(f"resourceHierarchy of {resourceName} is {resourceHierarchy} ")
            print("__Task 2 completed__")
            return 0
        else:
            return 1
    except KeyboardInterrupt:
        print("Flow interrupted by user.")
        return 1


if __name__ == "__main__":
    authomizeMain()
