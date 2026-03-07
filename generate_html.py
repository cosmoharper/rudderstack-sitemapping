#!/usr/bin/env python3
"""Generate the interactive HTML diagram data payload."""

import json
import os
from collections import defaultdict
from urllib.parse import urlparse

# Load data
with open("data/all_urls.json") as f:
    all_urls = json.load(f)

with open("data/crawl_results.json") as f:
    crawl_results = json.load(f)

# Load nav structure (optional — falls back gracefully)
nav_data = {"header_nav": [], "footer_nav": []}
if os.path.exists("data/nav_structure.json"):
    with open("data/nav_structure.json") as f:
        nav_data = json.load(f)
    print(f"Loaded nav structure: {len(nav_data['header_nav'])} header, {len(nav_data['footer_nav'])} footer sections")
else:
    print("Warning: data/nav_structure.json not found — nav layers will be empty")

# Build a compact tree for the visualization
def parse_path(url):
    path = urlparse(url).path.strip("/")
    if not path:
        return []
    return path.split("/")

# Build tree
tree = {"name": "rudderstack.com", "path": "/", "children": [], "_children_map": {}, "url_count": 0, "ctas": [], "has_crawl_data": False}

for url_obj in all_urls:
    url = url_obj["url"]
    segments = parse_path(url)

    current = tree
    for i, seg in enumerate(segments):
        if seg not in current["_children_map"]:
            child = {
                "name": seg,
                "path": "/" + "/".join(segments[:i+1]) + "/",
                "children": [],
                "_children_map": {},
                "url_count": 0,
                "ctas": [],
                "has_crawl_data": False,
            }
            current["_children_map"][seg] = child
            current["children"].append(child)
        current = current["_children_map"][seg]

    current["url_count"] += 1

    # Add crawl data if available
    crawl = crawl_results.get(url, None)
    if crawl and crawl["status"] == "ok":
        current["has_crawl_data"] = True
        current["ctas"] = [
            {"text": c["text"], "href": c["href"], "type": c["type"], "location": c.get("location", "body")}
            for c in crawl.get("ctas", [])
        ]
        current["link_count"] = crawl.get("link_count", 0)

# Clean up internal maps and compute totals
def clean_tree(node):
    del node["_children_map"]
    total = node["url_count"]
    for child in node["children"]:
        total += clean_tree(child)
    node["total_urls"] = total

    # Sort children by total_urls descending
    node["children"].sort(key=lambda x: -x["total_urls"])
    return total

clean_tree(tree)

# ============================================================
# CTA CONSOLIDATION
# ============================================================
def consolidate_ctas(node):
    """Walk tree, collect all CTAs from node and descendants.
    Group by (text, href) — count how many pages share each CTA.
    Store result as consolidated_ctas on each node.
    """
    # Collect all CTAs from this node and all descendants
    all_ctas = []

    def collect(n):
        for cta in n.get("ctas", []):
            all_ctas.append(cta)
        for child in n.get("children", []):
            collect(child)

    collect(node)

    # Group by text
    by_text = defaultdict(list)
    for cta in all_ctas:
        text = cta.get("text", "(no text)").strip()
        by_text[text].append(cta)

    consolidated = []
    for text, ctas_list in sorted(by_text.items(), key=lambda x: -len(x[1])):
        hrefs = [c["href"] for c in ctas_list]
        unique_hrefs = list(set(hrefs))
        locations = [c.get("location", "body") for c in ctas_list]
        body_count = sum(1 for loc in locations if loc == "body")
        entry = {
            "text": text,
            "count": len(ctas_list),  # total pages with this CTA text
            "body_count": body_count,
            "unique_targets": len(unique_hrefs),
        }
        if len(unique_hrefs) == 1:
            entry["href"] = unique_hrefs[0]
        elif len(unique_hrefs) <= 3:
            entry["hrefs"] = unique_hrefs
        else:
            entry["href_sample"] = unique_hrefs[:3]
        consolidated.append(entry)

    node["consolidated_ctas"] = consolidated

    # Recurse for children
    for child in node.get("children", []):
        consolidate_ctas(child)

consolidate_ctas(tree)

# ============================================================
# CONVERSION ENDPOINTS
# ============================================================
CONVERSION_ENDPOINTS = [
    {
        "id": "app_signup",
        "name": "App Signup",
        "url": "https://app.rudderstack.com/signup",
        "type": "external",
        "form_fields": ["email", "password"],
        "tracking_event": "signup_click",
    },
    {
        "id": "request_demo",
        "name": "Request Demo",
        "url": "/request-demo/",
        "type": "form",
        "form_fields": ["firstName", "lastName", "email", "company", "jobTitle", "estimated_event_volume"],
        "tracking_event": "form_submit",
        "form_id": "request-demo-form",
        "tracking_detail": "data-qualified-field attributes",
    },
    {
        "id": "enterprise_quote",
        "name": "Enterprise Quote",
        "url": "/enterprise-quote/",
        "type": "form",
        "form_fields": ["firstName", "lastName", "email", "company", "jobTitle"],
        "tracking_event": "form_submit",
        "form_id": "enterprise-quote-form",
    },
    {
        "id": "contact",
        "name": "Contact",
        "url": "/contact/",
        "type": "form",
        "form_fields": ["firstName", "lastName", "email"],
        "tracking_event": "form_submit",
        "form_id": "contact-form",
    },
    {
        "id": "interactive_demo",
        "name": "Interactive Demo",
        "url": "/interactive-demo/",
        "type": "page",
        "form_fields": [],
        "tracking_event": "demo_click",
    },
]

# Scan crawl data to find which pages have CTAs pointing to each endpoint
conversion_targets = {
    "app_signup": ["app.rudderstack.com/signup", "app.rudderstack.com"],
    "request_demo": ["/request-demo"],
    "enterprise_quote": ["/enterprise-quote"],
    "contact": ["/contact"],
    "interactive_demo": ["/interactive-demo"],
}

for endpoint in CONVERSION_ENDPOINTS:
    targets = conversion_targets[endpoint["id"]]
    source_pages = []
    for source_url, data in crawl_results.items():
        if data.get("status") != "ok":
            continue
        for cta in data.get("ctas", []):
            href = cta["href"]
            if any(t in href for t in targets):
                path = urlparse(source_url).path.rstrip("/") or "/"
                location = cta.get("location", "body")
                source_pages.append({
                    "path": path,
                    "cta_text": cta.get("text", ""),
                    "location": location,
                })
                break  # one match per source page is enough
    endpoint["source_pages"] = source_pages
    endpoint["source_count"] = len(source_pages)
    endpoint["body_source_count"] = sum(1 for sp in source_pages if sp.get("location") == "body")

# Build link edges (only for crawled pages)
edges = []
seen = set()
for source_url, data in crawl_results.items():
    if data["status"] != "ok":
        continue
    for link in data.get("internal_links", []):
        target = link["href"]
        if not target.startswith("https://www.rudderstack.com"):
            continue
        # Normalize
        s = urlparse(source_url).path.rstrip("/") or "/"
        t = urlparse(target).path.rstrip("/") or "/"
        if s == t:
            continue
        key = (s, t)
        if key not in seen:
            seen.add(key)
            is_cta = any(c["href"] == link["href"] for c in data.get("ctas", []))
            edges.append({
                "source": s,
                "target": t,
                "text": link.get("text", "")[:80],
                "is_nav": link.get("is_nav", False),
                "is_cta": is_cta,
                "location": link.get("location", "body"),
            })

# ============================================================
# INBOUND LINK COUNTS
# ============================================================
inbound_counts = defaultdict(int)
for edge in edges:
    inbound_counts[edge["target"]] += 1

def attach_inbound(node):
    """Attach inbound link count to each tree node."""
    path = node["path"].rstrip("/") or "/"
    node["inbound_count"] = inbound_counts.get(path, 0)
    for child in node.get("children", []):
        attach_inbound(child)

attach_inbound(tree)

total_with_inbound = sum(1 for v in inbound_counts.values() if v > 0)
print(f"Inbound link counts: {len(inbound_counts)} pages have inbound links")

# ============================================================
# ORPHAN PAGE DETECTION
# ============================================================
# Collect all paths in the tree
all_paths = set()
def collect_paths(node):
    path = node["path"].rstrip("/") or "/"
    all_paths.add(path)
    for child in node.get("children", []):
        collect_paths(child)
collect_paths(tree)

# Pages that are link targets
all_targets = set(e["target"] for e in edges)

# Orphans = pages in sitemap with zero inbound internal links (exclude root)
orphan_paths = sorted(all_paths - all_targets - {"/"})
print(f"Orphan pages (no inbound links from crawled pages): {len(orphan_paths)} of {len(all_paths)}")

# Mark orphans on tree nodes
orphan_set = set(orphan_paths)
def mark_orphans(node):
    path = node["path"].rstrip("/") or "/"
    node["is_orphan"] = path in orphan_set
    for child in node.get("children", []):
        mark_orphans(child)
mark_orphans(tree)

# ============================================================
# CROSS-SECTION LINK MATRIX
# ============================================================
SECTION_RULES = [
    ("product",      lambda p: p.startswith("/product/")),
    ("docs",         lambda p: p.startswith("/docs/")),
    ("blog",         lambda p: p.startswith("/blog/")),
    ("learn",        lambda p: p.startswith("/learn/") or p.startswith("/guides/") or p.startswith("/knowledge-base/")),
    ("customers",    lambda p: p.startswith("/customers/")),
    ("competitors",  lambda p: p.startswith("/competitors/")),
    ("integrations", lambda p: p.startswith("/integration/")),
    ("events",       lambda p: p.startswith("/webinars/") or p.startswith("/events/")),
    ("core",         lambda p: p in ["/", "/pricing", "/about", "/contact", "/request-demo",
                                      "/enterprise-quote", "/interactive-demo", "/careers",
                                      "/security", "/partners", "/partnerships", "/resource-center"]),
]

def get_section(path):
    path = path.rstrip("/") or "/"
    for key, match_fn in SECTION_RULES:
        if match_fn(path):
            return key
    return "other"

# Build cross-section matrix: only count cross-section links (not within same section)
section_matrix = defaultdict(lambda: defaultdict(int))
for edge in edges:
    src_sec = get_section(edge["source"])
    tgt_sec = get_section(edge["target"])
    if src_sec != tgt_sec:
        section_matrix[src_sec][tgt_sec] += 1

# Convert to serializable format: sorted list of top flows
cross_section_flows = []
for src_sec, targets in section_matrix.items():
    for tgt_sec, count in targets.items():
        cross_section_flows.append({
            "source": src_sec,
            "target": tgt_sec,
            "count": count,
        })
cross_section_flows.sort(key=lambda x: -x["count"])

print(f"Cross-section link flows: {len(cross_section_flows)} unique section pairs")
for flow in cross_section_flows[:10]:
    print(f"  {flow['source']} -> {flow['target']}: {flow['count']}")

# ============================================================
# WRITE DATA PAYLOAD
# ============================================================
payload = {
    "tree": tree,
    "edges": edges,
    "conversion_endpoints": CONVERSION_ENDPOINTS,
    "header_nav": nav_data.get("header_nav", []),
    "footer_nav": nav_data.get("footer_nav", []),
    "cross_section_flows": cross_section_flows,
    "stats": {
        "total_pages": len(all_urls),
        "pages_crawled": len([d for d in crawl_results.values() if d["status"] == "ok"]),
        "total_links": len(edges),
        "total_ctas": sum(len(d.get("ctas", [])) for d in crawl_results.values()),
        "orphan_count": len(orphan_paths),
    }
}

with open("output/diagram_data.json", "w") as f:
    json.dump(payload, f)

print(f"\nTree nodes at root level: {len(tree['children'])}")
print(f"Link edges: {len(edges)}")
print(f"Conversion endpoints: {len(CONVERSION_ENDPOINTS)}")
for ep in CONVERSION_ENDPOINTS:
    print(f"  {ep['name']}: {ep['source_count']} total ({ep['body_source_count']} body, {ep['source_count'] - ep['body_source_count']} nav)")
print(f"Orphan pages: {len(orphan_paths)}")
print(f"Data payload written to output/diagram_data.json")
