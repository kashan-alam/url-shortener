from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# This is set as an environment variable in deployment.yaml
API_URL = os.environ.get("API_URL", "http://localhost")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/shorten", methods=["POST"])
def shorten():
    url = request.form.get("url", "")
    try:
        response = requests.post(
            f"{API_URL}/shorten",
            json={"url": url},
            timeout=5
        )
        data = response.json()
        return render_template("index.html", short_url=data.get("short_url"), original_url=url)
    except Exception as e:
        return render_template("index.html", error=str(e))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)