#!/usr/bin/env python3
"""Expanded crawl: all blog, docs, learn, customers, events, top integrations.
Uses concurrent fetching for speed. Merges with existing crawl_results.json."""

import json
import os
import time
import sys
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Reuse the crawl_page function and LinkExtractor from crawl_pages.py
from crawl_pages import crawl_page

# Load all URLs from sitemap
with open("data/all_urls.json") as f:
    all_urls = json.load(f)

# Load existing crawl results to avoid re-crawling
existing = {}
if os.path.exists("data/crawl_results.json"):
    with open("data/crawl_results.json") as f:
        existing = json.load(f)

already_ok = {url for url, d in existing.items() if d.get("status") == "ok"}
print(f"Existing crawl: {len(already_ok)} successful pages")

# Categorize all URLs by section
def get_section(url):
    path = urlparse(url).path
    if path.startswith("/integration/"): return "integrations"
    if path.startswith("/docs/"): return "docs"
    if path.startswith("/blog/"): return "blog"
    if path.startswith("/learn/") or path.startswith("/guides/") or path.startswith("/knowledge-base/"): return "learn"
    if path.startswith("/customers/"): return "customers"
    if path.startswith("/competitors/"): return "competitors"
    if path.startswith("/webinars/") or path.startswith("/events/"): return "events"
    if path.startswith("/product/"): return "product"
    return "other"

by_section = {}
for u in all_urls:
    url = u["url"]
    sec = get_section(url)
    if sec not in by_section:
        by_section[sec] = []
    by_section[sec].append(url)

print("\nSitemap sections:")
for sec in sorted(by_section, key=lambda s: -len(by_section[s])):
    print(f"  {sec:15s}: {len(by_section[sec]):,} pages")

# Build crawl list: all non-integration sections + top 500 integrations
to_crawl = []

# Full crawl of these sections
full_sections = ["blog", "docs", "learn", "customers", "events", "product", "competitors", "other"]
for sec in full_sections:
    for url in by_section.get(sec, []):
        if url not in already_ok:
            to_crawl.append(url)

# Sample integrations: take first 500 alphabetically (they're somewhat representative)
integration_urls = sorted(by_section.get("integrations", []))
integration_sample = [u for u in integration_urls[:500] if u not in already_ok]
to_crawl.extend(integration_sample)

print(f"\nURLs to crawl: {len(to_crawl)}")
print(f"  (skipping {len(already_ok)} already crawled)")

if not to_crawl:
    print("Nothing to crawl!")
    sys.exit(0)

# Concurrent crawl
CONCURRENCY = 10
DELAY_PER_BATCH = 0.5  # politeness delay between batches
results = dict(existing)  # start with existing data
ok_count = 0
err_count = 0
start_time = time.time()

print(f"\nStarting crawl with {CONCURRENCY} concurrent workers...")
print(f"Estimated time: {len(to_crawl) / CONCURRENCY * 1.5 / 60:.0f}-{len(to_crawl) / CONCURRENCY * 2.5 / 60:.0f} minutes\n")

batch_size = CONCURRENCY * 5
for batch_start in range(0, len(to_crawl), batch_size):
    batch = to_crawl[batch_start:batch_start + batch_size]

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = {executor.submit(crawl_page, url): url for url in batch}
        for future in as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
                results[url] = result
                if result["status"] == "ok":
                    ok_count += 1
                else:
                    err_count += 1
            except Exception as e:
                err_count += 1
                results[url] = {"url": url, "status": "error", "error": str(e),
                                "internal_links": [], "ctas": [], "link_count": 0, "cta_count": 0}

    done = batch_start + len(batch)
    elapsed = time.time() - start_time
    rate = done / elapsed if elapsed > 0 else 0
    remaining = (len(to_crawl) - done) / rate if rate > 0 else 0
    total_ok = sum(1 for r in results.values() if r.get("status") == "ok")
    print(f"  [{done}/{len(to_crawl)}] +{ok_count} ok, +{err_count} err | total ok: {total_ok} | {elapsed:.0f}s elapsed, ~{remaining:.0f}s remaining")

    # Brief pause between batches
    if batch_start + batch_size < len(to_crawl):
        time.sleep(DELAY_PER_BATCH)

# Save merged results
with open("data/crawl_results.json", "w") as f:
    json.dump(results, f, indent=2)

elapsed = time.time() - start_time
total_ok = sum(1 for r in results.values() if r.get("status") == "ok")
total_err = sum(1 for r in results.values() if r.get("status") == "error")
total_links = sum(r.get("link_count", 0) for r in results.values())
total_ctas = sum(r.get("cta_count", 0) for r in results.values())

print(f"\n=== EXPANDED CRAWL COMPLETE ===")
print(f"Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
print(f"New pages crawled: {ok_count + err_count}")
print(f"  New ok: {ok_count}, new errors: {err_count}")
print(f"Total results: {total_ok} ok, {total_err} errors")
print(f"Total internal links: {total_links:,}")
print(f"Total CTAs: {total_ctas:,}")
print(f"Saved to data/crawl_results.json")

# Section coverage report
print(f"\n=== COVERAGE BY SECTION ===")
for sec in sorted(by_section, key=lambda s: -len(by_section[s])):
    sec_urls = set(by_section[sec])
    sec_ok = sum(1 for u in sec_urls if results.get(u, {}).get("status") == "ok")
    print(f"  {sec:15s}: {sec_ok:4d} / {len(sec_urls):5d} ({sec_ok/len(sec_urls)*100:5.1f}%)")
