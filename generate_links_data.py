#!/usr/bin/env python3
"""Generate aggregated internal linking data for the linking visualization page."""

import json
import os
from collections import defaultdict
from urllib.parse import urlparse

# Load data
with open("data/crawl_results.json") as f:
    crawl_results = json.load(f)

with open("data/all_urls.json") as f:
    all_urls = json.load(f)

# Section classification
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

# All sitemap paths
all_sitemap_paths = set()
for u in all_urls:
    path = urlparse(u["url"]).path.rstrip("/") or "/"
    all_sitemap_paths.add(path)

# Build edge list (deduplicated)
edges = []
seen_edges = set()
page_outbound = defaultdict(list)  # path -> list of target paths
page_inbound = defaultdict(list)   # path -> list of source paths

for source_url, data in crawl_results.items():
    if data.get("status") != "ok":
        continue
    source_path = urlparse(source_url).path.rstrip("/") or "/"

    for link in data.get("internal_links", []):
        target = link["href"]
        if not target.startswith("https://www.rudderstack.com"):
            continue
        target_path = urlparse(target).path.rstrip("/") or "/"
        if source_path == target_path:
            continue

        key = (source_path, target_path)
        if key not in seen_edges:
            seen_edges.add(key)
            location = link.get("location", "body")
            is_nav = link.get("is_nav", False)
            is_body = location == "body" and not is_nav

            edge = {
                "s": source_path,
                "t": target_path,
                "loc": location,
                "nav": is_nav,
                "body": is_body,
            }
            edges.append(edge)
            page_outbound[source_path].append(target_path)
            page_inbound[target_path].append(source_path)

print(f"Total unique edges: {len(edges):,}")
print(f"Pages with outbound links: {len(page_outbound):,}")
print(f"Pages with inbound links: {len(page_inbound):,}")

# Precompute body/nav inbound counts in a single pass over edges
page_inbound_body = defaultdict(int)
page_inbound_nav = defaultdict(int)
for edge in edges:
    if edge["body"]:
        page_inbound_body[edge["t"]] += 1
    else:
        page_inbound_nav[edge["t"]] += 1

# ============================================================
# 1. PAGE-LEVEL STATS
# ============================================================
pages = []
crawled_paths = set()
for url, data in crawl_results.items():
    if data.get("status") != "ok":
        continue
    path = urlparse(url).path.rstrip("/") or "/"
    crawled_paths.add(path)

for path in sorted(all_sitemap_paths):
    section = get_section(path)
    inbound_count = len(page_inbound.get(path, []))
    outbound_count = len(page_outbound.get(path, []))

    pages.append({
        "path": path,
        "section": section,
        "crawled": path in crawled_paths,
        "inbound": inbound_count,
        "inbound_body": page_inbound_body.get(path, 0),
        "inbound_nav": page_inbound_nav.get(path, 0),
        "outbound": outbound_count,
        "is_orphan": inbound_count == 0 and path != "/",
    })

# Sort by inbound descending for the top pages
pages.sort(key=lambda p: -p["inbound"])

print(f"\nTotal pages: {len(pages)}")
print(f"Crawled: {len(crawled_paths)}")
print(f"Orphans: {sum(1 for p in pages if p['is_orphan'])}")

# ============================================================
# 2. CROSS-SECTION MATRIX
# ============================================================
section_matrix = defaultdict(lambda: defaultdict(int))
section_matrix_body = defaultdict(lambda: defaultdict(int))

for edge in edges:
    src_sec = get_section(edge["s"])
    tgt_sec = get_section(edge["t"])
    section_matrix[src_sec][tgt_sec] += 1
    if edge["body"]:
        section_matrix_body[src_sec][tgt_sec] += 1

# Get all sections
all_sections = sorted(set(
    list(section_matrix.keys()) +
    [t for targets in section_matrix.values() for t in targets]
))

matrix_data = []
for src in all_sections:
    for tgt in all_sections:
        total = section_matrix[src][tgt]
        body = section_matrix_body[src][tgt]
        if total > 0:
            matrix_data.append({
                "source": src,
                "target": tgt,
                "total": total,
                "body": body,
                "nav": total - body,
            })

matrix_data.sort(key=lambda x: -x["total"])
print(f"\nCross-section flows: {len(matrix_data)} pairs")

# ============================================================
# 3. SECTION SUMMARIES
# ============================================================
section_stats = {}
for section in all_sections:
    sec_pages = [p for p in pages if p["section"] == section]
    sec_crawled = [p for p in sec_pages if p["crawled"]]
    sec_inbound = [p["inbound"] for p in sec_pages]
    sec_outbound = [p["outbound"] for p in sec_crawled]
    sec_orphans = [p for p in sec_pages if p["is_orphan"]]

    section_stats[section] = {
        "total_pages": len(sec_pages),
        "crawled": len(sec_crawled),
        "orphans": len(sec_orphans),
        "avg_inbound": round(sum(sec_inbound) / len(sec_inbound), 1) if sec_inbound else 0,
        "avg_outbound": round(sum(sec_outbound) / len(sec_outbound), 1) if sec_outbound else 0,
        "max_inbound": max(sec_inbound) if sec_inbound else 0,
        "total_inbound": sum(sec_inbound),
        "total_outbound": sum(sec_outbound),
    }

print(f"\nSection stats:")
for sec in sorted(section_stats, key=lambda s: -section_stats[s]["total_pages"]):
    s = section_stats[sec]
    print(f"  {sec:15s}: {s['total_pages']:5d} pages, {s['crawled']:4d} crawled, {s['orphans']:5d} orphans, avg in={s['avg_inbound']:.1f} out={s['avg_outbound']:.1f}")

# ============================================================
# 4. TOP PAGES (limit to top 500 by inbound)
# ============================================================
top_pages = pages[:500]

# ============================================================
# 5. INBOUND DISTRIBUTION (histogram buckets)
# ============================================================
inbound_counts = [p["inbound"] for p in pages]
buckets = [0, 1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000, 5000]
distribution = []
for i in range(len(buckets)):
    lo = buckets[i]
    hi = buckets[i + 1] if i + 1 < len(buckets) else float("inf")
    count = sum(1 for c in inbound_counts if lo <= c < hi)
    label = f"{lo}" if hi == lo + 1 else f"{lo}-{int(hi)-1}" if hi != float("inf") else f"{lo}+"
    distribution.append({"label": label, "min": lo, "max": hi if hi != float("inf") else 99999, "count": count})

print(f"\nInbound link distribution:")
for d in distribution:
    print(f"  {d['label']:10s}: {d['count']:5d} pages")

# ============================================================
# 6. ORPHAN PAGES BY SECTION (all orphans)
# ============================================================
orphan_pages = [p for p in pages if p["is_orphan"]]
orphan_by_section = defaultdict(list)
for p in orphan_pages:
    orphan_by_section[p["section"]].append(p["path"])

orphan_summary = []
for sec in sorted(orphan_by_section, key=lambda s: -len(orphan_by_section[s])):
    paths = orphan_by_section[sec]
    orphan_summary.append({
        "section": sec,
        "count": len(paths),
        "sample": paths[:20],  # first 20 as sample
    })

# ============================================================
# 7. TOP LINKED-TO PAGES (by body inbound only)
# ============================================================
pages_by_body_inbound = sorted(pages, key=lambda p: -p["inbound_body"])
top_body_targets = pages_by_body_inbound[:100]

# ============================================================
# WRITE PAYLOAD
# ============================================================
# Don't include full edge list (1.58M is too much). Include section-level flows
# and per-page summaries instead.

payload = {
    "sections": all_sections,
    "section_stats": section_stats,
    "matrix": matrix_data,
    "distribution": distribution,
    "top_pages": top_pages,
    "top_body_targets": top_body_targets,
    "orphan_summary": orphan_summary,
    "stats": {
        "total_pages": len(pages),
        "crawled_pages": len(crawled_paths),
        "total_edges": len(edges),
        "body_edges": sum(1 for e in edges if e["body"]),
        "nav_edges": sum(1 for e in edges if not e["body"]),
        "orphan_pages": len(orphan_pages),
        "sections_count": len(all_sections),
    }
}

with open("output/links_data.json", "w") as f:
    json.dump(payload, f)

size_mb = os.path.getsize("output/links_data.json") / 1024 / 1024
print(f"\nPayload written to output/links_data.json ({size_mb:.1f} MB)")
print(f"Stats: {payload['stats']}")
