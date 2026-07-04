from flask import Flask, render_template, request, jsonify, session, send_file
from scraper import scrape_products, export_products_to_csv, export_products_to_json, export_products_to_excel
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "product-scraper-secret")
app.config["JSON_SORT_KEYS"] = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.form.get("url", "").strip()
    if not url:
        return jsonify({"success": False, "message": "Please enter a valid URL."}), 400

    try:
        products = scrape_products(url)
    except Exception as exc:
        return jsonify({"success": False, "message": f"Scraping failed: {exc}"}), 500

    if not products:
        return jsonify({"success": False, "message": "No products found."}), 404

    session["latest_products"] = products
    export_products_to_csv(products, "products.csv")

    stats = {
        "total_products": len(products),
        "average_price": round(sum(float(item["price_value"]) for item in products) / len(products), 2),
        "highest_price": max(float(item["price_value"]) for item in products),
        "lowest_price": min(float(item["price_value"]) for item in products),
        "categories": len({item["category"] for item in products}),
    }

    return jsonify({
        "success": True,
        "message": "Products extracted successfully.",
        "products": products,
        "stats": stats,
    })


@app.route("/export/<file_type>")
def export_file(file_type):
    products = session.get("latest_products", [])
    if not products:
        return jsonify({"success": False, "message": "No data available to export."}), 404

    if file_type == "csv":
        path = export_products_to_csv(products, "products.csv")
        return send_file(path, mimetype="text/csv", as_attachment=True, download_name="products.csv")

    if file_type == "json":
        path = export_products_to_json(products, "products.json")
        return send_file(path, mimetype="application/json", as_attachment=True, download_name="products.json")

    if file_type == "excel":
        path = export_products_to_excel(products, "products.xlsx")
        return send_file(path, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="products.xlsx")

    return jsonify({"success": False, "message": "Unsupported export type."}), 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
