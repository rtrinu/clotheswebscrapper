from flask import Flask, render_template, request
from backend import find_sitemaps_from_robots
import numpy as np


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scrape", methods=["POST"])
def scrape():
    target_url = request.form.get("url")
    sitemaps = find_sitemaps_from_robots(target_url)
    return sitemaps


if __name__ == "__main__":
    app.run(debug=True)
