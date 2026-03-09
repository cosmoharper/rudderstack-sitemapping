#!/usr/bin/env python3
"""Generate IA (Information Architecture) diagram data — compact section-level graph for force-directed visualization."""

import json
import os
from collections import defaultdict

# ============================================================
# SECTION CLASSIFICATION (matches other generators)
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
# FUTURE STATE DEFINITIONS (same as other generators)
# ============================================================
TOPIC_HUBS = [
    {"id": "warehouse-native-cdp", "name": "Warehouse-Native CDP", "path": "/topics/warehouse-native-cdp/", "phase": 2,
     "child_pages": [
         {"path": "/topics/warehouse-native-cdp/snowflake-cdp/", "title": "CDP on Snowflake", "phase": 3},
         {"path": "/topics/warehouse-native-cdp/bigquery-cdp/", "title": "BigQuery CDP", "phase": 3},
         {"path": "/topics/warehouse-native-cdp/databricks-cdp/", "title": "Databricks CDP", "phase": 4},
         {"path": "/topics/warehouse-native-cdp/redshift-cdp/", "title": "Redshift CDP", "phase": 4},
     ]},
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
    {"path": "/competitors/migrate-from-segment/", "title": "Migrate from Segment", "phase": 3},
    {"path": "/competitors/cdp-pricing-comparison/", "title": "CDP Pricing Comparison", "phase": 3},
]

CASE_STUDIES = [
    {"path": "/customers/kajabi/", "title": "Kajabi", "phase": 2},
    {"path": "/customers/influxdata/", "title": "InfluxData", "phase": 2},
    {"path": "/customers/grafana/", "title": "Grafana", "phase": 2},
    {"path": "/customers/accurx/", "title": "Accurx", "phase": 2},
    {"path": "/customers/wynn/", "title": "Wynn Slots", "phase": 2},
    {"path": "/customers/wyze/", "title": "Wyze", "phase": 2},
]

QA_PAGES = [
    {"path": "/learn/what-is-a-warehouse-native-cdp/", "phase": 3},
    {"path": "/learn/how-to-build-ai-ready-data-stack/", "phase": 3},
    {"path": "/learn/what-is-event-data-governance/", "phase": 3},
    {"path": "/learn/how-do-ai-agents-use-customer-data/", "phase": 3},
    {"path": "/learn/what-is-the-best-cdp-for-data-teams/", "phase": 3},
    {"path": "/learn/how-to-govern-data-for-ai/", "phase": 3},
    {"path": "/learn/what-is-reverse-etl/", "phase": 3},
    {"path": "/learn/how-to-track-llm-usage/", "phase": 3},
    {"path": "/learn/what-is-a-customer-data-plane/", "phase": 3},
    {"path": "/learn/warehouse-native-vs-traditional-cdp/", "phase": 3},
]

EDUCATION_PAGES = [
    {"path": "/learn/customer-data-management/", "phase": 4},
    {"path": "/learn/cdp-marketing/", "phase": 4},
    {"path": "/learn/dmp-vs-cdp/", "phase": 4},
    {"path": "/learn/customer-database-platform/", "phase": 4},
    {"path": "/learn/cdp-platform/", "phase": 4},
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
# LOAD SOURCE DATA
# ============================================================
print("Loading source data...")

with open("output/links_data.json") as f:
    links_data = json.load(f)

# Try to load backlinks data for extra metrics
backlinks_data = None
try:
    with open("output/backlinks_data.json") as f:
        backlinks_data = json.load(f)
except FileNotFoundError:
    print("  (backlinks_data.json not found, continuing without)")

# ============================================================
# BUILD CURRENT STATE SECTION GRAPH
# ============================================================
print("\nBuilding current-state section graph...")

# Use section_stats from links_data (pre-computed per-section metrics)
section_pages = defaultdict(int)
section_crawled = defaultdict(int)
section_orphans = defaultdict(int)

for sec, sec_stats in links_data.get("section_stats", {}).items():
    section_pages[sec] = sec_stats.get("total_pages", 0)
    section_crawled[sec] = sec_stats.get("crawled", 0)
    section_orphans[sec] = sec_stats.get("orphans", 0)

# Count cross-section body links from the matrix
current_flows = defaultdict(int)
for entry in links_data.get("matrix", []):
    src = entry.get("source", "")
    tgt = entry.get("target", "")
    body = entry.get("body", 0)
    if src != tgt and body > 0:
        key = f"{src}|{tgt}"
        current_flows[key] = body

# Backlinks per section from section_summary
section_backlinks = defaultdict(int)
if backlinks_data:
    for entry in backlinks_data.get("section_summary", []):
        sec = entry.get("section", "")
        section_backlinks[sec] = entry.get("backlinks", 0)

print(f"  {len(section_pages)} sections found")
print(f"  {sum(current_flows.values())} cross-section body links")

# ============================================================
# COMPUTE FUTURE STATE FLOWS
# ============================================================
print("\nComputing future-state flows...")

# Add planned pages to section counts
future_section_pages = dict(section_pages)
planned_by_section = defaultdict(int)

all_planned = []
for hub in TOPIC_HUBS:
    sec = get_section(hub["path"])
    planned_by_section[sec] += 1
    all_planned.append({"path": hub["path"], "section": sec, "phase": hub["phase"]})
    for child in hub["child_pages"]:
        sec = get_section(child["path"])
        planned_by_section[sec] += 1
        all_planned.append({"path": child["path"], "section": sec, "phase": child["phase"]})

for page in COMPARISON_PAGES:
    sec = get_section(page["path"])
    planned_by_section[sec] += 1
    all_planned.append({"path": page["path"], "section": sec, "phase": page["phase"]})

for page in CASE_STUDIES:
    sec = get_section(page["path"])
    planned_by_section[sec] += 1
    all_planned.append({"path": page["path"], "section": sec, "phase": page["phase"]})

for page in QA_PAGES:
    sec = get_section(page["path"])
    planned_by_section[sec] += 1
    all_planned.append({"path": page["path"], "section": sec, "phase": page["phase"]})

for page in EDUCATION_PAGES:
    sec = get_section(page["path"])
    planned_by_section[sec] += 1
    all_planned.append({"path": page["path"], "section": sec, "phase": page["phase"]})

for sec, count in planned_by_section.items():
    future_section_pages[sec] = future_section_pages.get(sec, 0) + count

# Project future flows from linking rules
future_flows = dict(current_flows)
for rule in LINKING_RULES:
    src = rule["source"]
    tgt = rule["target"]
    key = f"{src}|{tgt}"
    pages_in_src = section_crawled.get(src, 0) + planned_by_section.get(src, 0)
    projected = pages_in_src * rule["min_per_page"]
    current = current_flows.get(key, 0)
    future_flows[key] = max(current, projected)

# Also add future flows for new section connections from planned content
# Topics will link to product
if "topics|product" not in future_flows:
    future_flows["topics|product"] = 0
future_flows["topics|product"] = max(future_flows.get("topics|product", 0), len(TOPIC_HUBS) * 3)

# Topics will link to learn
if "topics|learn" not in future_flows:
    future_flows["topics|learn"] = 0
future_flows["topics|learn"] = max(future_flows.get("topics|learn", 0), len(TOPIC_HUBS) * 2)

print(f"  {len(future_flows)} flow pairs in future state")

# ============================================================
# BUILD OUTPUT PAYLOAD
# ============================================================
print("\nBuilding IA diagram payload...")

# Section nodes
all_sections = sorted(set(list(section_pages.keys()) + list(future_section_pages.keys())))

nodes = []
for sec in all_sections:
    current_count = section_pages.get(sec, 0)
    future_count = future_section_pages.get(sec, 0)
    crawled = section_crawled.get(sec, 0)
    orphans = section_orphans.get(sec, 0)
    backlinks = section_backlinks.get(sec, 0)
    planned = planned_by_section.get(sec, 0)
    orphan_rate = orphans / current_count if current_count > 0 else 0
    is_new = current_count == 0 and future_count > 0

    nodes.append({
        "id": sec,
        "label": sec.replace("_", " ").title() if sec not in ["docs", "core", "other", "events"] else {
            "docs": "Documentation",
            "core": "Core Pages",
            "other": "Other",
            "events": "Events & Webinars"
        }.get(sec, sec.title()),
        "current_pages": current_count,
        "future_pages": future_count,
        "planned_pages": planned,
        "crawled_pages": crawled,
        "orphan_pages": orphans,
        "orphan_rate": round(orphan_rate, 3),
        "backlinks": backlinks,
        "is_new": is_new,
    })

# Edges — one for each flow direction
edges = []
seen_pairs = set()
all_flow_keys = set(list(current_flows.keys()) + list(future_flows.keys()))

for key in sorted(all_flow_keys):
    src, tgt = key.split("|")
    pair_key = f"{min(src,tgt)}|{max(src,tgt)}"

    cur = current_flows.get(key, 0)
    fut = future_flows.get(key, 0)

    edges.append({
        "source": src,
        "target": tgt,
        "current_count": cur,
        "future_count": fut,
        "is_new": cur == 0 and fut > 0,
    })

# Linking rules for display
linking_rules = []
for rule in LINKING_RULES:
    key = f"{rule['source']}|{rule['target']}"
    cur = current_flows.get(key, 0)
    fut = future_flows.get(key, 0)
    linking_rules.append({
        "id": rule["id"],
        "source": rule["source"],
        "target": rule["target"],
        "min_per_page": rule["min_per_page"],
        "phase": rule["phase"],
        "current_links": cur,
        "projected_links": fut,
        "gap": max(0, fut - cur),
    })

# Topic hubs for future state display
topic_hubs_data = []
for hub in TOPIC_HUBS:
    topic_hubs_data.append({
        "id": hub["id"],
        "name": hub["name"],
        "path": hub["path"],
        "phase": hub["phase"],
        "child_count": len(hub["child_pages"]),
    })

# Summary stats
total_current = sum(n["current_pages"] for n in nodes)
total_future = sum(n["future_pages"] for n in nodes)
total_current_flows = sum(current_flows.values())
total_future_flows = sum(future_flows.values())

payload = {
    "nodes": nodes,
    "edges": edges,
    "linking_rules": linking_rules,
    "topic_hubs": topic_hubs_data,
    "stats": {
        "total_sections": len(nodes),
        "new_sections": sum(1 for n in nodes if n["is_new"]),
        "total_current_pages": total_current,
        "total_future_pages": total_future,
        "total_planned_pages": sum(n["planned_pages"] for n in nodes),
        "total_current_flows": total_current_flows,
        "total_future_flows": total_future_flows,
        "flow_increase": total_future_flows - total_current_flows,
    }
}

# ============================================================
# WRITE OUTPUT
# ============================================================
out_path = "output/ia_data.json"
with open(out_path, "w") as f:
    json.dump(payload, f, indent=2)

size_kb = os.path.getsize(out_path) / 1024
print(f"\nPayload written to {out_path} ({size_kb:.1f} KB)")
print(f"  {len(nodes)} section nodes")
print(f"  {len(edges)} directed edges")
print(f"  Current: {total_current} pages, {total_current_flows} cross-section links")
print(f"  Future: {total_future} pages, {total_future_flows} cross-section links (+{total_future_flows - total_current_flows})")
