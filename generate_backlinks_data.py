#!/usr/bin/env python3
"""Process Ahrefs backlinks CSV into aggregated data for the backlinks visualization."""

import csv
import json
import os
from collections import defaultdict
from urllib.parse import urlparse

INPUT = "data/backlinks_raw.csv"
OUTPUT = "output/backlinks_data.json"

# Read CSV (tab-separated, UTF-8 with BOM)
rows = []
with open(INPUT, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter="\t", quotechar='"')
    for row in reader:
        rows.append(row)

print(f"Total backlinks: {len(rows)}")

# ============================================================
# PARSE AND CLEAN
# ============================================================
backlinks = []
for row in rows:
    ref_url = row.get("Referring page URL", "").strip()
    target_url = row.get("Target URL", "").strip()
    anchor = row.get("Anchor", "").strip()
    dr = row.get("Domain rating", "0").strip()
    ur = row.get("UR", "0").strip()
    page_traffic = row.get("Page traffic", "0").strip()
    domain_traffic = row.get("Domain traffic", "0").strip()
    ref_title = row.get("Referring page title", "").strip()
    link_type = row.get("Type", "").strip()
    nofollow = row.get("Nofollow", "false").strip().lower() == "true"
    ugc = row.get("UGC", "false").strip().lower() == "true"
    sponsored = row.get("Sponsored", "false").strip().lower() == "true"
    is_content = row.get("Content", "false").strip().lower() == "true"
    first_seen = row.get("First seen", "").strip()
    last_seen = row.get("Last seen", "").strip()
    lost = row.get("Lost", "").strip()
    page_type = row.get("Page type", "").strip()
    page_category = row.get("Page category", "").strip()
    ref_domains = row.get("Referring domains", "0").strip()
    language = row.get("Language", "").strip()

    # Parse referring domain
    try:
        ref_domain = urlparse(ref_url).netloc
    except Exception:
        ref_domain = ""

    # Parse target path
    try:
        target_path = urlparse(target_url).path.rstrip("/") or "/"
    except Exception:
        target_path = "/"

    # Safe numeric conversion
    def safe_float(v):
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0

    backlinks.append({
        "ref_url": ref_url,
        "ref_domain": ref_domain,
        "ref_title": ref_title[:120],
        "target_url": target_url,
        "target_path": target_path,
        "anchor": anchor[:200],
        "dr": safe_float(dr),
        "ur": safe_float(ur),
        "page_traffic": safe_float(page_traffic),
        "domain_traffic": safe_float(domain_traffic),
        "link_type": link_type,
        "nofollow": nofollow,
        "ugc": ugc,
        "sponsored": sponsored,
        "is_content": is_content,
        "first_seen": first_seen[:10],
        "last_seen": last_seen[:10],
        "lost": lost[:10] if lost else "",
        "page_type": page_type,
        "page_category": page_category.split(";")[0].strip() if page_category else "",
        "language": language,
    })

print(f"Parsed: {len(backlinks)} backlinks")

# ============================================================
# SECTION CLASSIFICATION (for target URLs)
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

for bl in backlinks:
    bl["target_section"] = get_section(bl["target_path"])

# ============================================================
# 1. OVERALL STATS
# ============================================================
unique_domains = set(bl["ref_domain"] for bl in backlinks)
unique_targets = set(bl["target_path"] for bl in backlinks)
dofollow = [bl for bl in backlinks if not bl["nofollow"]]
live = [bl for bl in backlinks if not bl["lost"]]
lost_links = [bl for bl in backlinks if bl["lost"]]

stats = {
    "total_backlinks": len(backlinks),
    "unique_domains": len(unique_domains),
    "unique_targets": len(unique_targets),
    "dofollow": len(dofollow),
    "nofollow": len(backlinks) - len(dofollow),
    "live": len(live),
    "lost": len(lost_links),
    "text_links": sum(1 for bl in backlinks if bl["link_type"] == "text"),
    "image_links": sum(1 for bl in backlinks if bl["link_type"] == "image"),
    "avg_dr": round(sum(bl["dr"] for bl in backlinks) / len(backlinks), 1) if backlinks else 0,
}
print(f"\nStats: {json.dumps(stats, indent=2)}")

# ============================================================
# 2. TOP TARGET PAGES (most backlinks)
# ============================================================
target_stats = defaultdict(lambda: {"count": 0, "dofollow": 0, "domains": set(), "dr_sum": 0, "traffic_sum": 0, "anchors": defaultdict(int)})
for bl in backlinks:
    t = target_stats[bl["target_path"]]
    t["count"] += 1
    t["domains"].add(bl["ref_domain"])
    t["dr_sum"] += bl["dr"]
    t["traffic_sum"] += bl["page_traffic"]
    if not bl["nofollow"]:
        t["dofollow"] += 1
    if bl["anchor"]:
        t["anchors"][bl["anchor"]] += 1

top_targets = []
for path, t in sorted(target_stats.items(), key=lambda x: -x[1]["count"]):
    top_anchors = sorted(t["anchors"].items(), key=lambda x: -x[1])[:5]
    top_targets.append({
        "path": path,
        "section": get_section(path),
        "backlinks": t["count"],
        "domains": len(t["domains"]),
        "dofollow": t["dofollow"],
        "avg_dr": round(t["dr_sum"] / t["count"], 1) if t["count"] else 0,
        "total_traffic": round(t["traffic_sum"]),
        "top_anchors": [{"text": a, "count": c} for a, c in top_anchors],
    })

print(f"\nTop targets: {len(top_targets)} unique target pages")
for t in top_targets[:5]:
    print(f"  {t['path']}: {t['backlinks']} backlinks from {t['domains']} domains")

# ============================================================
# 3. TOP REFERRING DOMAINS
# ============================================================
domain_stats = defaultdict(lambda: {"count": 0, "dr": 0, "traffic": 0, "targets": set(), "dofollow": 0})
for bl in backlinks:
    d = domain_stats[bl["ref_domain"]]
    d["count"] += 1
    d["dr"] = max(d["dr"], bl["dr"])
    d["traffic"] = max(d["traffic"], bl["domain_traffic"])
    d["targets"].add(bl["target_path"])
    if not bl["nofollow"]:
        d["dofollow"] += 1

top_domains = []
for domain, d in sorted(domain_stats.items(), key=lambda x: -x[1]["dr"]):
    top_domains.append({
        "domain": domain,
        "backlinks": d["count"],
        "dr": d["dr"],
        "traffic": round(d["traffic"]),
        "targets": len(d["targets"]),
        "dofollow": d["dofollow"],
    })

print(f"\nTop domains: {len(top_domains)} unique referring domains")

# ============================================================
# 4. ANCHOR TEXT ANALYSIS
# ============================================================
anchor_counts = defaultdict(lambda: {"count": 0, "domains": set(), "targets": set()})
for bl in backlinks:
    text = bl["anchor"] if bl["anchor"] else "(no anchor / image)"
    a = anchor_counts[text]
    a["count"] += 1
    a["domains"].add(bl["ref_domain"])
    a["targets"].add(bl["target_path"])

top_anchors = []
for text, a in sorted(anchor_counts.items(), key=lambda x: -x[1]["count"]):
    top_anchors.append({
        "text": text,
        "count": a["count"],
        "domains": len(a["domains"]),
        "targets": len(a["targets"]),
    })

print(f"\nUnique anchors: {len(top_anchors)}")

# ============================================================
# 5. BACKLINKS BY SECTION
# ============================================================
section_bl = defaultdict(lambda: {"count": 0, "domains": set(), "dofollow": 0, "targets": set()})
for bl in backlinks:
    s = section_bl[bl["target_section"]]
    s["count"] += 1
    s["domains"].add(bl["ref_domain"])
    s["targets"].add(bl["target_path"])
    if not bl["nofollow"]:
        s["dofollow"] += 1

section_summary = []
for sec in sorted(section_bl, key=lambda x: -section_bl[x]["count"]):
    s = section_bl[sec]
    section_summary.append({
        "section": sec,
        "backlinks": s["count"],
        "domains": len(s["domains"]),
        "targets": len(s["targets"]),
        "dofollow": s["dofollow"],
    })

# ============================================================
# 6. DR DISTRIBUTION
# ============================================================
dr_buckets = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
dr_distribution = []
for i, lo in enumerate(dr_buckets):
    hi = dr_buckets[i + 1] if i + 1 < len(dr_buckets) else 101
    count = sum(1 for bl in backlinks if lo <= bl["dr"] < hi)
    label = f"{lo}-{hi-1}" if hi <= 100 else f"{lo}+"
    dr_distribution.append({"label": label, "min": lo, "count": count})

# ============================================================
# 7. TIMELINE (backlinks by month)
# ============================================================
monthly = defaultdict(int)
for bl in backlinks:
    if bl["first_seen"]:
        month = bl["first_seen"][:7]  # YYYY-MM
        monthly[month] += 1

timeline = [{"month": m, "count": c} for m, c in sorted(monthly.items())]

# ============================================================
# 8. ALL BACKLINKS (for table - keep compact)
# ============================================================
all_backlinks = []
for bl in backlinks:
    all_backlinks.append({
        "ref_domain": bl["ref_domain"],
        "ref_url": bl["ref_url"],
        "ref_title": bl["ref_title"],
        "target_path": bl["target_path"],
        "target_section": bl["target_section"],
        "anchor": bl["anchor"],
        "dr": bl["dr"],
        "ur": bl["ur"],
        "page_traffic": bl["page_traffic"],
        "link_type": bl["link_type"],
        "nofollow": bl["nofollow"],
        "first_seen": bl["first_seen"],
        "last_seen": bl["last_seen"],
        "lost": bl["lost"],
    })

# ============================================================
# WRITE PAYLOAD
# ============================================================
payload = {
    "stats": stats,
    "top_targets": top_targets[:200],
    "top_domains": top_domains[:200],
    "top_anchors": top_anchors[:200],
    "section_summary": section_summary,
    "dr_distribution": dr_distribution,
    "timeline": timeline,
    "all_backlinks": all_backlinks,
}

with open(OUTPUT, "w") as f:
    json.dump(payload, f)

size_mb = os.path.getsize(OUTPUT) / 1024 / 1024
print(f"\nPayload written to {OUTPUT} ({size_mb:.1f} MB)")
