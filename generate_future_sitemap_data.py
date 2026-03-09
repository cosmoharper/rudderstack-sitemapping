#!/usr/bin/env python3
"""Generate future-state sitemap tree by merging current diagram_data.json with planned pages."""

import json
import copy
import os
from collections import defaultdict

# ============================================================
# SECTION CLASSIFICATION (with new 'topics' section)
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
    ("topics",       lambda p: p.startswith("/topics/")),
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

# ============================================================
# FUTURE STATE PAGE DEFINITIONS (from strategy documents)
# ============================================================
TOPIC_HUBS = [
    {
        "id": "warehouse-native-cdp", "name": "Warehouse-Native CDP",
        "path": "/topics/warehouse-native-cdp/", "phase": 2,
        "child_pages": [
            {"path": "/topics/warehouse-native-cdp/snowflake-cdp/", "title": "Complete Guide to CDP on Snowflake", "phase": 3},
            {"path": "/topics/warehouse-native-cdp/bigquery-cdp/", "title": "BigQuery as CDP Foundation", "phase": 3},
            {"path": "/topics/warehouse-native-cdp/databricks-cdp/", "title": "Customer Data on Databricks", "phase": 4},
            {"path": "/topics/warehouse-native-cdp/redshift-cdp/", "title": "Redshift CDP Implementation", "phase": 4},
        ],
    },
    {"id": "event-streaming", "name": "Event Streaming", "path": "/topics/event-streaming/", "phase": 3, "child_pages": []},
    {"id": "reverse-etl", "name": "Reverse ETL", "path": "/topics/reverse-etl/", "phase": 3, "child_pages": []},
    {"id": "identity-resolution", "name": "Identity Resolution", "path": "/topics/identity-resolution/", "phase": 3, "child_pages": []},
    {"id": "data-governance", "name": "Data Governance", "path": "/topics/data-governance/", "phase": 2, "child_pages": []},
    {"id": "ai-ml", "name": "AI & ML Data", "path": "/topics/ai-ml/", "phase": 3, "child_pages": []},
]

COMPARISON_PAGES = [
    {"path": "/competitors/rudderstack-vs-mparticle/", "title": "RudderStack vs mParticle", "phase": 2},
    {"path": "/competitors/rudderstack-vs-hightouch/", "title": "RudderStack vs Hightouch", "phase": 3},
    {"path": "/competitors/segment-alternatives-2026/", "title": "Segment Alternatives 2026", "phase": 3},
    {"path": "/competitors/migrate-from-segment/", "title": "Migrate from Segment to RudderStack", "phase": 3},
    {"path": "/competitors/cdp-pricing-comparison/", "title": "CDP Pricing Comparison", "phase": 3},
]

CASE_STUDIES = [
    {"path": "/customers/kajabi/", "title": "Kajabi + RudderStack", "phase": 2},
    {"path": "/customers/influxdata/", "title": "InfluxData + RudderStack", "phase": 2},
    {"path": "/customers/grafana/", "title": "Grafana + RudderStack", "phase": 2},
    {"path": "/customers/accurx/", "title": "Accurx + RudderStack", "phase": 2},
    {"path": "/customers/wynn/", "title": "Wynn Slots + RudderStack", "phase": 2},
    {"path": "/customers/wyze/", "title": "Wyze + RudderStack", "phase": 2},
]

QA_PAGES = [
    {"path": "/learn/what-is-a-warehouse-native-cdp/", "title": "What Is a Warehouse-Native CDP?", "phase": 3},
    {"path": "/learn/how-to-build-ai-ready-data-stack/", "title": "How to Build an AI-Ready Data Stack", "phase": 3},
    {"path": "/learn/what-is-event-data-governance/", "title": "What Is Event Data Governance?", "phase": 3},
    {"path": "/learn/how-do-ai-agents-use-customer-data/", "title": "How Do AI Agents Use Customer Data?", "phase": 3},
    {"path": "/learn/what-is-the-best-cdp-for-data-teams/", "title": "Best CDP for Data Teams", "phase": 3},
    {"path": "/learn/how-to-govern-data-for-ai/", "title": "How to Govern Data for AI Models", "phase": 3},
    {"path": "/learn/what-is-reverse-etl/", "title": "What Is Reverse ETL?", "phase": 3},
    {"path": "/learn/how-to-track-llm-usage/", "title": "How to Track LLM Usage & Analytics", "phase": 3},
    {"path": "/learn/what-is-a-customer-data-plane/", "title": "What Is a Customer Data Plane?", "phase": 3},
    {"path": "/learn/warehouse-native-vs-traditional-cdp/", "title": "Warehouse-Native vs Traditional CDP", "phase": 3},
]

EDUCATION_PAGES = [
    {"path": "/learn/customer-data-management/", "title": "Customer Data Management Guide", "phase": 4},
    {"path": "/learn/cdp-marketing/", "title": "CDP for Marketing Teams", "phase": 4},
    {"path": "/learn/dmp-vs-cdp/", "title": "DMP vs CDP: Complete Comparison", "phase": 4},
    {"path": "/learn/customer-database-platform/", "title": "Customer Database Platform Guide", "phase": 4},
    {"path": "/learn/cdp-platform/", "title": "CDP Platform: What to Evaluate", "phase": 4},
]

LINKING_RULES = [
    {"id": "blog_to_product", "source": "blog", "target": "product", "min_per_page": 3, "phase": 2},
    {"id": "learn_to_product", "source": "learn", "target": "product", "min_per_page": 2, "phase": 3},
    {"id": "blog_to_hub", "source": "blog", "target": "topics", "min_per_page": 1, "phase": 2},
    {"id": "integration_to_hub", "source": "integrations", "target": "topics", "min_per_page": 1, "phase": 3},
    {"id": "integration_cross", "source": "integrations", "target": "integrations", "min_per_page": 3, "phase": 3},
    {"id": "comparison_to_hub", "source": "competitors", "target": "topics", "min_per_page": 2, "phase": 2},
    {"id": "casestudy_to_int", "source": "customers", "target": "integrations", "min_per_page": 2, "phase": 2},
]

# ============================================================
# LOAD & PROCESS
# ============================================================
print("Loading diagram_data.json...")
with open("output/diagram_data.json") as f:
    data = json.load(f)

tree = copy.deepcopy(data["tree"])
edges = data["edges"]
current_flows = data["cross_section_flows"]
stats = data["stats"]

print(f"  Current tree: {stats['total_pages']} pages, {len(edges)} body edges")

# Build _children_map for tree navigation
def build_maps(node):
    node["_children_map"] = {}
    for child in node.get("children", []):
        node["_children_map"][child["name"]] = child
        build_maps(child)

build_maps(tree)

# Collect all existing paths
existing_paths = set()
def collect_paths(node):
    existing_paths.add(node["path"])
    for child in node.get("children", []):
        collect_paths(child)

collect_paths(tree)

# ============================================================
# INSERT PLANNED PAGES INTO TREE
# ============================================================
def insert_planned_page(path, title, phase, page_type):
    """Insert a planned page into the tree at the correct position."""
    if path in existing_paths:
        return False  # already exists

    segments = path.strip("/").split("/")
    current = tree
    for i, seg in enumerate(segments):
        child_path = "/" + "/".join(segments[:i+1]) + "/"
        if seg in current.get("_children_map", {}):
            current = current["_children_map"][seg]
        else:
            child = {
                "name": seg,
                "path": child_path,
                "children": [],
                "_children_map": {},
                "url_count": 0,
                "total_urls": 0,
                "ctas": [],
                "consolidated_ctas": [],
                "has_crawl_data": False,
                "inbound_count": 0,
                "nav_inbound": 0,
                "nav_outbound": 0,
                "is_orphan": True,
                "is_planned": True,
                "phase": phase,
                "planned_type": page_type,
                "planned_title": title,
            }
            if "_children_map" not in current:
                current["_children_map"] = {}
            current["_children_map"][seg] = child
            current["children"].append(child)
            current = child

    # Mark the leaf node
    current["is_planned"] = True
    current["phase"] = phase
    current["planned_type"] = page_type
    current["planned_title"] = title
    current["url_count"] = max(current.get("url_count", 0), 1)
    current["total_urls"] = max(current.get("total_urls", 0), 1)
    existing_paths.add(path)
    return True

# Insert all planned pages
planned_pages = []
added = 0

print("\nInserting planned pages...")

# Topic hubs + children
for hub in TOPIC_HUBS:
    if insert_planned_page(hub["path"], hub["name"] + " Hub", hub["phase"], "topic_hub"):
        planned_pages.append({"path": hub["path"], "title": hub["name"] + " Hub", "type": "topic_hub", "phase": hub["phase"]})
        added += 1
    for child in hub["child_pages"]:
        if insert_planned_page(child["path"], child["title"], child["phase"], "warehouse_pillar"):
            planned_pages.append({"path": child["path"], "title": child["title"], "type": "warehouse_pillar", "phase": child["phase"]})
            added += 1

# Comparison pages
for page in COMPARISON_PAGES:
    if insert_planned_page(page["path"], page["title"], page["phase"], "comparison"):
        planned_pages.append({"path": page["path"], "title": page["title"], "type": "comparison", "phase": page["phase"]})
        added += 1

# Case studies
for page in CASE_STUDIES:
    if insert_planned_page(page["path"], page["title"], page["phase"], "case_study"):
        planned_pages.append({"path": page["path"], "title": page["title"], "type": "case_study", "phase": page["phase"]})
        added += 1

# Q&A pages
for page in QA_PAGES:
    if insert_planned_page(page["path"], page["title"], page["phase"], "qa_aeo"):
        planned_pages.append({"path": page["path"], "title": page["title"], "type": "qa_aeo", "phase": page["phase"]})
        added += 1

# Education pages
for page in EDUCATION_PAGES:
    if insert_planned_page(page["path"], page["title"], page["phase"], "education"):
        planned_pages.append({"path": page["path"], "title": page["title"], "type": "education", "phase": page["phase"]})
        added += 1

print(f"  Added {added} new planned pages")

# ============================================================
# COMPUTE PROJECTED CROSS-SECTION FLOWS
# ============================================================
print("\nComputing projected cross-section flows...")

# Build current flow map
current_flow_map = {}
for flow in current_flows:
    key = f"{flow['source']}|{flow['target']}"
    current_flow_map[key] = flow["count"]

# Count crawled pages per section (for linking rule projections)
section_page_counts = defaultdict(int)
def count_section_pages(node):
    if node.get("has_crawl_data"):
        sec = get_section(node["path"])
        section_page_counts[sec] += 1
    for child in node.get("children", []):
        count_section_pages(child)

count_section_pages(tree)

# Project future flows from linking rules
projected_flow_map = dict(current_flow_map)
for rule in LINKING_RULES:
    src = rule["source"]
    tgt = rule["target"]
    key = f"{src}|{tgt}"
    pages_in_src = section_page_counts.get(src, 0)
    projected = pages_in_src * rule["min_per_page"]
    current = current_flow_map.get(key, 0)
    projected_flow_map[key] = max(current, projected)

# Build future flows list
future_flows = []
for key, count in projected_flow_map.items():
    src, tgt = key.split("|")
    current = current_flow_map.get(key, 0)
    future_flows.append({
        "source": src, "target": tgt,
        "current_count": current, "future_count": count,
        "is_new": current == 0 and count > 0,
    })
future_flows.sort(key=lambda f: f["future_count"], reverse=True)

# ============================================================
# CLEAN UP TREE (remove _children_map before serialization)
# ============================================================
def clean_tree(node):
    node.pop("_children_map", None)
    # Recompute total_urls for planned intermediate nodes
    if node.get("children"):
        child_total = sum(clean_tree(c) for c in node["children"])
        node["total_urls"] = max(node.get("url_count", 0), 0) + child_total
    else:
        node["total_urls"] = max(node.get("url_count", 0), 1)
    return node["total_urls"]

clean_tree(tree)

# ============================================================
# COMPUTE STATS
# ============================================================
phase_counts = defaultdict(int)
type_counts = defaultdict(int)
for p in planned_pages:
    phase_counts[p["phase"]] += 1
    type_counts[p["type"]] += 1

future_stats = {
    "current_total_pages": stats["total_pages"],
    "future_total_pages": stats["total_pages"] + added,
    "pages_added": added,
    "current_orphan_count": stats["orphan_count"],
    "pages_crawled": stats.get("pages_crawled", stats.get("crawled_pages", 0)),
    "current_body_links": stats.get("body_links", 0),
    "by_phase": dict(phase_counts),
    "by_type": dict(type_counts),
    "topic_hubs": len(TOPIC_HUBS),
    "new_sections": ["topics"],
}

# ============================================================
# WRITE OUTPUT
# ============================================================
payload = {
    "tree": tree,
    "edges": edges,
    "planned_pages": planned_pages,
    "current_flows": current_flows,
    "future_flows": future_flows,
    "conversion_endpoints": data.get("conversion_endpoints", []),
    "header_nav": data.get("header_nav", []),
    "footer_nav": data.get("footer_nav", []),
    "stats": future_stats,
}

out_path = "output/future_sitemap_data.json"
with open(out_path, "w") as f:
    json.dump(payload, f, separators=(",", ":"))

size_mb = os.path.getsize(out_path) / 1024 / 1024
print(f"\nPayload written to {out_path} ({size_mb:.1f} MB)")
print(f"  {added} planned pages across {len(phase_counts)} phases")
print(f"  {len(future_flows)} projected cross-section flows")
print(f"  Types: {dict(type_counts)}")
