#!/usr/bin/env python3
"""Build a hierarchical tree from all URLs and identify key pages to crawl."""

import json
from urllib.parse import urlparse
from collections import defaultdict

with open("data/all_urls.json") as f:
    all_urls = json.load(f)

print(f"Total URLs loaded: {len(all_urls)}")

# Parse URLs into path segments
def parse_url(url_str):
    parsed = urlparse(url_str)
    path = parsed.path.strip("/")
    if not path:
        return ["/"]
    return path.split("/")

# Build tree structure
def build_tree(urls):
    tree = {"name": "rudderstack.com", "path": "/", "children": {}, "urls": [], "count": 0}

    for url_obj in urls:
        url = url_obj["url"]
        segments = parse_url(url)

        if segments == ["/"]:
            tree["urls"].append(url_obj)
            tree["count"] += 1
            continue

        current = tree
        for i, seg in enumerate(segments):
            if seg not in current["children"]:
                partial_path = "/" + "/".join(segments[:i+1]) + "/"
                current["children"][seg] = {
                    "name": seg,
                    "path": partial_path,
                    "children": {},
                    "urls": [],
                    "count": 0,
                }
            current = current["children"][seg]

        current["urls"].append(url_obj)
        current["count"] += 1

    return tree

# Count total URLs under each node (including descendants)
def count_descendants(node):
    total = node["count"]
    for child in node["children"].values():
        total += count_descendants(child)
    node["total_count"] = total
    return total

# Convert tree to a serializable format
def tree_to_dict(node, depth=0):
    result = {
        "name": node["name"],
        "path": node["path"],
        "page_count": node["count"],
        "total_descendants": node.get("total_count", node["count"]),
        "depth": depth,
        "children": [],
    }
    # Include actual URLs for leaf nodes
    if node["urls"]:
        result["urls"] = [u["url"] for u in node["urls"]]

    for child_name in sorted(node["children"].keys()):
        child = node["children"][child_name]
        result["children"].append(tree_to_dict(child, depth + 1))

    return result

tree = build_tree(all_urls)
count_descendants(tree)
tree_dict = tree_to_dict(tree)

with open("data/hierarchy.json", "w") as f:
    json.dump(tree_dict, f, indent=2)

# Print summary of top-level sections
print("\n=== TOP-LEVEL SECTIONS ===")
for child in sorted(tree_dict["children"], key=lambda x: -x["total_descendants"]):
    print(f"  /{child['name']}/  ({child['total_descendants']} pages)")
    if child["children"]:
        for sub in sorted(child["children"], key=lambda x: -x["total_descendants"])[:5]:
            print(f"    /{child['name']}/{sub['name']}/  ({sub['total_descendants']} pages)")
        remaining = len(child["children"]) - 5
        if remaining > 0:
            print(f"    ... and {remaining} more subsections")

# Identify KEY pages to crawl (top-level + product + competitor pages)
key_pages = set()

# Always crawl: homepage
key_pages.add("https://www.rudderstack.com/")

# Crawl all depth-1 pages from main sitemap
for url_obj in all_urls:
    if url_obj["sitemap_source"] == "main":
        segments = parse_url(url_obj["url"])
        if segments == ["/"]:
            continue
        if len(segments) <= 2:  # top-level and one level deep
            key_pages.add(url_obj["url"])

# Crawl integration category pages (not individual sub-integrations)
for url_obj in all_urls:
    if url_obj["sitemap_source"] != "main":
        segments = parse_url(url_obj["url"])
        if len(segments) <= 2:  # /integration/X/
            key_pages.add(url_obj["url"])

key_pages_list = sorted(key_pages)
print(f"\n=== KEY PAGES TO CRAWL: {len(key_pages_list)} ===")
for p in key_pages_list[:20]:
    print(f"  {p}")
if len(key_pages_list) > 20:
    print(f"  ... and {len(key_pages_list) - 20} more")

with open("data/key_pages.json", "w") as f:
    json.dump(key_pages_list, f, indent=2)

print(f"\nSaved hierarchy to data/hierarchy.json")
print(f"Saved {len(key_pages_list)} key pages to data/key_pages.json")
