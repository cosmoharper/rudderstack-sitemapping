#!/usr/bin/env python3
"""Fetch all RudderStack sitemaps (auto-discovering from sitemap index) and extract URLs."""

import urllib.request
import xml.etree.ElementTree as ET
import json
import ssl
from urllib.parse import urlparse

# Bypass SSL verification for fetching
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

ENTRY_POINTS = [
    "https://www.rudderstack.com/sitemap.xml",
    # Integration sitemap isn't listed in the index, add it explicitly
    "https://www.rudderstack.com/integration/sitemap.xml",
]


def fetch_xml(url):
    """Fetch and parse XML from a URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        return ET.fromstring(resp.read())


def extract_urls_from_urlset(root, source_label):
    """Extract URL entries from a <urlset> sitemap."""
    urls = []
    for url_elem in root.findall(".//sm:url", NS):
        loc = url_elem.find("sm:loc", NS)
        lastmod = url_elem.find("sm:lastmod", NS)
        changefreq = url_elem.find("sm:changefreq", NS)
        priority = url_elem.find("sm:priority", NS)
        if loc is not None and loc.text:
            urls.append({
                "url": loc.text.strip(),
                "lastmod": lastmod.text.strip() if lastmod is not None else None,
                "changefreq": changefreq.text.strip() if changefreq is not None else None,
                "priority": priority.text.strip() if priority is not None else None,
                "sitemap_source": source_label,
            })
    return urls


def process_sitemap(url, seen=None):
    """Process a sitemap URL — handles both sitemap indexes and URL sets."""
    if seen is None:
        seen = set()
    if url in seen:
        return []
    seen.add(url)

    print(f"Fetching {url}...")
    try:
        root = fetch_xml(url)
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return []

    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag

    # Sitemap index — contains <sitemap> elements pointing to child sitemaps
    if tag == "sitemapindex":
        child_sitemaps = []
        for sm_elem in root.findall(".//sm:sitemap", NS):
            loc = sm_elem.find("sm:loc", NS)
            if loc is not None and loc.text:
                child_sitemaps.append(loc.text.strip())
        print(f"  Sitemap index with {len(child_sitemaps)} child sitemaps")

        all_urls = []
        for child_url in child_sitemaps:
            all_urls.extend(process_sitemap(child_url, seen))
        return all_urls

    # URL set — contains actual page URLs
    elif tag == "urlset":
        # Derive source label from URL path
        path = urlparse(url).path.rstrip("/")
        parts = [p for p in path.split("/") if p and p != "sitemap.xml"]
        source_label = parts[0] if parts else "main"

        urls = extract_urls_from_urlset(root, source_label)
        print(f"  Found {len(urls)} URLs (source: {source_label})")
        return urls

    else:
        print(f"  Unknown root tag: {tag}")
        return []


# Fetch everything
all_urls = []
seen = set()
for entry in ENTRY_POINTS:
    all_urls.extend(process_sitemap(entry, seen))

# Deduplicate by URL (keep first occurrence)
seen_urls = set()
deduped = []
for u in all_urls:
    if u["url"] not in seen_urls:
        seen_urls.add(u["url"])
        deduped.append(u)

print(f"\nTotal URLs: {len(deduped)} (before dedup: {len(all_urls)})")

# Summary by source
sources = {}
for u in deduped:
    s = u["sitemap_source"]
    sources[s] = sources.get(s, 0) + 1
for s, c in sorted(sources.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")

with open("data/all_urls.json", "w") as f:
    json.dump(deduped, f, indent=2)

print(f"\nSaved to data/all_urls.json")
