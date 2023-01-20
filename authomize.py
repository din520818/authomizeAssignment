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
from graphUtils.graphUtils import Graph


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
        resourceId = permissionsJson['name']
        resourceType = permissionsJson['asset_type']
        resourceNode = graphObj.add_node(resourceId, resourceType)

        # create edges for resource -> parent resource
        for ancestor in permissionsJson['ancestors']:
            parentResourceNode = graphObj.add_node(ancestor, "resource")
            graphObj.add_edge(resourceNode, parentResourceNode, "is_child_of")

        # create edges for resource -> identity with role
        for binding in permissionsJson['iam_policy']['bindings']:
            role = binding['roles']
            for member in binding['members']:
                identity_node = graphObj.add_node(member, "identity")
                graphObj.add_edge(resourceNode, identity_node, role)
    return graphObj


def getResourceHierarchy(graph: Graph, resource_id: str):
    # DFS
    resource = None
    for node in graph.nodes:
        if node.id == resource_id and node.type == 'resource':
            resource = node
            break
    if resource is None:
        return None

    ancestors = [resource.id]
    stack = [resource]
    while stack:
        current = stack.pop()
        for edge in graph.edges:
            if edge.to_node == current and edge.type == 'parent':
                parent = edge.from_node
                ancestors.append(parent.id)
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
        print("Permissions JSON list: {}".format(permissionsJsonList))
        if getPermissionsStat == 0:
            permissionsGraph = buildPermissionsGraph(permissionsJsonList)
            print(get_user_permissions(permissionsGraph, "user:ron@test.authomize.com"))
            return 0
        else:
            return 1
    except KeyboardInterrupt:
        print("Flow interrupted by user.")
        return 1


if __name__ == "__main__":
    print("Authomize assignment main")
    authomizeMain()
