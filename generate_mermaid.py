#!/usr/bin/env python3
"""Generate a Mermaid diagram of the RudderStack site structure.

Mermaid has limits on complexity, so this creates a focused diagram
showing the core site hierarchy with internal links as dotted lines.
"""

import json
from urllib.parse import urlparse

with open("data/all_urls.json") as f:
    all_urls = json.load(f)

with open("data/crawl_results.json") as f:
    crawl_results = json.load(f)

# ============================================================
# Build a summary tree (collapse large sections)
# ============================================================
def parse_path(url):
    path = urlparse(url).path.strip("/")
    if not path:
        return []
    return path.split("/")

# Count pages per top-level section
sections = {}
for url_obj in all_urls:
    segs = parse_path(url_obj["url"])
    if not segs:
        continue
    section = segs[0]
    if section not in sections:
        sections[section] = {"count": 0, "subsections": {}}
    sections[section]["count"] += 1
    if len(segs) > 1:
        sub = segs[1]
        if sub not in sections[section]["subsections"]:
            sections[section]["subsections"][sub] = 0
        sections[section]["subsections"][sub] += 1

# Sanitize IDs for Mermaid
def safe_id(text):
    return text.replace("-", "_").replace("/", "_").replace(".", "_").replace(" ", "_").replace("(", "").replace(")", "").replace("'", "").replace(",", "")

# ============================================================
# Generate Mermaid flowchart
# ============================================================
lines = []
lines.append("```mermaid")
lines.append("flowchart LR")
lines.append("")
lines.append("  %% === RUDDERSTACK.COM SITE MAP ===")
lines.append("  %% 20,016 total pages from 2 sitemaps")
lines.append("  %% Dotted lines = internal links/CTAs discovered via crawling")
lines.append("")

# Root
lines.append('  HOME["<b>rudderstack.com</b><br/>Homepage"]')
lines.append("")

# ---- PRODUCT SECTION ----
lines.append("  %% Product Pages")
lines.append('  PRODUCT["<b>Product</b><br/>12 pages"]')
lines.append("  HOME --> PRODUCT")

product_pages = [
    ("event_stream", "Event Stream", "/product/event-stream/"),
    ("data_cloud_cdp", "Data Cloud CDP", "/product/data-cloud-cdp/"),
    ("reverse_etl", "Reverse ETL", "/product/reverse-etl/"),
    ("profiles", "Profiles", "/product/profiles/"),
    ("transformations", "Transformations", "/product/transformations/"),
    ("data_governance", "Data Governance", "/product/data-governance/"),
    ("data_quality", "Data Quality Toolkit", "/product/data-quality-toolkit/"),
    ("compliance", "Compliance Toolkit", "/product/compliance-toolkit/"),
    ("sdk_identity", "SDK Identity Resolution", "/product/sdk-identity-resolution/"),
    ("data_apps", "Data Apps", "/product/rudderstack-data-apps/"),
]
for pid, pname, ppath in product_pages:
    lines.append(f'  P_{pid}["{pname}"]')
    lines.append(f"  PRODUCT --> P_{pid}")
lines.append("")

# ---- INTEGRATION SECTION ----
lines.append("  %% Integration Pages (19,186 pages)")
lines.append('  INTEGRATION["<b>Integrations</b><br/>19,186 pages<br/>267 categories"]')
lines.append("  HOME --> INTEGRATION")

# Top integration categories by count
int_subs = sections.get("integration", {}).get("subsections", {})
top_ints = sorted(int_subs.items(), key=lambda x: -x[1])[:12]
for name, count in top_ints:
    sid = safe_id(name)
    display = name.replace("-", " ").title()
    lines.append(f'  INT_{sid}["{display}<br/>{count} pages"]')
    lines.append(f"  INTEGRATION --> INT_{sid}")
lines.append(f'  INT_MORE["...+{len(int_subs) - 12} more categories"]')
lines.append("  INTEGRATION --> INT_MORE")
lines.append("")

# ---- COMPETITORS SECTION ----
lines.append("  %% Competitor Pages")
comp_count = sections.get("competitors", {}).get("count", 0)
lines.append(f'  COMPETITORS["<b>Competitors</b><br/>{comp_count} pages"]')
lines.append("  HOME --> COMPETITORS")

comp_groups = {
    "vs_pages": {"label": "VS Comparisons", "pages": []},
    "alt_pages": {"label": "Alternatives", "pages": []},
}
for url_obj in all_urls:
    path = urlparse(url_obj["url"]).path
    if "/competitors/" in path:
        name = path.strip("/").split("/")[-1]
        if "-vs-" in name:
            comp_groups["vs_pages"]["pages"].append(name)
        elif "-alternatives" in name:
            comp_groups["alt_pages"]["pages"].append(name)

lines.append(f'  COMP_VS["VS Comparisons<br/>{len(comp_groups["vs_pages"]["pages"])} pages"]')
lines.append(f'  COMP_ALT["Alternatives<br/>{len(comp_groups["alt_pages"]["pages"])} pages"]')
lines.append("  COMPETITORS --> COMP_VS")
lines.append("  COMPETITORS --> COMP_ALT")
lines.append("")

# ---- BLOG SECTION ----
blog_count = sections.get("blog", {}).get("count", 0)
lines.append(f'  BLOG["<b>Blog</b><br/>{blog_count} pages"]')
lines.append("  HOME --> BLOG")
lines.append('  BLOG_ENG["Engineering"]')
lines.append('  BLOG_PROD["Product"]')
lines.append('  BLOG_CO["Company"]')
lines.append(f'  BLOG_POSTS["{blog_count - 6} posts"]')
lines.append("  BLOG --> BLOG_ENG")
lines.append("  BLOG --> BLOG_PROD")
lines.append("  BLOG --> BLOG_CO")
lines.append("  BLOG --> BLOG_POSTS")
lines.append("")

# ---- CUSTOMERS SECTION ----
cust_count = sections.get("customers", {}).get("count", 0)
lines.append(f'  CUSTOMERS["<b>Customers</b><br/>{cust_count} case studies"]')
lines.append("  HOME --> CUSTOMERS")
lines.append("")

# ---- GUIDES SECTION ----
guide_count = sections.get("guides", {}).get("count", 0)
lines.append(f'  GUIDES["<b>Guides</b><br/>{guide_count} guides"]')
lines.append("  HOME --> GUIDES")
lines.append("")

# ---- KNOWLEDGE BASE ----
kb_count = sections.get("knowledge-base", {}).get("count", 0)
lines.append(f'  KB["<b>Knowledge Base</b><br/>{kb_count} articles"]')
lines.append("  HOME --> KB")
lines.append("")

# ---- RESOURCES ----
lines.append('  RESOURCES["<b>Resources</b><br/>Resource Center"]')
lines.append("  HOME --> RESOURCES")
lines.append("")

# ---- OTHER CORE PAGES ----
lines.append("  %% Core Pages")
core_pages = [
    ("PRICING", "Pricing"),
    ("ABOUT", "About"),
    ("CAREERS", "Careers"),
    ("CONTACT", "Contact"),
    ("SECURITY", "Security"),
    ("PARTNERS", "Partners"),
    ("PARTNERSHIPS", "Partnerships"),
    ("DEMO", "Request Demo"),
    ("ENTERPRISE", "Enterprise Quote"),
    ("INTERACTIVE_DEMO", "Interactive Demo"),
]
for cid, cname in core_pages:
    lines.append(f'  {cid}["{cname}"]')
    lines.append(f"  HOME --> {cid}")
lines.append("")

# ---- LEGAL PAGES ----
lines.append("  %% Legal")
lines.append('  LEGAL["<b>Legal</b>"]')
lines.append("  HOME --> LEGAL")
legal_pages = [
    ("PRIVACY", "Privacy Policy"),
    ("COOKIE", "Cookie Policy"),
    ("MSA", "Master Service Agreement"),
    ("DPA", "Data Privacy Addendum"),
]
for lid, lname in legal_pages:
    lines.append(f'  {lid}["{lname}"]')
    lines.append(f"  LEGAL --> {lid}")
lines.append("")

# ---- LANDING PAGES ----
lines.append("  %% Landing Pages")
lines.append('  LANDING["<b>Landing Pages</b>"]')
lines.append("  HOME --> LANDING")
landing_pages = [
    ("TAG_MGR", "Tag Manager Alternative"),
    ("GA4_REPLACE", "Replace GA4 Guide"),
    ("SAVE_MONEY", "Do More Spend Less"),
    ("ID_PLAYBOOK", "Identity Resolution Playbook"),
    ("RT_TRANSFORM", "Realtime Transformations"),
    ("SNOWFLAKE", "RudderStack + Snowflake"),
]
for lid, lname in landing_pages:
    lines.append(f'  {lid}["{lname}"]')
    lines.append(f"  LANDING --> {lid}")
lines.append("")

# ============================================================
# INTERNAL LINKS & CTAs (dotted lines)
# ============================================================
lines.append("  %% =========================================")
lines.append("  %% INTERNAL LINKS & CTAs (dotted lines)")
lines.append("  %% Discovered via crawling 77 key pages")
lines.append("  %% =========================================")
lines.append("")

# Map URLs to node IDs
url_to_node = {
    "https://www.rudderstack.com/": "HOME",
    "https://www.rudderstack.com/pricing/": "PRICING",
    "https://www.rudderstack.com/about/": "ABOUT",
    "https://www.rudderstack.com/careers/": "CAREERS",
    "https://www.rudderstack.com/contact/": "CONTACT",
    "https://www.rudderstack.com/security/": "SECURITY",
    "https://www.rudderstack.com/partners/": "PARTNERS",
    "https://www.rudderstack.com/partnerships/": "PARTNERSHIPS",
    "https://www.rudderstack.com/request-demo/": "DEMO",
    "https://www.rudderstack.com/enterprise-quote/": "ENTERPRISE",
    "https://www.rudderstack.com/interactive-demo/": "INTERACTIVE_DEMO",
    "https://www.rudderstack.com/customers/": "CUSTOMERS",
    "https://www.rudderstack.com/blog/": "BLOG",
    "https://www.rudderstack.com/resource-center/": "RESOURCES",
    "https://www.rudderstack.com/privacy-policy/": "PRIVACY",
    "https://www.rudderstack.com/cookie-policy/": "COOKIE",
    "https://www.rudderstack.com/integration/": "INTEGRATION",
    "https://www.rudderstack.com/tag-manager-alternative/": "TAG_MGR",
    "https://www.rudderstack.com/replace-google-analytics-4-guide/": "GA4_REPLACE",
    "https://www.rudderstack.com/do-more-spend-less/": "SAVE_MONEY",
    "https://www.rudderstack.com/the-identity-resolution-playbook/": "ID_PLAYBOOK",
    "https://www.rudderstack.com/realtime-transformations/": "RT_TRANSFORM",
    "https://www.rudderstack.com/rudderstack-and-snowflake/": "SNOWFLAKE",
    "https://www.rudderstack.com/competitors/rudderstack-vs-segment/": "COMP_VS",
    "https://www.rudderstack.com/competitors/segment-alternatives/": "COMP_ALT",
}
for pid, pname, ppath in product_pages:
    url_to_node[f"https://www.rudderstack.com{ppath}"] = f"P_{pid}"
    # Also handle double-slash variants
    url_to_node[f"https://www.rudderstack.com{ppath.rstrip('/')}/"] = f"P_{pid}"

# Collect CTA edges from crawl data
cta_edges = set()
internal_edges = set()

for source_url, data in crawl_results.items():
    if data["status"] != "ok":
        continue

    source_norm = source_url.rstrip("/") + "/"
    source_id = url_to_node.get(source_norm) or url_to_node.get(source_url)
    if not source_id:
        continue

    for cta in data.get("ctas", []):
        target_url = cta["href"].rstrip("/") + "/"
        target_id = url_to_node.get(target_url) or url_to_node.get(cta["href"])
        if target_id and target_id != source_id:
            cta_text = cta["text"][:40] if cta["text"] else "CTA"
            cta_edges.add((source_id, target_id, cta_text))

    for link in data.get("internal_links", []):
        if link.get("is_nav"):
            continue
        target_url = link["href"].rstrip("/") + "/"
        target_id = url_to_node.get(target_url) or url_to_node.get(link["href"])
        if target_id and target_id != source_id:
            text = link.get("text", "")[:30]
            internal_edges.add((source_id, target_id, text))

# Emit CTA links
lines.append("  %% CTA Links (amber dotted)")
for source, target, text in sorted(cta_edges):
    label = text.replace('"', "'")
    lines.append(f'  {source} -. "{label}" .-> {target}')
lines.append("")

# Emit internal links (only non-CTA, non-nav, limit to avoid overwhelming)
lines.append("  %% Key Internal Links (purple dotted)")
count = 0
for source, target, text in sorted(internal_edges):
    if (source, target) in {(s, t) for s, t, _ in cta_edges}:
        continue
    if count >= 60:
        break
    if text:
        label = text.replace('"', "'")
        lines.append(f'  {source} -. "{label}" .-> {target}')
    else:
        lines.append(f"  {source} -.-> {target}")
    count += 1
lines.append("")

# ---- STYLING ----
lines.append("  %% Styling")
lines.append("  classDef home fill:#8b5cf6,stroke:#6d28d9,color:#fff,font-weight:bold")
lines.append("  classDef section fill:#1e1b4b,stroke:#4338ca,color:#e0e7ff")
lines.append("  classDef product fill:#1e3a5f,stroke:#3b82f6,color:#bfdbfe")
lines.append("  classDef cta fill:#78350f,stroke:#f59e0b,color:#fef3c7")
lines.append("  classDef legal fill:#1a1a2a,stroke:#555,color:#999")
lines.append("  classDef landing fill:#1a2e1a,stroke:#22c55e,color:#bbf7d0")
lines.append("")
lines.append("  class HOME home")
lines.append("  class PRODUCT,INTEGRATION,COMPETITORS,BLOG,CUSTOMERS,GUIDES,KB,RESOURCES section")

product_ids = ",".join([f"P_{pid}" for pid, _, _ in product_pages])
lines.append(f"  class {product_ids} product")
lines.append("  class DEMO,ENTERPRISE,INTERACTIVE_DEMO cta")
lines.append("  class PRIVACY,COOKIE,MSA,DPA,LEGAL legal")

landing_ids = ",".join([lid for lid, _ in landing_pages])
lines.append(f"  class {landing_ids},LANDING landing")

lines.append("```")

mermaid_text = "\n".join(lines)

with open("output/sitemap_diagram.md", "w") as f:
    f.write(f"# RudderStack.com Site Map Diagram\n\n")
    f.write(f"**Total pages:** 20,016 across 2 sitemaps  \n")
    f.write(f"**Pages crawled:** 77 key pages  \n")
    f.write(f"**Internal links discovered:** 2,862  \n")
    f.write(f"**CTAs discovered:** 724  \n\n")
    f.write(f"Solid lines = site hierarchy. Dotted lines = internal links/CTAs discovered via crawling.\n\n")
    f.write(mermaid_text)
    f.write("\n\n---\n\n")
    f.write("## Section Breakdown\n\n")
    f.write("| Section | Pages | Description |\n")
    f.write("|---------|-------|-------------|\n")
    f.write("| /integration/ | 19,186 | Integration destination pages (267 categories) |\n")
    f.write(f"| /blog/ | {blog_count} | Blog posts and categories |\n")
    f.write(f"| /guides/ | {guide_count} | Technical guides |\n")
    f.write(f"| /competitors/ | {comp_count} | Competitor comparison pages |\n")
    f.write(f"| /customers/ | {cust_count} | Customer case studies |\n")
    f.write(f"| /knowledge-base/ | {kb_count} | Knowledge base articles |\n")
    f.write("| /product/ | 12 | Product feature pages |\n")
    f.write("| Other | ~50 | Core pages, legal, landing pages |\n")

print(f"Written Mermaid diagram to output/sitemap_diagram.md")
print(f"CTA edges: {len(cta_edges)}")
print(f"Internal link edges: {min(count, len(internal_edges))}")
