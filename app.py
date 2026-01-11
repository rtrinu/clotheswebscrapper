from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from sitemaps_util import get_sitemap, filter_product_urls, get_product_urls_only
from webscrape_utils import scrape_all
import csv
import json

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scrape", methods=["POST"])
def scrape():
    target_url = request.form.get("url")

    # Get sitemap + product URLs
    sitemaps = get_sitemap(target_url)

    if not sitemaps:
        print("No sitemaps found (might be missing or blocked).")

    products = []
    if sitemaps:
        products = get_product_urls_only(sitemaps["urls"]) or []

    # Scrape to DataFrame
    df = scrape_all(products, test_mode=True)

    # Save CSV in background (server‑side)
    csv_filename = "scraped_products.csv"
    df.to_csv(csv_filename, index=False)

    # Convert to JSON for response
    json_output = df.head(10).to_json(orient="records", indent=4)

    return jsonify(
        {
            "preview": json.loads(json_output),
            "message": f"CSV saved as {csv_filename}",
            "count": len(df),
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
