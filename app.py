from flask import Flask, render_template, request, jsonify
import json, os
from datetime import datetime

app = Flask(__name__)
DB_FILE = "stock.json"

SA_DB = {
 "6001243000123": {"name": "Savanna Dry 330ml", "pack": 24, "bottle": "6001243000017"},
 "6001007000123": {"name": "Heineken 330ml", "pack": 24, "bottle": "6001007000018"},
 "6001008000123": {"name": "Black Label 330ml", "pack": 24, "bottle": "6001008000018"},
 "6001120000123": {"name": "Castle Lite 330ml", "pack": 24, "bottle": "6001120000018"},
}

def load_stock():
    if not os.path.exists(DB_FILE):
        return {"products": {}, "sales_today": 0, "log": []}
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_stock(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def home(): return render_template('sell.html')
@app.route('/sell')
def sell_page(): return render_template('sell.html')
@app.route('/in')
def in_page(): return render_template('in.html')
@app.route('/owner')
def owner_page():
    data = load_stock()
    return render_template('owner.html', data=data)

@app.route('/api/scan', methods=['POST'])
def scan():
    data = load_stock()
    body = request.json
    code = body.get('code')
    mode = body.get('mode')
    qty = int(body.get('qty', 1))
    product = None
    for c, info in SA_DB.items():
        if code == c or code == info['bottle']:
            product = info.copy(); product['case_code']=c; break
    if not product:
        for name, info in data['products'].items():
            if code == info.get('case_code') or code == info.get('bottle_code'):
                product = {"name": name, "pack": info['pack'], "bottle": info.get('bottle_code'), "case_code": info.get('case_code')}
                break
    if not product:
        return jsonify({"status": "unknown", "code": code})
    name = product['name']
    if name not in data['products']:
        data['products'][name] = {"stock": 0, "pack": product['pack'], "case_code": product['case_code'], "bottle_code": product['bottle']}
    if mode == 'in':
        added = product['pack'] * qty
        data['products'][name]['stock'] += added
        data['log'].append(f"{datetime.now().strftime('%H:%M')} IN +{added} {name}")
    else:
        data['products'][name]['stock'] -= qty
        data['sales_today'] += 25 * qty
        data['log'].append(f"{datetime.now().strftime('%H:%M')} SELL -{qty} {name} - Stock: {data['products'][name]['stock']}")
    save_stock(data)
    return jsonify({"status": "ok", "product": name, "stock": data['products'][name]['stock']})

@app.route('/api/learn', methods=['POST'])
def learn():
    data = load_stock()
    body = request.json
    code = body.get('code'); name = body.get('name'); pack = int(body.get('pack', 24))
    data['products'][name] = {"stock": 0, "pack": pack, "case_code": code, "bottle_code": code}
    SA_DB[code] = {"name": name, "pack": pack, "bottle": code}
    save_stock(data)
    return jsonify({"status": "learned"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
