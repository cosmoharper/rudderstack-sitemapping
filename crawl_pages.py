#!/usr/bin/env python3
"""Crawl key RudderStack pages to extract CTAs and internal links."""

import urllib.request
import json
import re
import ssl
import time
import html
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# Priority pages to crawl (core site structure)
PRIORITY_PAGES = [
    # Homepage
    "https://www.rudderstack.com/",
    # Product pages
    "https://www.rudderstack.com/product/event-stream//",
    "https://www.rudderstack.com/product/data-cloud-cdp/",
    "https://www.rudderstack.com/product/reverse-etl/",
    "https://www.rudderstack.com/product/profiles/",
    "https://www.rudderstack.com/product/transformations/",
    "https://www.rudderstack.com/product/data-governance//",
    "https://www.rudderstack.com/product/data-quality-toolkit/",
    "https://www.rudderstack.com/product/compliance-toolkit/",
    "https://www.rudderstack.com/product/sdk-identity-resolution/",
    "https://www.rudderstack.com/product/rudderstack-data-apps//",
    # Core pages
    "https://www.rudderstack.com/pricing/",
    "https://www.rudderstack.com/about/",
    "https://www.rudderstack.com/careers/",
    "https://www.rudderstack.com/contact/",
    "https://www.rudderstack.com/security/",
    "https://www.rudderstack.com/partners/",
    "https://www.rudderstack.com/partnerships/",
    "https://www.rudderstack.com/request-demo/",
    "https://www.rudderstack.com/enterprise-quote/",
    "https://www.rudderstack.com/interactive-demo/",
    "https://www.rudderstack.com/resource-center/",
    # Competitor pages
    "https://www.rudderstack.com/competitors/rudderstack-vs-segment/",
    "https://www.rudderstack.com/competitors/rudderstack-vs-snowplow/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-mparticle/",
    "https://www.rudderstack.com/competitors/rudderstack-vs-tealium/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-hightouch/",
    "https://www.rudderstack.com/competitors/rudderstack-vs-census/",
    "https://www.rudderstack.com/competitors/segment-alternatives/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-freshpaint-cdp/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-treasure-data-cdp/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-blueconic-cdp/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-lytics-cdp/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-tealium-cdp/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-action-iq-cdp/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-optimizely-cdp/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-redpoint-global-cdp/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-acquia-cdp/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-heap-cdp/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-vs-simon-data-cdp/",
    "https://www.rudderstack.com/competitors/hightouch-vs-census/",
    "https://www.rudderstack.com/competitors/segment-vs-tealium/",
    "https://www.rudderstack.com/competitors/segment-vs-mparticle/",
    "https://www.rudderstack.com/competitors/mparticle-vs-tealium/",
    "https://www.rudderstack.com/competitors/snowplow-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/mparticle-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/heap-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/freshpaint-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/census-alternatives/",
    "https://www.rudderstack.com/competitors/blueconic-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/amperity-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/actioniq-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/acquia-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/optimizely-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/treasure-data-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/tealium-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/simon-data-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/lytics-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/redpoint-global-cdp-alternatives/",
    "https://www.rudderstack.com/competitors/hightouch-alternatives/",
    "https://www.rudderstack.com/competitors/rudderstack-cdp-alternatives/",
    # Customer pages
    "https://www.rudderstack.com/customers/",
    # Blog index
    "https://www.rudderstack.com/blog/",
    # Use cases
    "https://www.rudderstack.com/use-case/identity-resolution-alt-11-24/",
    # Partnerships
    "https://www.rudderstack.com/partnerships/bigquery/",
    "https://www.rudderstack.com/partnerships/aws/",
    "https://www.rudderstack.com/rudderstack-and-snowflake/",
    # Legal
    "https://www.rudderstack.com/privacy-policy/",
    "https://www.rudderstack.com/cookie-policy/",
    "https://www.rudderstack.com/master-service-agreement/",
    # Landing / special pages
    "https://www.rudderstack.com/tag-manager-alternative/",
    "https://www.rudderstack.com/replace-google-analytics-4-guide/",
    "https://www.rudderstack.com/do-more-spend-less/",
    "https://www.rudderstack.com/the-identity-resolution-playbook/",
    "https://www.rudderstack.com/realtime-transformations/",
    # Knowledge base
    "https://www.rudderstack.com/learn/",
    # Guides (top index)
    "https://www.rudderstack.com/guides/",
]


class LinkExtractor(HTMLParser):
    """Extract links and CTAs from HTML."""

    CTA_PATTERNS = [
        r'get\s+started', r'sign\s+up', r'try\s+(for\s+)?free', r'start\s+free',
        r'request\s+(a\s+)?demo', r'book\s+(a\s+)?demo', r'schedule\s+(a\s+)?demo',
        r'contact\s+(us|sales)', r'talk\s+to\s+(us|sales|an?\s+expert)',
        r'free\s+trial', r'see\s+pricing', r'view\s+pricing',
        r'learn\s+more', r'read\s+more', r'explore', r'discover',
        r'download', r'watch\s+demo', r'see\s+demo', r'see\s+it\s+in\s+action',
        r'get\s+(a\s+)?quote', r'enterprise\s+quote',
        r'join\s+', r'subscribe', r'register',
    ]

    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []
        self.ctas = []
        self.current_tag = None
        self.current_attrs = {}
        self.current_text = ""
        self.in_a = False
        self.a_href = None
        self.a_classes = ""
        self.a_text_parts = []
        self.nav_links = []
        self.in_nav = False
        self.nav_depth = 0
        self.tag_stack = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.tag_stack.append(tag)

        if tag == "nav":
            self.in_nav = True
            self.nav_depth += 1

        if tag == "a":
            self.in_a = True
            self.a_href = attrs_dict.get("href", "")
            self.a_classes = attrs_dict.get("class", "")
            self.a_text_parts = []

    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

        if tag == "nav":
            self.nav_depth -= 1
            if self.nav_depth <= 0:
                self.in_nav = False
                self.nav_depth = 0

        if tag == "a" and self.in_a:
            self.in_a = False
            link_text = " ".join(self.a_text_parts).strip()
            href = self.a_href or ""

            # Resolve relative URLs
            if href and not href.startswith(("http", "mailto:", "tel:", "javascript:", "#")):
                href = urljoin(self.base_url, href)

            # Only track internal links
            if href and "rudderstack.com" in href:
                link_info = {
                    "href": href.split("?")[0].split("#")[0],  # Clean URL
                    "text": link_text[:200] if link_text else "",
                    "is_nav": self.in_nav,
                }
                self.links.append(link_info)

                # Check if it's a CTA
                combined = f"{link_text} {self.a_classes}".lower()
                is_cta = False
                cta_type = None

                # Check button-like classes
                if any(cls in self.a_classes.lower() for cls in ["btn", "button", "cta", "hero"]):
                    is_cta = True
                    cta_type = "button"

                # Check CTA text patterns
                for pattern in self.CTA_PATTERNS:
                    if re.search(pattern, combined, re.IGNORECASE):
                        is_cta = True
                        cta_type = cta_type or "text-cta"
                        break

                if is_cta:
                    self.ctas.append({
                        "href": link_info["href"],
                        "text": link_text[:200] if link_text else "",
                        "type": cta_type,
                        "classes": self.a_classes[:200],
                    })

            self.a_href = None
            self.a_classes = ""
            self.a_text_parts = []

    def handle_data(self, data):
        if self.in_a:
            self.a_text_parts.append(data.strip())


def crawl_page(url):
    """Fetch a page and extract links and CTAs."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            html_content = resp.read().decode("utf-8", errors="replace")

        parser = LinkExtractor(url)
        parser.feed(html_content)

        # Deduplicate links
        seen_hrefs = set()
        unique_links = []
        for link in parser.links:
            if link["href"] not in seen_hrefs:
                seen_hrefs.add(link["href"])
                unique_links.append(link)

        # Deduplicate CTAs
        seen_ctas = set()
        unique_ctas = []
        for cta in parser.ctas:
            key = (cta["href"], cta["text"])
            if key not in seen_ctas:
                seen_ctas.add(key)
                unique_ctas.append(cta)

        return {
            "url": url,
            "status": "ok",
            "internal_links": unique_links,
            "ctas": unique_ctas,
            "link_count": len(unique_links),
            "cta_count": len(unique_ctas),
        }
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "error": str(e),
            "internal_links": [],
            "ctas": [],
            "link_count": 0,
            "cta_count": 0,
        }


def main():
    results = {}
    total = len(PRIORITY_PAGES)

    for i, url in enumerate(PRIORITY_PAGES):
        print(f"[{i+1}/{total}] Crawling {url}...")
        result = crawl_page(url)
        results[url] = result
        print(f"  -> {result['link_count']} links, {result['cta_count']} CTAs, status: {result['status']}")

        # Be polite
        if i < total - 1:
            time.sleep(0.3)

    # Save results
    with open("data/crawl_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    ok_count = sum(1 for r in results.values() if r["status"] == "ok")
    err_count = sum(1 for r in results.values() if r["status"] == "error")
    total_links = sum(r["link_count"] for r in results.values())
    total_ctas = sum(r["cta_count"] for r in results.values())

    print(f"\n=== CRAWL SUMMARY ===")
    print(f"Pages crawled: {total}")
    print(f"Successful: {ok_count}")
    print(f"Errors: {err_count}")
    print(f"Total internal links found: {total_links}")
    print(f"Total CTAs found: {total_ctas}")

    # Show top CTAs
    all_ctas = []
    for r in results.values():
        for cta in r.get("ctas", []):
            all_ctas.append({**cta, "found_on": r["url"]})

    print(f"\n=== SAMPLE CTAs ===")
    for cta in all_ctas[:30]:
        print(f"  [{cta['type']}] \"{cta['text']}\" -> {cta['href']} (on {cta['found_on']})")


if __name__ == "__main__":
    main()
