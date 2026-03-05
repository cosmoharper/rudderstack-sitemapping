#!/usr/bin/env python3
"""Generate CSV and JSON outputs combining hierarchy, links, and CTAs."""

import json
import csv
from urllib.parse import urlparse

# Load data
with open("data/all_urls.json") as f:
    all_urls = json.load(f)

with open("data/hierarchy.json") as f:
    hierarchy = json.load(f)

with open("data/crawl_results.json") as f:
    crawl_results = json.load(f)

# ============================================================
# 1. Pages CSV - Every page with its section, depth, CTAs
# ============================================================
def get_section(url):
    path = urlparse(url).path.strip("/")
    if not path:
        return "homepage"
    return path.split("/")[0]

def get_depth(url):
    path = urlparse(url).path.strip("/")
    if not path:
        return 0
    return len(path.split("/"))

pages_rows = []
for url_obj in all_urls:
    url = url_obj["url"]
    section = get_section(url)
    depth = get_depth(url)

    # Check if we have crawl data for this page
    crawl_data = crawl_results.get(url, {})
    ctas = crawl_data.get("ctas", [])
    cta_texts = "; ".join([f"{c['text']} -> {c['href']}" for c in ctas]) if ctas else ""
    cta_count = len(ctas)
    internal_link_count = crawl_data.get("link_count", 0)

    pages_rows.append({
        "url": url,
        "section": section,
        "depth": depth,
        "sitemap_source": url_obj.get("sitemap_source", ""),
        "lastmod": url_obj.get("lastmod", ""),
        "priority": url_obj.get("priority", ""),
        "was_crawled": "yes" if url in crawl_results else "no",
        "internal_link_count": internal_link_count,
        "cta_count": cta_count,
        "ctas": cta_texts,
    })

with open("output/pages.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "url", "section", "depth", "sitemap_source", "lastmod", "priority",
        "was_crawled", "internal_link_count", "cta_count", "ctas"
    ])
    writer.writeheader()
    writer.writerows(pages_rows)

print(f"Written {len(pages_rows)} rows to output/pages.csv")

# ============================================================
# 2. Internal Links CSV - All discovered internal links
# ============================================================
links_rows = []
for source_url, data in crawl_results.items():
    for link in data.get("internal_links", []):
        links_rows.append({
            "source_url": source_url,
            "target_url": link["href"],
            "link_text": link.get("text", ""),
            "is_navigation": link.get("is_nav", False),
        })

with open("output/internal_links.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "source_url", "target_url", "link_text", "is_navigation"
    ])
    writer.writeheader()
    writer.writerows(links_rows)

print(f"Written {len(links_rows)} rows to output/internal_links.csv")

# ============================================================
# 3. CTAs CSV - All discovered CTAs
# ============================================================
cta_rows = []
for source_url, data in crawl_results.items():
    for cta in data.get("ctas", []):
        cta_rows.append({
            "page_url": source_url,
            "cta_text": cta.get("text", ""),
            "cta_target_url": cta["href"],
            "cta_type": cta.get("type", ""),
            "css_classes": cta.get("classes", ""),
        })

with open("output/ctas.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "page_url", "cta_text", "cta_target_url", "cta_type", "css_classes"
    ])
    writer.writeheader()
    writer.writerows(cta_rows)

print(f"Written {len(cta_rows)} rows to output/ctas.csv")

# ============================================================
# 4. Complete JSON - Everything combined
# ============================================================
complete_data = {
    "metadata": {
        "total_pages": len(all_urls),
        "pages_crawled": len(crawl_results),
        "total_internal_links_found": len(links_rows),
        "total_ctas_found": len(cta_rows),
        "sitemap_sources": [
            "https://www.rudderstack.com/sitemap.xml",
            "https://www.rudderstack.com/integration/sitemap.xml",
        ],
    },
    "hierarchy": hierarchy,
    "crawl_results": crawl_results,
    "sections_summary": {},
}

# Build sections summary
sections = {}
for url_obj in all_urls:
    section = get_section(url_obj["url"])
    if section not in sections:
        sections[section] = {"count": 0, "urls": []}
    sections[section]["count"] += 1
    sections[section]["urls"].append(url_obj["url"])

complete_data["sections_summary"] = {
    k: {"count": v["count"], "sample_urls": v["urls"][:10]}
    for k, v in sorted(sections.items(), key=lambda x: -x[1]["count"])
}

with open("output/complete_sitemap_data.json", "w") as f:
    json.dump(complete_data, f, indent=2)

print(f"Written complete JSON to output/complete_sitemap_data.json")

# ============================================================
# 5. Link graph edges JSON (for D3.js visualization)
# ============================================================
# Build a clean link graph from crawl data
edges = []
seen = set()
for source_url, data in crawl_results.items():
    for link in data.get("internal_links", []):
        target = link["href"]
        # Normalize
        source_clean = source_url.rstrip("/") + "/"
        target_clean = target.rstrip("/") + "/" if not target.endswith("/") else target
        key = (source_clean, target_clean)
        if key not in seen:
            seen.add(key)
            is_cta = any(
                c["href"] == link["href"]
                for c in data.get("ctas", [])
            )
            edges.append({
                "source": source_clean,
                "target": target_clean,
                "text": link.get("text", ""),
                "is_nav": link.get("is_nav", False),
                "is_cta": is_cta,
            })

with open("output/link_graph.json", "w") as f:
    json.dump(edges, f, indent=2)

print(f"Written {len(edges)} unique edges to output/link_graph.json")
print("\nDone!")
