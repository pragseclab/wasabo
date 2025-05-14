"""
Basic skeleton of a mitmproxy addon.

Run as follows: mitmproxy -s anatomy.py
"""
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from mitmproxy import http
import requests
import logging
import json
import sys
import re

class FileTree:
    def __init__(self, value):
        self.value = value
        self.parent = None
        self.children = []
        # self.pt = PrettyPrintTree(lambda x: x.children, lambda x: x.value)

    def add_child(self, child):
        self.children.append(child)
        child.parent = self
        return child

    # def print_tree(self, horizontal=True):
    #     pt = PrettyPrintTree(lambda x: x.children, lambda x: x.value)
    #     pt(self, orientation=PrettyPrintTree.HORIZONTAL if horizontal else None)

    # Return string representation of tree from current node
    # Note: Currently only for a branch (i.e., a tree with one path)
    # TODO: Return a list of paths from current node if there are any points with multiple children
    def to_string(self):
        nodes = [self]
        pointer = self

        while(len(pointer.children) > 0):
            pointer = pointer.children[0]
            nodes.append(pointer)

        path = "/".join([node.value for node in nodes])
        return path[1:] if path.startswith("//") else path

    # Print the file path from the root to the current node
    def get_current_path(self):
        nodes = []
        pointer = self

        while(pointer.parent):
            nodes.append(pointer)
            pointer = pointer.parent

        return "/".join(reversed([node.value for node in nodes]))

    def get_level_n_nodes(self, level):
        if(level == 0):
            return [self]
        else:
            return [node for child in self.children for node in child.get_level_n_nodes(level-1)]

    # Get the max depth of the current tree
    def get_depth(self):
        if(self.children == []):
            return 1
        return 1 + max([child.get_depth() for child in self.children])

    # Flatten object into JSON-serializable form
    def flatten(self):
        return {
            "value" : self.value,
            "children" : [child.flatten() for child in self.children]
        }

    # Convert dictionary to FileTree type
    @classmethod
    def from_dictionary(cls, d):
        obj = cls(d["value"])
        for child in d["children"]:
            obj.add_child(cls.from_dictionary(child))

        return obj

    # Load in a file containing a serialized tree and load it
    @classmethod
    def from_file(filename):
        return FileTree.from_dictionary(json.load(open(filename)))

    # Dump tree to file
    def to_file(self, filename):
        print(json.dump(self.flatten(), open(filename, "w")))

def tree_contains_branch(tree, branch):
    while(branch.children != []):
        current_tree_node_children = [child.value for child in tree.children]

        if(branch.value != tree.value):
            return False
        elif(branch.children[0].value not in current_tree_node_children):
            return False

        branch = branch.children[0]
        tree = tree.children[current_tree_node_children.index(branch.value)]
    return True

# Takes as input a tree and a branch, returns the sub-branch that exists in the
# tree, or None if no nodes match beyond the root
def largest_present_subbranch(tree, branch):
    branch_pointer = branch

    while(branch_pointer.children != []):
        current_tree_node_children = [child.value for child in tree.children]

        if(branch_pointer.value != tree.value):
            break
        elif(branch_pointer.children[0].value not in current_tree_node_children):
            break

        branch_pointer = branch_pointer.children[0]
        tree = tree.children[current_tree_node_children.index(branch_pointer.value)]

    branch_pointer.children = []
    return branch

# Merge a URL branch into the tree using one of a few strategies
def merge_new_path(tree, branch):
    pass

# Append tree2 to lowest-most node of tree1 and return new tree1
# tree1 is a full filepath tree, potentially with multiple children for any given node
# tree2 is a single branch tree representing a new file path
def merge_trees(tree1, tree2) -> FileTree:
    tree1_current_node = tree1
    tree2_current_node = tree2

    # Loop through all elements of tree2 until a match can no longer be found at level n
    # Then, add the remanining nodes at that element of tree1
    while(True):
        # Get the value of all children of tree2
        tree1_children = [node.value for node in tree1_current_node.children]

        # We reached a leaf node (resource file). By this point, the paths match so we should not continue
        if(tree2_current_node.children == []):
            break

        # Get children of current node in tree1 and check if tree2 is in there
        if(tree2_current_node.children[0].value not in tree1_children):
            tree1_current_node.add_child(tree2_current_node.children[0])
            break

        # Move to next node of tree2
        tree1_current_node = tree1_current_node.children[tree1_children.index(tree2_current_node.children[0].value)]
        tree2_current_node = tree2_current_node.children[0]

    return tree1

# Parse URL and return tree branch for path, else None if URL doesn't have path
def get_tree_from_url(url:str) -> FileTree:
    # Parse out path from URL
    path = urlparse(url).path

    # Don't care about URLs that don't have file paths
    if(path == "" or path == "/"):
        return None

    # Clean up path if it is a relative path (no URL)
    path = path.strip(".").strip("/")

    # Iterate through elements of the path and construct single-brach tree
    root = FileTree("/")
    current_tree_node = root
    for segment in path.split("/"):
        # Create FileTree node for current segment and append to current tree
        segment_node = FileTree(segment)
        current_tree_node = current_tree_node.add_child(segment_node)

    return root

# Given a list of resource URLs, construct tree of filesystem
def construct_webpage_tree(urls) -> FileTree:
    branches = []
    for url in urls:
        branch = get_tree_from_url(url)
        if(branch):
            branches.append(branch)

    if(len(branches) == 0):
        return None
    elif(len(branches) == 1):
        return branches[0]

    tree = branches[0]
    for branch in branches[1:]:
        try:
            tree = merge_trees(tree, branch)
        except Exception as e:
            print(branches)
            raise e

    return tree

# Given a tree and a branch to merge, search for a matching parent
# directory at level n. Essentially, try appending all top level sub
# strings up to level n to the given path and see if it exists.
# Returns paths to try with top-level subtrees prepended to given path
def branch_search_n(tree, branch, n=2):
    # First, get a list of all nodes at level n to see if we have a
    # matching branch in the tree already
    level_n_nodes = tree.get_level_n_nodes(n)

    branches = []

    # First check if the desired branch has a first-level node matching
    # one of the found at level n of the tree
    for node in level_n_nodes:
        if(branch.children[0].value == node.value):
            branches.append([node.parent.get_current_path() + branch.to_string()])

    return branches

def http_get(url):
    response = requests.get(url,
                            headers={"User-Agent" :
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15"})
    return (response.status_code, response.headers, response.content)

# Get all of the URLs from a given web address
def get_webpage_urls(url):
    domain = urlparse(url).hostname
    status_code, headers, content = http_get(url)
    soup = BeautifulSoup(content, "html.parser")

    urls = []
    for tag in soup.find_all():
        if("href" in tag.attrs):
            urls.append(tag["href"])
        elif("src" in tag.attrs):
            urls.append(tag["src"])

    urls = [url.split("?")[0] for url in urls if not url.startswith("mailto")]
    urls = [url for url in urls if (domain in url or not url.startswith(("http")))]
    urls = [url for url in urls if "." in url.split("/")[-1]]

    return urls

class WebPathPredictor:
    def __init__(self):
        self.trees = {}

    def remove_comments(self, string):
        try:
            pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
            # first group captures quoted strings (double or single)
            # second group captures comments (//single-line or /* multi-line */)
            regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
            def _replacer(match):
                # if the 2nd group (capturing comments) is not None,
                # it means we have captured a non-quoted (real) comment string.
                if match.group(2) is not None:
                    return "" # so we will return empty to remove the comment
                else: # otherwise, we will return the 1st group
                    return match.group(1) # captured quoted-string
            return regex.sub(_replacer, string.decode()).encode()
        except:
            return string

    def remove_whitespace(self, data):
         try:
             new_data = "".join(data.decode("utf-8").split()).encode()
         except Exception as e:
             logging.error(e)
             return data
         return new_data

    # def response(self, flow):
    #     flow.response.content = self.remove_whitespace(self.remove_comments(flow.response.content))

    # def response(self, flow):
    #     pass

    def request(self, flow):
        domain = urlparse(flow.request.pretty_url).hostname

        logging.error(f"Got request for {domain}")

        # First make a request for the given URL and return the value if it exists
        status_code, headers, content = http_get(flow.request.pretty_url)
        flow.response = http.Response.make(
                status_code,
                content,
        )

        # for key, value in headers.items():
        #     flow.response.headers[key] = value

        if(status_code == 200):
            logging.error(f"Pre-change: {flow.request.pretty_url}: {flow.response.content[:100]}")
            flow.response.content = self.remove_whitespace(self.remove_comments(flow.response.content))
            logging.error(f"Post-change: {flow.request.pretty_url}: {flow.response.content[:100]}")
            return

        # If we haven't seen this domain yet, create a URL tree of the homepage
        if(domain not in self.trees):
            urls = get_webpage_urls(f"http://{domain}")
            self.trees[domain] = construct_webpage_tree(urls)

        # Get the homepage URL tree for the domain
        tree = self.trees[domain]

        branch = get_tree_from_url(flow.request.pretty_url)
        paths = branch_search_n(tree, branch)

        if(len(paths) > 0):
            logging.error(f"Found alternative paths for {flow.request.pretty_url}: {paths}")

        # For each potential path, see if that path exists and if so, return that content
        for path in paths:
            path = path[0]
            current_url = f"http://{domain}/{path}"
            status_code, headers, content = http_get(current_url)
            if(status_code == 200):
                tree = merge_trees(tree, get_tree_from_url(path))

                flow.response = http.Response.make(
                        status_code,
                        content,
                )

                # for key, value in headers.items():
                #     flow.response.headers[key] = value
                break
            else:
                logging.error(f"{current_url} status_code={status_code}")

        self.trees[domain] = tree

        flow.response.content = self.remove_whitespace(self.remove_comments(flow.response.content))

addons = [WebPathPredictor()]
