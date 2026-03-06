#!/usr/bin/env python3
"""Extract header and footer navigation structure from rudderstack.com.

The header nav uses Radix UI with client-side rendering, so dropdown content
is not in the server-side HTML. We define header nav structure manually
(it's stable site architecture) and extract footer nav programmatically.

Output: data/nav_structure.json
"""

import urllib.request
import json
import re
import ssl
from html.parser import HTMLParser

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# ============================================================
# HEADER NAV — defined manually (Radix UI renders dropdowns client-side)
# Source: inspected from rudderstack.com header menu
# ============================================================
HEADER_NAV = [
    {
        "label": "Products",
        "href": None,
        "children": [
            {"label": "Customer Data Platform", "href": "/product/data-cloud-cdp/"},
            {"label": "Event Stream", "href": "/product/event-stream/"},
            {"label": "Profiles", "href": "/product/profiles/"},
            {"label": "Reverse ETL", "href": "/product/reverse-etl/"},
            {"label": "Transformations", "href": "/product/transformations/"},
            {"label": "Data Compliance Toolkit", "href": "/product/compliance-toolkit/"},
            {"label": "Data Quality Toolkit", "href": "/product/data-quality-toolkit/"},
        ],
    },
    {
        "label": "Solutions",
        "href": None,
        "children": [
            {"label": "Customer 360", "href": "/learn/customer-360/"},
            {"label": "Personalization", "href": "/learn/what-is-personalization/"},
            {"label": "Identity Resolution", "href": "/product/sdk-identity-resolution/"},
            {"label": "Data Apps", "href": "/product/rudderstack-data-apps/"},
        ],
    },
    {
        "label": "Integrations",
        "href": None,
        "children": [
            {"label": "Integration Library", "href": "/integration/"},
        ],
    },
    {
        "label": "Docs",
        "href": None,
        "children": [
            {"label": "Documentation", "href": "/docs/"},
            {"label": "Get Started", "href": "/docs/get-started/"},
            {"label": "Sources", "href": "/docs/sources/"},
            {"label": "Destinations", "href": "/docs/destinations/"},
        ],
    },
    {
        "label": "Resources",
        "href": None,
        "children": [
            {"label": "Blog", "href": "/blog/"},
            {"label": "Learning Center", "href": "/learn/"},
            {"label": "Case Studies", "href": "/customers/"},
            {"label": "Events", "href": "/events/"},
            {"label": "Community", "href": "/join-rudderstack-slack-community/"},
        ],
    },
    {
        "label": "Pricing",
        "href": "/pricing/",
        "children": [],
    },
]


# ============================================================
# FOOTER NAV — extracted programmatically from HTML
# ============================================================
class FooterExtractor(HTMLParser):
    """Extract footer navigation columns and links."""

    def __init__(self):
        super().__init__()
        self.in_footer = False
        self.tag_stack = []
        self.in_h3 = False
        self.h3_text = ""
        self.in_a = False
        self.a_href = ""
        self.a_text = []
        self.current_section = None
        self.sections = {}  # section_name -> [links]

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        self.tag_stack.append(tag)

        if tag == "footer":
            self.in_footer = True
        if tag == "h3" and self.in_footer:
            self.in_h3 = True
            self.h3_text = ""
        if tag == "a" and self.in_footer:
            self.in_a = True
            self.a_href = attrs_d.get("href", "")
            self.a_text = []

    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

        if tag == "footer":
            self.in_footer = False

        if tag == "h3" and self.in_h3:
            self.in_h3 = False
            text = self.h3_text.strip()
            if text and text not in self.sections:
                self.current_section = text
                self.sections[text] = []

        if tag == "a" and self.in_a and self.in_footer:
            self.in_a = False
            text = " ".join(self.a_text).strip()
            href = self.a_href

            if text and href:
                # Normalize href
                href = href.split("?")[0].split("#")[0]
                if href.startswith("https://www.rudderstack.com"):
                    href = href.replace("https://www.rudderstack.com", "") or "/"

                if (href.startswith("/") or "rudderstack" in href) and self.current_section:
                    entry = {"label": text, "href": href}
                    if entry not in self.sections[self.current_section]:
                        self.sections[self.current_section].append(entry)

    def handle_data(self, data):
        if self.in_h3:
            self.h3_text += data
        if self.in_a and self.in_footer:
            self.a_text.append(data.strip())


def extract_footer_nav():
    """Fetch homepage and extract footer navigation structure."""
    url = "https://www.rudderstack.com/"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        html_content = resp.read().decode("utf-8", errors="replace")

        parser = FooterExtractor()
        parser.feed(html_content)

        footer_nav = []
        for section, links in parser.sections.items():
            if links:
                footer_nav.append({
                    "label": section,
                    "href": None,
                    "children": links,
                })

        return footer_nav
    except Exception as e:
        print(f"Warning: Failed to extract footer nav: {e}")
        return []


def main():
    print("Extracting navigation structure from rudderstack.com...")

    print("\nHeader nav (manually defined):")
    for item in HEADER_NAV:
        children_count = len(item["children"])
        print(f"  {item['label']}: {children_count} children")
        for child in item["children"]:
            print(f"    {child['label']}: {child['href']}")

    print("\nExtracting footer nav from live site...")
    footer_nav = extract_footer_nav()
    print(f"Footer sections found: {len(footer_nav)}")
    for item in footer_nav:
        print(f"  {item['label']}: {len(item['children'])} children")
        for child in item["children"]:
            print(f"    {child['label']}: {child['href']}")

    result = {
        "header_nav": HEADER_NAV,
        "footer_nav": footer_nav,
    }

    with open("data/nav_structure.json", "w") as f:
        json.dump(result, f, indent=2)

    total_header = sum(len(item["children"]) for item in HEADER_NAV)
    total_footer = sum(len(item["children"]) for item in footer_nav)
    print(f"\nSaved to data/nav_structure.json")
    print(f"  Header: {len(HEADER_NAV)} sections, {total_header} links")
    print(f"  Footer: {len(footer_nav)} sections, {total_footer} links")


if __name__ == "__main__":
    main()
