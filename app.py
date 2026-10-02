from flask import Flask, render_template, request, jsonify
import json, os, datetime

app = Flask(__name__)
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"products": {}, "barcodes": {}, "sales_today": 0, "log": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
def home():
    return render_template("sell.html")

@app.route("/sell")
def sell_page():
    return render_template("sell.html")

@app.route("/in")
def in_page():
    return render_template("in.html")

@app.route("/owner")
def owner_page():
    data = load_data()
    return render_template("owner.html", data=data)

@app.route("/api/scan", methods=["POST"])
def api_scan():
    j = request.json
    code = j.get("code","").strip()
    mode = j.get("mode","sell")
    qty = int(j.get("qty",1))

    data = load_data()

    if code not in data["barcodes"]:
        return jsonify({"status":"unknown", "code":code})

    prod_name = data["barcodes"][code]
    product = data["products"].get(prod_name)
    if not product:
        return jsonify({"status":"unknown"})

    if mode == "in":
        # qty = cases, product has pack size
        pack = product.get("pack", 1)
        added = qty * pack
        product["stock"] += added
        data["log"].append(f"{datetime.datetime.now().strftime('%H:%M')} IN +{added} {prod_name} (code {code})")
    else:
        # sell 1 bottle at a time
        if product["stock"] <= 0:
            return jsonify({"status":"empty", "product":prod_name})
        product["stock"] -= qty
        data["sales_today"] += 1
        data["log"].append(f"{datetime.datetime.now().strftime('%H:%M')} SOLD 1 {prod_name}")

    save_data(data)
    return jsonify({"status":"ok", "product":prod_name, "stock":product["stock"]})

@app.route("/api/learn", methods=["POST"])
def api_learn():
    j = request.json
    code = j["code"].strip()
    name = j["name"].strip()
    pack = int(j.get("pack",24))

    data = load_data()
    data["barcodes"][code] = name
    if name not in data["products"]:
        data["products"][name] = {"stock":0, "pack":pack}
    else:
        data["products"][name]["pack"] = pack

    data["log"].append(f"LEARNED new barcode {code} as {name} pack {pack}")
    save_data(data)
    return jsonify({"status":"learned"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
