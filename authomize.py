"""
Author: Dinesh Bhusal
Date: 20th jan, 2023
Notes: Authomize assignment
"""
import os
import sys
import json
from typing import List, Tuple, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

script_root_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(script_root_path)
from graphWeb.graphWeb import Graph


def getPermissionsJsonList(permissionsJsonLFile: str) -> tuple[int, list[Any]]:
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


def getResourceAncestors(graph: Graph, resource_id: str) -> List[str]:
    """
    :param graph: Graph object with nodes and edges
    :param resource_id: Resource identifier
    :return: list of ancestors in the hierarchy
    """
    # DFS
    resourceNode = None
    for node in graph.nodes:
        if node._id == resource_id:
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


def getResourceChildren(graph: Graph, resource_id: str) -> List[str]:
    """
    :param graph: Graph object with nodes and edges
    :param resource_id: Resource identifier
    :return: list of children in the hierarchy
    """
    # DFS
    resourceNode = None
    for node in graph.nodes:
        if node._id == resource_id:
            resourceNode = node
            break
    if resourceNode is None:
        return []

    children = []
    stack = [resourceNode]
    while stack:
        current = stack.pop()
        for edge in graph.edges:
            if edge.to_node == current and edge._type == 'is-child-of':
                child = edge.from_node
                children.append(child._id)
                stack.append(child)
    return children


def get_identity_permissions(graph: Graph, identity_id: str) -> List[Tuple[str, str, str]]:
    """
    :param graph: Graph object with nodes and edges
    :param identity_id: user identifier
    :return: list of tuples of resource identifier, resource type and role as its items
    """
    permissions = []
    queue = []
    visited = set()

    # First, find all the resources that the identity has a direct role on
    for edge in graph.edges:
        if edge.from_node._id.split(":")[-1] == identity_id:
            queue.append(edge)
            visited.add(edge.to_node._id)

    # For each resource found, add its permissions to the final list
    while queue:
        edge = queue.pop(0)
        resource_id = edge.to_node._id
        resource_type = edge.to_node._type
        role = edge._type
        permissions.append((resource_id, resource_type, role))

        # Then, find all the children of the resource, and add them to the queue
        children = getResourceChildren(graph, resource_id)
        for child in children:
            if child not in visited:
                permissions.append((child, resource_type, role))
                visited.add(edge.to_node._id)
    return permissions


def get_resource_permissions(graph: Graph, resource_id: str) -> List[Tuple[str, str]]:
    """
    :param graph: Graph object with nodes and edges
    :param resource_id: Resource identifier
    :return: list of tuples of Identity name and Role as its items
    """
    permissions = []
    queue = []
    visited = set()

    # First, find all the resources that the identity has a direct role on
    for edge in graph.edges:
        if edge.to_node._id == resource_id and "roles" in edge._type:
            queue.append(edge)
            visited.add(edge.from_node._id)

    # For each resource found, add its permissions to the final list
    while queue:
        edge = queue.pop(0)
        if "roles" in edge._type:
            identityName = edge.from_node._id
            role = edge._type
            permissions.append((identityName, role))

            # Then, find all the ancestors of the resource, and add them to the queue
            parentList = getResourceAncestors(graph, resource_id)
            for parent in parentList:
                if parent not in visited:
                    parentEdges = graph.find_edges_to_node(to_node_id=parent)
                    queue.extend(parentEdges)
                    visited.add(parent)
    return list(set(permissions))


def get_users_from_google(credentialsFile: str) -> List:
    # use the service account json to connect to the Directory API
    credentials = Credentials.from_service_account_file(credentialsFile,
                    ['https://www.googleapis.com/auth/admin.directory.user'])
    directory_service = build('admin', 'directory_v1', credentials=credentials)

    users = directory_service.users().list(customer='my_customer', maxResults=500).execute()
    return users


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
            permissionsGraph.print_graph()
            print(f"Graph generated: {permissionsGraph}")
            print("__Task 1 completed__")

            # Task 2
            resourceId = "folders/7"
            resourceAncestors = getResourceAncestors(permissionsGraph, resourceId)
            print(f"resourceAncestors of {resourceId} is {resourceAncestors} ")
            resourceId = "folders/2"
            resourceChildren = getResourceChildren(permissionsGraph, resourceId)
            resourceId = "organizations/1"
            print(f"resourceChildren of {resourceId} is {resourceChildren} ")
            print("__Task 2 completed__")

            # Task 3
            userName = "dev-manager@striking-arbor-264209.iam.serviceaccount.com"
            identityPermissions = get_identity_permissions(permissionsGraph, userName)
            print(f"resourcePermissions of {userName} is {identityPermissions} ")
            print("__Task 3 completed__")

            # Task 4
            resourceId = "folders/7"
            resourcePermissions = get_resource_permissions(permissionsGraph, resourceId)
            print(f"resourcePermissions of {resourceId} is {resourcePermissions} ")
            print("__Task 4 completed__")

            # Task 5
            # todo update the google key file and get the users list and verify
            # todo QC
            # credentialsFile = f"{script_root_path}/data/credentials_key_file"
            # usersList = get_users_from_google(credentialsFile)
            # print(f"Users List from google are {resourcePermissions}")
            # print("__Task 5 completed__")

            # todo Task 6
            # Without the data from task 5 I cannot work on  task 6
            return 0
        else:
            return 1
    except KeyboardInterrupt:
        print("Flow interrupted by user.")
        return 1


if __name__ == "__main__":
    authomizeMain()
