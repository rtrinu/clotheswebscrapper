import requests
from bs4 import BeautifulSoup
import re
import numpy as np
from urllib.parse import urljoin, urlparse


def find_sitemaps_from_robots(homepage_url):
    # Normalize homepage (strip path/query, keep scheme+netloc)
    parsed = urlparse(homepage_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    sitemap_urls = set()

    # 1) Try to fetch robots.txt
    robots_url = urljoin(base, "/robots.txt")
    try:
        resp = requests.get(
            robots_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}
        )
        if resp.status_code == 200:
            robots_txt = resp.text

            # Parse any "Sitemap:" lines
            matches = re.findall(
                r"(?i)^Sitemap:\s*(https?://[^\s]+)", robots_txt, re.MULTILINE
            )
            for m in matches:
                sitemap_urls.add(m)
    except Exception as e:
        # Could be 403/timeout/etc — ignore and fallback
        pass

    # 2) If nothing was found, try common sitemap locations
    common_paths = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemap-index.xml",
        "/sitemap.xml.gz",
        "/sitemaps/sitemap-index.xml.gz",  # sometimes used by major sites
        "/sitemaps/sitemap.xml.gz",
    ]

    for path in common_paths:
        url = urljoin(base, path)
        try:
            r = requests.head(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            # If HEAD allowed and content type is xml or okay → add
            if r.status_code == 200:
                sitemap_urls.add(url)
        except:
            pass

    return list(sitemap_urls)
