#!/usr/bin/env python3
"""Generate the IA Roadmap data payload — current state vs future state analysis."""

import json
import os
from collections import defaultdict
from urllib.parse import urlparse

# ============================================================
# SECTION CLASSIFICATION (shared with other generators)
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

SECTION_NAMES = {
    "product": "Product", "docs": "Docs", "blog": "Blog", "learn": "Learn",
    "customers": "Customers", "competitors": "Competitors", "integrations": "Integrations",
    "events": "Events", "core": "Core", "other": "Other"
}

def get_section(path):
    path = path.rstrip("/") or "/"
    for key, match_fn in SECTION_RULES:
        if match_fn(path):
            return key
    return "other"

# ============================================================
# LOAD EXISTING DATA
# ============================================================
print("Loading data...")

with open("data/all_urls.json") as f:
    all_urls = json.load(f)
all_url_set = set()
for u in all_urls:
    path = urlparse(u["url"]).path.rstrip("/") or "/"
    all_url_set.add(path)
print(f"  all_urls.json: {len(all_urls)} URLs")

with open("output/links_data.json") as f:
    links_data = json.load(f)
print(f"  links_data.json: {len(links_data.get('sections', []))} sections")

with open("output/backlinks_data.json") as f:
    backlinks_data = json.load(f)
print(f"  backlinks_data.json: {backlinks_data['stats']['total_backlinks']} backlinks")

# ============================================================
# FUTURE STATE CONFIGURATION (from strategy documents)
# ============================================================

TOPIC_HUBS = [
    {
        "id": "warehouse-native-cdp",
        "name": "Warehouse-Native CDP",
        "path": "/topics/warehouse-native-cdp/",
        "phase": 2,
        "target_keywords": ["warehouse-native CDP", "composable CDP", "CDP alternative"],
        "child_pages": [
            {"path": "/topics/warehouse-native-cdp/snowflake-cdp/", "title": "Complete Guide to CDP on Snowflake", "phase": 3},
            {"path": "/topics/warehouse-native-cdp/bigquery-cdp/", "title": "BigQuery as CDP Foundation", "phase": 3},
            {"path": "/topics/warehouse-native-cdp/databricks-cdp/", "title": "Customer Data on Databricks", "phase": 4},
            {"path": "/topics/warehouse-native-cdp/redshift-cdp/", "title": "Redshift CDP Implementation", "phase": 4},
        ],
    },
    {
        "id": "event-streaming",
        "name": "Event Streaming",
        "path": "/topics/event-streaming/",
        "phase": 3,
        "target_keywords": ["real-time event streaming", "event tracking platform"],
        "child_pages": [],
    },
    {
        "id": "reverse-etl",
        "name": "Reverse ETL",
        "path": "/topics/reverse-etl/",
        "phase": 3,
        "target_keywords": ["reverse ETL tools", "reverse ETL + warehouse"],
        "child_pages": [],
    },
    {
        "id": "identity-resolution",
        "name": "Identity Resolution",
        "path": "/topics/identity-resolution/",
        "phase": 3,
        "target_keywords": ["customer 360 platform", "identity resolution"],
        "child_pages": [],
    },
    {
        "id": "data-governance",
        "name": "Data Governance",
        "path": "/topics/data-governance/",
        "phase": 2,
        "target_keywords": ["data governance platform", "event data governance", "AI data governance"],
        "child_pages": [],
    },
    {
        "id": "ai-ml",
        "name": "AI & ML Data",
        "path": "/topics/ai-ml/",
        "phase": 3,
        "target_keywords": ["AI customer data platform", "data platform for AI agents", "AI telemetry"],
        "child_pages": [],
    },
]

COMPARISON_PAGES = [
    {"path": "/competitors/rudderstack-vs-segment/", "title": "RudderStack vs Segment", "phase": 2, "priority": "high"},
    {"path": "/competitors/rudderstack-vs-mparticle/", "title": "RudderStack vs mParticle", "phase": 2, "priority": "high"},
    {"path": "/competitors/rudderstack-vs-tealium/", "title": "RudderStack vs Tealium", "phase": 2, "priority": "high"},
    {"path": "/competitors/rudderstack-vs-hightouch/", "title": "RudderStack vs Hightouch", "phase": 3, "priority": "medium"},
    {"path": "/competitors/rudderstack-vs-census/", "title": "RudderStack vs Census", "phase": 3, "priority": "medium"},
    {"path": "/competitors/segment-alternatives-2026/", "title": "Segment Alternatives 2026", "phase": 3, "priority": "high"},
    {"path": "/competitors/migrate-from-segment/", "title": "Migrate from Segment to RudderStack", "phase": 3, "priority": "medium"},
    {"path": "/competitors/cdp-pricing-comparison/", "title": "CDP Pricing Comparison", "phase": 3, "priority": "medium"},
]

CASE_STUDIES_TO_CONVERT = [
    {"id": "kajabi", "path": "/customers/kajabi/", "title": "Kajabi + RudderStack", "phase": 2},
    {"id": "influxdata", "path": "/customers/influxdata/", "title": "InfluxData + RudderStack", "phase": 2},
    {"id": "grafana", "path": "/customers/grafana/", "title": "Grafana + RudderStack", "phase": 2},
    {"id": "accurx", "path": "/customers/accurx/", "title": "Accurx + RudderStack", "phase": 2},
    {"id": "wynn", "path": "/customers/wynn/", "title": "Wynn Slots + RudderStack", "phase": 2},
    {"id": "wyze", "path": "/customers/wyze/", "title": "Wyze + RudderStack", "phase": 2},
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

CATEGORY_EDUCATION_PAGES = [
    {"path": "/learn/customer-data-management/", "title": "Customer Data Management Guide", "phase": 4},
    {"path": "/learn/cdp-marketing/", "title": "CDP for Marketing Teams", "phase": 4},
    {"path": "/learn/dmp-vs-cdp/", "title": "DMP vs CDP: Complete Comparison", "phase": 4},
    {"path": "/learn/customer-database-platform/", "title": "Customer Database Platform Guide", "phase": 4},
    {"path": "/learn/cdp-platform/", "title": "CDP Platform: What to Evaluate", "phase": 4},
]

TECHNICAL_SEO_TASKS = [
    {"id": "fix_undefined", "title": "301 redirect /undefined/ → homepage", "phase": 1, "priority": "critical", "category": "redirects"},
    {"id": "robots_txt", "title": "Validate and fix robots.txt (403 issue)", "phase": 1, "priority": "critical", "category": "crawling"},
    {"id": "xml_sitemaps", "title": "Create section-level XML sitemaps, submit to GSC", "phase": 1, "priority": "high", "category": "crawling"},
    {"id": "canonical_tags", "title": "Audit and fix canonical tags (blog pagination, integrations)", "phase": 1, "priority": "high", "category": "crawling"},
    {"id": "url_casing", "title": "Normalize /learn/Data/ → /learn/data/ with 301", "phase": 1, "priority": "high", "category": "redirects"},
    {"id": "schema_organization", "title": "Add Organization JSON-LD on homepage", "phase": 1, "priority": "medium", "category": "structured_data"},
    {"id": "schema_breadcrumb", "title": "Add BreadcrumbList schema sitewide", "phase": 1, "priority": "medium", "category": "structured_data"},
    {"id": "schema_article", "title": "Add Article schema to blog/learn pages", "phase": 2, "priority": "medium", "category": "structured_data"},
    {"id": "schema_faq", "title": "Add FAQPage schema to Q&A + comparison pages", "phase": 3, "priority": "medium", "category": "structured_data"},
    {"id": "schema_howto", "title": "Add HowTo schema to integration setup guides", "phase": 3, "priority": "medium", "category": "structured_data"},
    {"id": "schema_event", "title": "Add Event schema to webinars/events pages", "phase": 4, "priority": "low", "category": "structured_data"},
    {"id": "alt_text", "title": "Fix generic alt text on homepage + integrations index", "phase": 1, "priority": "medium", "category": "accessibility"},
    {"id": "cwv_audit", "title": "Core Web Vitals audit and remediation", "phase": 2, "priority": "medium", "category": "performance"},
    {"id": "blog_categories", "title": "Make blog category pages indexable with descriptive copy", "phase": 4, "priority": "medium", "category": "content"},
    {"id": "gsc_setup", "title": "Submit sitemaps to GSC, set up non-brand tracking", "phase": 1, "priority": "high", "category": "crawling"},
    {"id": "nofollow_signup", "title": "Add rel=nofollow to app.rudderstack.com/signup links (preserve link equity)", "phase": 2, "priority": "medium", "category": "linking"},
]

LINKING_RULES = [
    {
        "id": "blog_to_product",
        "rule": "Every blog post links to 3–5 product pages + parent topic hub",
        "source_section": "blog",
        "target_section": "product",
        "min_links_per_page": 3,
        "phase": 2,
        "priority": "high",
    },
    {
        "id": "learn_to_product",
        "rule": "Learn articles link to 2–3 product pages",
        "source_section": "learn",
        "target_section": "product",
        "min_links_per_page": 2,
        "phase": 3,
        "priority": "high",
    },
    {
        "id": "blog_to_hub",
        "rule": "Every blog post links to its parent topic hub",
        "source_section": "blog",
        "target_section": "topics",
        "min_links_per_page": 1,
        "phase": 2,
        "priority": "high",
    },
    {
        "id": "integration_to_hub",
        "rule": "Integration pages link to relevant topic hub + docs",
        "source_section": "integrations",
        "target_section": "topics",
        "min_links_per_page": 1,
        "phase": 3,
        "priority": "medium",
    },
    {
        "id": "integration_cross_link",
        "rule": "Integration pages add 'People also integrate' module",
        "source_section": "integrations",
        "target_section": "integrations",
        "min_links_per_page": 3,
        "phase": 3,
        "priority": "medium",
    },
    {
        "id": "comparison_to_hub",
        "rule": "Comparison pages link to relevant hub + pricing page",
        "source_section": "competitors",
        "target_section": "topics",
        "min_links_per_page": 2,
        "phase": 2,
        "priority": "medium",
    },
    {
        "id": "case_study_to_integrations",
        "rule": "Case studies link to integration pages + product features mentioned",
        "source_section": "customers",
        "target_section": "integrations",
        "min_links_per_page": 2,
        "phase": 2,
        "priority": "medium",
    },
]

# ============================================================
# COMPUTE CURRENT STATE
# ============================================================
print("\nComputing current state...")

section_stats = links_data.get("section_stats", {})
current_sections = {}
for sec_name, stats in section_stats.items():
    current_sections[sec_name] = {
        "pages": stats.get("total_pages", 0),
        "crawled": stats.get("crawled", 0),
        "orphans": stats.get("orphans", 0),
        "orphan_rate": round(stats["orphans"] / max(stats["total_pages"], 1) * 100, 1),
        "avg_inbound_body": round(stats.get("inbound_body", 0) / max(stats.get("crawled", 1), 1), 1),
        "backlinks": 0,  # filled from backlinks_data below
    }

# Add backlink counts per section
for entry in backlinks_data.get("section_summary", []):
    sec = entry.get("section", "")
    if sec in current_sections:
        current_sections[sec]["backlinks"] = entry.get("backlinks", 0)

# Cross-section body link counts
matrix = links_data.get("matrix", [])
cross_links = {}
for m in matrix:
    key = f"{m['source']}_to_{m['target']}"
    cross_links[key] = m.get("body", 0)

# Count existing comparison/hub pages
existing_comparison_count = 0
for path in all_url_set:
    if path.startswith("/competitors/") and "vs" in path.lower():
        existing_comparison_count += 1
existing_hub_count = sum(1 for p in all_url_set if p.startswith("/topics/"))

# /undefined/ backlinks
undefined_backlinks = 0
undefined_domains = 0
for target in backlinks_data.get("top_targets", []):
    if "/undefined" in target.get("path", ""):
        undefined_backlinks = target.get("backlinks", 0)
        undefined_domains = target.get("domains", 0)
        break

# Technical issues
technical_issues = [
    {
        "id": "undefined_bug",
        "title": "/undefined/ absorbing high-authority backlinks",
        "severity": "critical",
        "detail": f"{undefined_backlinks} backlinks from {undefined_domains} domains pointing to /undefined/",
    },
    {
        "id": "orphan_integrations",
        "title": f"{current_sections.get('integrations', {}).get('orphan_rate', 0)}% integration pages are orphans",
        "severity": "critical",
        "detail": f"{current_sections.get('integrations', {}).get('orphans', 0):,} of {current_sections.get('integrations', {}).get('pages', 0):,} integration pages have zero inbound body links",
    },
    {
        "id": "product_invisible",
        "title": "Product pages have near-zero organic visibility",
        "severity": "high",
        "detail": "All organic traffic goes to /learn/ and /blog/, not /product/ or /use-case/",
    },
    {
        "id": "edu_no_product_links",
        "title": "Educational content doesn't link to product pages",
        "severity": "high",
        "detail": f"Blog→Product body links: {cross_links.get('blog_to_product', 0)}, Learn→Product: {cross_links.get('learn_to_product', 0)}",
    },
    {
        "id": "url_casing",
        "title": "Inconsistent URL casing in /learn/",
        "severity": "medium",
        "detail": "/learn/Data/ (capital D) vs /learn/data-analytics/ (lowercase) splits link equity",
    },
]

total_pages = links_data["stats"]["total_pages"]
crawled_pages = links_data["stats"]["crawled_pages"]
orphan_pages = links_data["stats"]["orphan_pages"]

current_state = {
    "total_pages": total_pages,
    "crawled_pages": crawled_pages,
    "orphan_pages": orphan_pages,
    "orphan_rate": round(orphan_pages / max(total_pages, 1) * 100, 1),
    "sections": current_sections,
    "cross_section_body_links": {
        "blog_to_product": cross_links.get("blog_to_product", 0),
        "learn_to_product": cross_links.get("learn_to_product", 0),
        "blog_to_learn": cross_links.get("blog_to_learn", 0),
        "learn_to_blog": cross_links.get("learn_to_blog", 0),
        "blog_to_core": cross_links.get("blog_to_core", 0),
        "learn_to_core": cross_links.get("learn_to_core", 0),
    },
    "technical_issues": technical_issues,
    "comparison_pages_count": existing_comparison_count,
    "topic_hubs_count": existing_hub_count,
    "undefined_backlinks": undefined_backlinks,
    "undefined_domains": undefined_domains,
}
print(f"  Total pages: {total_pages}, Orphans: {orphan_pages} ({current_state['orphan_rate']}%)")
print(f"  Existing comparisons: {existing_comparison_count}, Existing hubs: {existing_hub_count}")
print(f"  /undefined/ backlinks: {undefined_backlinks}")

# ============================================================
# FUTURE STATE (check which pages already exist)
# ============================================================
print("\nBuilding future state...")

def check_exists(path):
    """Check if a path exists in the current sitemap."""
    normalized = path.rstrip("/") or "/"
    return normalized in all_url_set or (normalized + "/") in all_url_set

for hub in TOPIC_HUBS:
    hub["exists"] = check_exists(hub["path"])
    for child in hub.get("child_pages", []):
        child["exists"] = check_exists(child["path"])

for page in COMPARISON_PAGES:
    page["exists"] = check_exists(page["path"])

for cs in CASE_STUDIES_TO_CONVERT:
    cs["exists"] = check_exists(cs["path"])

for qa in QA_PAGES:
    qa["exists"] = check_exists(qa["path"])

for edu in CATEGORY_EDUCATION_PAGES:
    edu["exists"] = check_exists(edu["path"])

future_state = {
    "topic_hubs": TOPIC_HUBS,
    "new_pages": COMPARISON_PAGES,
    "case_studies_to_convert": CASE_STUDIES_TO_CONVERT,
    "qa_pages": QA_PAGES,
    "category_education_pages": CATEGORY_EDUCATION_PAGES,
    "technical_seo_tasks": TECHNICAL_SEO_TASKS,
    "linking_rules": LINKING_RULES,
}

# ============================================================
# GAP ANALYSIS
# ============================================================
print("\nComputing gap analysis...")

pages_to_create = []

# Topic hubs + children
for hub in TOPIC_HUBS:
    if not hub["exists"]:
        pages_to_create.append({
            "path": hub["path"], "title": hub["name"] + " Hub", "type": "topic_hub",
            "phase": hub["phase"], "priority": "high",
        })
    for child in hub.get("child_pages", []):
        if not child["exists"]:
            pages_to_create.append({
                "path": child["path"], "title": child["title"], "type": "warehouse_pillar",
                "phase": child["phase"], "priority": "medium",
            })

# Comparison pages
for page in COMPARISON_PAGES:
    if not page["exists"]:
        pages_to_create.append({
            "path": page["path"], "title": page["title"], "type": "comparison",
            "phase": page["phase"], "priority": page["priority"],
        })

# Q&A pages
for qa in QA_PAGES:
    if not qa["exists"]:
        pages_to_create.append({
            "path": qa["path"], "title": qa["title"], "type": "qa_aeo",
            "phase": qa["phase"], "priority": "medium",
        })

# Category education pages
for edu in CATEGORY_EDUCATION_PAGES:
    if not edu["exists"]:
        pages_to_create.append({
            "path": edu["path"], "title": edu["title"], "type": "education",
            "phase": edu["phase"], "priority": "medium",
        })

# Pages to enhance (top integration pages)
pages_to_enhance = []
top_pages = links_data.get("top_pages", [])
integration_pages = [p for p in top_pages if p.get("section") == "integrations"][:50]
for p in integration_pages:
    pages_to_enhance.append({
        "path": p["path"],
        "type": "integration_enrichment",
        "enhancement": "Add unique content, setup guide, 'People also integrate' module, FAQs",
        "phase": 3,
        "priority": "medium",
        "current_inbound": p.get("inbound_body", 0),
    })

# If we have fewer than 50 integration pages from top_pages, that's fine

# Content conversions (PDF → HTML case studies)
content_conversions = []
for cs in CASE_STUDIES_TO_CONVERT:
    if not cs["exists"]:
        content_conversions.append({
            "path": cs["path"], "title": cs["title"], "type": "pdf_to_html",
            "phase": cs["phase"], "priority": "high",
        })

# Redirects
pages_to_redirect = [
    {"source": "/undefined/", "target": "/", "type": "301", "reason": f"Bug page absorbing {undefined_backlinks} backlinks from {undefined_domains} domains", "phase": 1},
]

gap_summary = {
    "pages_to_create": len(pages_to_create),
    "pages_to_enhance": len(pages_to_enhance),
    "content_conversions": len(content_conversions),
    "redirects": len(pages_to_redirect),
    "technical_fixes": len(TECHNICAL_SEO_TASKS),
    "total_actions": len(pages_to_create) + len(pages_to_enhance) + len(content_conversions) + len(pages_to_redirect) + len(TECHNICAL_SEO_TASKS),
}

gap_analysis = {
    "pages_to_create": pages_to_create,
    "pages_to_enhance": pages_to_enhance,
    "content_conversions": content_conversions,
    "pages_to_redirect": pages_to_redirect,
    "summary": gap_summary,
}
print(f"  Pages to create: {len(pages_to_create)}")
print(f"  Pages to enhance: {len(pages_to_enhance)}")
print(f"  Content conversions: {len(content_conversions)}")
print(f"  Technical fixes: {len(TECHNICAL_SEO_TASKS)}")
print(f"  Total actions: {gap_summary['total_actions']}")

# ============================================================
# PHASES
# ============================================================
print("\nGrouping into phases...")

phase_items = defaultdict(list)

for p in pages_to_create:
    phase_items[p["phase"]].append({**p, "action": "create"})
for p in pages_to_enhance:
    phase_items[p["phase"]].append({**p, "action": "enhance"})
for p in content_conversions:
    phase_items[p["phase"]].append({**p, "action": "convert"})
for p in pages_to_redirect:
    phase_items[p["phase"]].append({**p, "action": "redirect"})
for t in TECHNICAL_SEO_TASKS:
    phase_items[t["phase"]].append({**t, "action": "technical"})

PHASE_DEFS = [
    {"id": 1, "name": "Technical SEO Foundations", "days": "0–14", "description": "Fix critical technical issues. Nothing else compounds until these are resolved."},
    {"id": 2, "name": "Content Foundations", "days": "15–30", "description": "Launch first topic hubs, HTML case studies, comparison pages, and internal linking rules."},
    {"id": 3, "name": "Scale", "days": "31–60", "description": "Remaining hubs, programmatic integration pages (top 50), warehouse pillars, Q&A/AEO pages."},
    {"id": 4, "name": "Compound", "days": "61–90", "description": "Category education pages, remaining integrations, content refresh, ROI calculators."},
]

phases = []
for pdef in PHASE_DEFS:
    items = phase_items.get(pdef["id"], [])
    # Sort: critical first, then high, medium, low
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 2))
    summary = {
        "total": len(items),
        "critical": sum(1 for i in items if i.get("priority") == "critical"),
        "high": sum(1 for i in items if i.get("priority") == "high"),
        "medium": sum(1 for i in items if i.get("priority") == "medium"),
        "low": sum(1 for i in items if i.get("priority") == "low"),
    }
    phases.append({**pdef, "items": items, "summary": summary})
    print(f"  Phase {pdef['id']} ({pdef['name']}): {len(items)} items")

# ============================================================
# SECTION HEALTH SCORECARD
# ============================================================
print("\nComputing section health scores...")

section_scorecard = []
for sec_name in ["product", "docs", "blog", "learn", "customers", "competitors", "integrations", "events", "core", "other"]:
    stats = current_sections.get(sec_name, {"pages": 0, "crawled": 0, "orphans": 0, "orphan_rate": 0, "avg_inbound_body": 0, "backlinks": 0})

    orphan_rate = stats.get("orphan_rate", 0) / 100.0
    crawl_coverage = stats["crawled"] / max(stats["pages"], 1)
    avg_inbound_norm = min(stats.get("avg_inbound_body", 0) / 50.0, 1.0)
    backlinks_norm = min(stats.get("backlinks", 0) / 500.0, 1.0)

    health_score = round(
        30 * (1 - orphan_rate) +
        25 * avg_inbound_norm +
        25 * backlinks_norm +
        20 * crawl_coverage
    )
    health_score = max(0, min(100, health_score))

    # Identify issues
    issues = []
    if orphan_rate > 0.5:
        issues.append(f"{stats['orphan_rate']}% orphan rate")
    if stats.get("avg_inbound_body", 0) < 1:
        issues.append("Very low body inbound links")
    if stats.get("backlinks", 0) < 10:
        issues.append(f"Only {stats['backlinks']} backlinks")
    if crawl_coverage < 0.5 and stats["pages"] > 10:
        issues.append(f"Only {round(crawl_coverage*100)}% crawled")
    if sec_name == "product":
        issues.append("Near-zero organic visibility")
    if sec_name == "integrations":
        issues.append("Missing unique content per page")

    # Identify improvements
    improvements = []
    if sec_name == "integrations":
        improvements.append("Programmatic SEO content (Phase 3–4)")
        improvements.append("Add 'People also integrate' cross-links")
    if sec_name in ("blog", "learn"):
        improvements.append("Add 3–5 product page links per article (Phase 2–3)")
        improvements.append("Link to parent topic hub")
    if sec_name == "product":
        improvements.append("Topic hubs funnel traffic to product (Phase 2)")
        improvements.append("SEO-optimized content on each product page")
    if sec_name == "competitors":
        improvements.append("Create 8 new comparison pages (Phase 2–3)")
    if sec_name == "customers":
        improvements.append("Convert 6 PDF case studies to HTML (Phase 2)")
    if sec_name == "events":
        improvements.append("Add Event schema + transcript content")

    section_scorecard.append({
        "section": sec_name,
        "name": SECTION_NAMES.get(sec_name, sec_name),
        "pages": stats["pages"],
        "crawled": stats["crawled"],
        "orphan_rate": stats.get("orphan_rate", 0),
        "avg_inbound_body": stats.get("avg_inbound_body", 0),
        "backlinks": stats.get("backlinks", 0),
        "health_score": health_score,
        "issues": issues[:3],
        "improvements": improvements[:3],
    })

section_scorecard.sort(key=lambda x: x["health_score"])
print(f"  Scored {len(section_scorecard)} sections (lowest: {section_scorecard[0]['section']} = {section_scorecard[0]['health_score']})")

# ============================================================
# LINKING RECOMMENDATIONS
# ============================================================
print("\nComputing linking recommendations...")

linking_recommendations = []
for rule in LINKING_RULES:
    src = rule["source_section"]
    tgt = rule["target_section"]
    current = cross_links.get(f"{src}_to_{tgt}", 0)

    # Estimate recommended links: source pages * min_links_per_page
    src_pages = current_sections.get(src, {}).get("crawled", 0)
    recommended = src_pages * rule.get("min_links_per_page", 1)
    gap = max(0, recommended - current)

    linking_recommendations.append({
        "id": rule["id"],
        "rule": rule["rule"],
        "source_section": src,
        "target_section": tgt,
        "current_links": current,
        "recommended": recommended,
        "gap": gap,
        "phase": rule["phase"],
        "priority": rule["priority"],
    })

linking_recommendations.sort(key=lambda x: -x["gap"])
for lr in linking_recommendations[:3]:
    print(f"  {lr['source_section']}→{lr['target_section']}: {lr['current_links']} / {lr['recommended']} (gap: {lr['gap']})")

# ============================================================
# TOP-LEVEL STATS
# ============================================================
blog_to_product_gap = next((lr["gap"] for lr in linking_recommendations if lr["id"] == "blog_to_product"), 0)
learn_to_product_gap = next((lr["gap"] for lr in linking_recommendations if lr["id"] == "learn_to_product"), 0)

stats = {
    "total_pages": total_pages,
    "orphan_pages": orphan_pages,
    "orphan_rate": current_state["orphan_rate"],
    "undefined_backlinks": undefined_backlinks,
    "total_actions": gap_summary["total_actions"],
    "pages_to_create": gap_summary["pages_to_create"],
    "pages_to_enhance": gap_summary["pages_to_enhance"],
    "technical_fixes": gap_summary["technical_fixes"],
    "content_conversions": gap_summary["content_conversions"],
    "blog_to_product_gap": blog_to_product_gap,
    "learn_to_product_gap": learn_to_product_gap,
    "current_topic_hubs": existing_hub_count,
    "target_topic_hubs": len(TOPIC_HUBS),
    "current_comparisons": existing_comparison_count,
    "target_comparisons": len(COMPARISON_PAGES),
}

# ============================================================
# WRITE PAYLOAD
# ============================================================
payload = {
    "current_state": current_state,
    "future_state": future_state,
    "gap_analysis": gap_analysis,
    "phases": phases,
    "section_scorecard": section_scorecard,
    "linking_recommendations": linking_recommendations,
    "stats": stats,
}

out_path = "output/roadmap_data.json"
with open(out_path, "w") as f:
    json.dump(payload, f)

size = os.path.getsize(out_path)
print(f"\nPayload written to {out_path} ({size / 1024:.1f} KB)")
print(f"Total actions: {gap_summary['total_actions']}")
