from flask import Flask, render_template, request, jsonify
import pandas as pd
from sitemaps_util import get_sitemap, filter_product_urls, get_product_urls_only

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scrape", methods=["POST"])
def scrape():
    target_url = request.form.get("url")
    sitemaps = get_sitemap(target_url)
    if not sitemaps:
        print("No sitemaps found (might be missing or blocked).")
    else:
        products = get_product_urls_only(sitemaps["urls"])
    if not products:
        products = []
    return products


if __name__ == "__main__":
    app.run(debug=True)
