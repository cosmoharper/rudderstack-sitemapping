#!/usr/bin/env python3
"""Fetch both RudderStack sitemaps and extract all URLs into a JSON file."""

import urllib.request
import xml.etree.ElementTree as ET
import json
import ssl

# Bypass SSL verification for fetching
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

SITEMAPS = [
    "https://www.rudderstack.com/sitemap.xml",
    "https://www.rudderstack.com/integration/sitemap.xml",
]

all_urls = []

for sitemap_url in SITEMAPS:
    print(f"Fetching {sitemap_url}...")
    req = urllib.request.Request(sitemap_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx) as resp:
        xml_data = resp.read()

    root = ET.fromstring(xml_data)
    # Handle XML namespace
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    urls = []
    for url_elem in root.findall(".//sm:url", ns):
        loc = url_elem.find("sm:loc", ns)
        lastmod = url_elem.find("sm:lastmod", ns)
        changefreq = url_elem.find("sm:changefreq", ns)
        priority = url_elem.find("sm:priority", ns)

        if loc is not None:
            urls.append({
                "url": loc.text.strip(),
                "lastmod": lastmod.text.strip() if lastmod is not None else None,
                "changefreq": changefreq.text.strip() if changefreq is not None else None,
                "priority": priority.text.strip() if priority is not None else None,
                "sitemap_source": sitemap_url.split("/")[-2] if "integration" in sitemap_url else "main",
            })

    print(f"  Found {len(urls)} URLs")
    all_urls.extend(urls)

print(f"\nTotal URLs: {len(all_urls)}")

with open("data/all_urls.json", "w") as f:
    json.dump(all_urls, f, indent=2)

print("Saved to data/all_urls.json")
