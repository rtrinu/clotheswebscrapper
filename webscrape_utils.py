import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import time
import numpy as np
import json
import re
from class_selectors import COMMON_SELECTORS
from price_parser import Price

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def find_with_css(soup, selectors):
    for selector in selectors:
        el = soup.select_one(selector)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return None


def extract_json_ld(soup):
    data = {"name": None, "price": None, "brand": None}
    for script in soup.select("script[type='application/ld+json']"):
        try:
            obj = json.loads(script.string)
        except Exception:
            continue
        items = obj if isinstance(obj, list) else [obj]
        for item in items:
            if item.get("@type") == "Product":
                data["name"] = data["name"] or item.get("name")
                if "offers" in item and isinstance(item["offers"], dict):
                    data["price"] = data["price"] or item["offers"].get("price")
                brand = item.get("brand")
                if isinstance(brand, dict):
                    data["brand"] = data["brand"] or brand.get("name")
                elif isinstance(brand, str):
                    data["brand"] = data["brand"] or brand
                return data
    return data


def extract_price_from_text(text: str) -> float | None:
    price = Price.fromstring(text)
    if price.amount is not None:
        try:
            return float(price.amount)
        except ValueError:
            return None
    return None


def scrape_product_auto(url: str) -> dict:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] {url} → {e}")
        return {
            "url": url,
            "name": None,
            "price": None,
            "brand": None,
            "fibre_count": "NA",
        }

    soup = BeautifulSoup(r.text, "html.parser")
    json_data = extract_json_ld(soup)

    name = json_data.get("name") or find_with_css(soup, COMMON_SELECTORS["name"])
    raw_price_text = json_data.get("price") or find_with_css(
        soup, COMMON_SELECTORS["price"]
    )
    price = extract_price_from_text(str(raw_price_text)) if raw_price_text else None

    brand = json_data.get("brand") or find_with_css(soup, COMMON_SELECTORS["brand"])
    fibre_text = find_with_css(soup, COMMON_SELECTORS["fibre_count"])

    if not fibre_text:
        fibre_count = "NA"
    else:
        m = re.search(r"\d+", fibre_text)
        fibre_count = int(m.group()) if m else fibre_text

    return {
        "url": url,
        "name": name,
        "price": price,
        "brand": brand,
        "fibre_count": fibre_count,
    }


def scrape_all(
    urls: list[str], delay: float = 0.5, test_mode: bool = True
) -> pd.DataFrame:
    if test_mode:
        print(f"--- TEST MODE ACTIVE: Scraping first 10 of {len(urls)} URLs ---")
        urls_to_scrape = urls[:10]
    else:
        urls_to_scrape = urls

    rows = []
    for url in tqdm(urls_to_scrape):
        try:
            data = scrape_product_auto(url)
            rows.append(data)
            time.sleep(delay)
        except Exception as e:
            print(f"[ERROR] scraping {url}: {e}")
            continue

    df = pd.DataFrame(rows)
    df.rename(
        columns={
            "name": "Name",
            "price": "Price",
            "brand": "Brand",
            "fibre_count": "Fibre Content",
        },
        inplace=True,
    )

    if not df.empty and pd.api.types.is_numeric_dtype(df["Price"]):
        avg_price = np.nanmean(df["Price"])
        print(f"\nAverage Price for these {len(df)} items: {avg_price:.2f}")

    return df
