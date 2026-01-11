import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional


def get_sitemap(
    url: str, follow_index: bool = True, timeout: int = 10
) -> Dict[str, any]:

    # Normalize URL
    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # Try to find sitemap
    sitemap_url = url if "sitemap" in url.lower() else urljoin(base_url, "/sitemap.xml")

    results = {"urls": [], "sitemaps": [], "error": None}

    try:
        response = requests.get(
            sitemap_url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SitemapBot/1.0)"},
        )
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)

        # Define namespaces
        namespaces = {
            "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
            "image": "http://www.google.com/schemas/sitemap-image/1.1",
            "news": "http://www.google.com/schemas/sitemap-news/0.9",
        }

        # Check if it's a sitemap index
        sitemap_elements = root.findall(".//sm:sitemap", namespaces)

        if sitemap_elements and follow_index:
            # This is a sitemap index - get all child sitemaps
            for sitemap in sitemap_elements:
                loc = sitemap.find("sm:loc", namespaces)
                if loc is not None and loc.text:
                    results["sitemaps"].append(loc.text)
                    # Recursively fetch each sitemap
                    child_result = get_sitemap(
                        loc.text, follow_index=False, timeout=timeout
                    )
                    results["urls"].extend(child_result["urls"])
                    if child_result["error"]:
                        # Log but don't stop for individual sitemap errors
                        print(
                            f"Warning: Error in child sitemap {loc.text}: {child_result['error']}"
                        )
        else:
            # This is a regular sitemap - extract URLs
            url_elements = root.findall(".//sm:url", namespaces)
            for url_elem in url_elements:
                loc = url_elem.find("sm:loc", namespaces)
                if loc is not None and loc.text:
                    results["urls"].append(loc.text)

            results["sitemaps"].append(sitemap_url)

    except requests.RequestException as e:
        # Try robots.txt as fallback
        try:
            robots_url = urljoin(base_url, "/robots.txt")
            response = requests.get(robots_url, timeout=timeout)
            if response.status_code == 200:
                for line in response.text.split("\n"):
                    if line.lower().startswith("sitemap:"):
                        found_sitemap = line.split(":", 1)[1].strip()
                        return get_sitemap(found_sitemap, follow_index, timeout)
        except:
            pass
        results["error"] = f"Error fetching sitemap: {str(e)}"

    except ET.ParseError as e:
        results["error"] = f"Error parsing XML: {str(e)}"

    return results


def filter_urls(
    urls: List[str],
    pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
) -> List[str]:

    filtered = urls

    if pattern:
        filtered = [u for u in filtered if pattern.lower() in u.lower()]

    if exclude_pattern:
        filtered = [u for u in filtered if exclude_pattern.lower() not in u.lower()]

    return filtered


def filter_product_urls(urls: List[str]) -> Dict[str, List[str]]:

    # Common product page patterns
    product_patterns = [
        "/product",
        "/products",
        "/item",
        "/items",
        "/p/",
        "/shop/product",
        "/pd/",
        "/dp/",
        "/sku",
        "/style",
    ]

    # Common category patterns
    category_patterns = [
        "/category",
        "/categories",
        "/collection",
        "/collections",
        "/shop",
        "/catalog",
        "/browse",
    ]

    # Gender/demographic patterns
    women_patterns = [
        "/women",
        "/womens",
        "/woman",
        "/ladies",
        "/her",
        "/female",
        "/w/",
    ]

    men_patterns = ["/men", "/mens", "/man", "/male", "/him", "/m/"]

    kids_patterns = [
        "/kids",
        "/children",
        "/child",
        "/baby",
        "/toddler",
        "/boys",
        "/girls",
        "/junior",
        "/youth",
    ]

    # Sale patterns
    sale_patterns = [
        "/sale",
        "/clearance",
        "/outlet",
        "/deals",
        "/discount",
        "/promo",
        "/special",
        "/offer",
    ]

    # Patterns to exclude (non-product pages)
    exclude_patterns = [
        "/about",
        "/contact",
        "/help",
        "/faq",
        "/support",
        "/terms",
        "/privacy",
        "/policy",
        "/legal",
        "/blog",
        "/news",
        "/press",
        "/careers",
        "/jobs",
        "/store-locator",
        "/returns",
        "/shipping",
        "/cart",
        "/checkout",
        "/account",
        "/login",
        "/register",
        "/wishlist",
        "/gift-card",
    ]

    categorized = {
        "products": [],
        "categories": [],
        "women": [],
        "men": [],
        "kids": [],
        "sale": [],
        "other": [],
    }

    for url in urls:
        url_lower = url.lower()

        # Skip excluded patterns
        if any(pattern in url_lower for pattern in exclude_patterns):
            continue

        # Check each category (URL can match multiple)
        matched = False

        if any(pattern in url_lower for pattern in product_patterns):
            categorized["products"].append(url)
            matched = True

        if any(pattern in url_lower for pattern in category_patterns):
            categorized["categories"].append(url)
            matched = True

        if any(pattern in url_lower for pattern in women_patterns):
            categorized["women"].append(url)
            matched = True

        if any(pattern in url_lower for pattern in men_patterns):
            categorized["men"].append(url)
            matched = True

        if any(pattern in url_lower for pattern in kids_patterns):
            categorized["kids"].append(url)
            matched = True

        if any(pattern in url_lower for pattern in sale_patterns):
            categorized["sale"].append(url)
            matched = True

        if not matched:
            categorized["other"].append(url)

    return categorized


def get_product_urls_only(urls: List[str]) -> List[str]:
    """
    Convenience function to get only product URLs.

    Args:
        urls: List of URLs to filter

    Returns:
        List of URLs that appear to be product pages
    """
    categorized = filter_product_urls(urls)
    return categorized["products"]
