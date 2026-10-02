from flask import Flask, request, render_template_string, jsonify
import json, os, datetime

app = Flask(__name__)
DB_FILE = "products.json"
SALES_FILE = "sales.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE) as f: return json.load(f)
        except: return {}
    return {}
def save_db(db):
    with open(DB_FILE,'w') as f: json.dump(db,f, indent=2)
def load_sales():
    if os.path.exists(SALES_FILE):
        try:
            with open(SALES_FILE) as f: return json.load(f)
        except: return []
    return []
def save_sales(s):
    with open(SALES_FILE,'w') as f: json.dump(s,f, indent=2)

BASE_CSS = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family: Arial; background:#f5f5f5; margin:0; padding:15px; }
.card{background:white; border-radius:15px; padding:15px; margin-bottom:15px; box-shadow:0 2px 5px #ccc}
.big-btn{display:block; width:100%; padding:22px; font-size:22px; font-weight:bold; border:none; border-radius:12px; margin:12px 0; text-align:center; text-decoration:none; color:white}
.green{background:#16a34a}.blue{background:#2563eb}.orange{background:#ea580c}.black{background:#111}
input{width:100%; padding:16px; font-size:18px; border:2px solid #ddd; border-radius:10px; box-sizing:border-box; margin:8px 0}
h2{margin:10px 0}
</style>
"""

@app.route('/')
def home():
    return render_template_string(BASE_CSS + """
    <h1 style="text-align:center">🍺 GoGo's Spaza</h1>
    <div class="card" style="text-align:center; font-size:18px">System is LIVE ✅</div>
    <a class="big-btn blue" href="/sell">🛒 TILL - SELL</a>
    <a class="big-btn green" href="/in">📦 STOCK IN - Add Stock</a>
    <a class="big-btn orange" href="/owner">👑 OWNER - Low Stock & Profit</a>
    """)

@app.route('/in')
def stock_in():
    return render_template_string(BASE_CSS + """
    <a href="/" class="big-btn black">⬅ HOME</a>
    <div class="card">
    <h2>📦 STOCK IN</h2>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <div id="reader" style="width:100%"></div>
    <input id="barcode" placeholder="Barcode - Scan or Type">
    <input id="name" placeholder="Product Name e.g Savanna 330ml">
    <input id="cost" type="number" placeholder="Cost Price (what you paid) e.g 12">
    <input id="price" type="number" placeholder="Selling Price e.g 18">
    <input id="pack" type="number" placeholder="How many in case? e.g 24" value="24">
    <button onclick="save()" class="big-btn green">✅ SAVE PRODUCT</button>
    <p id="msg" style="font-size:18px;font-weight:bold"></p>
    </div>
    <script>
    function onScan(s){document.getElementById('barcode').value=s; fetch('/get/'+s).then(r=>r.json()).then(d=>{if(d.found){document.getElementById('name').value=d.name;document.getElementById('cost').value=d.cost;document.getElementById('price').value=d.price; msg.innerText='Found: '+d.name+' Stock: '+d.stock}})}
    let h=new Html5Qrcode("reader");h.start({facingMode:"environment"},{fps:10,qrbox:250},onScan);
    function save(){fetch('/save_product',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({barcode:barcode.value,name:name.value,cost:cost.value,price:price.value,pack:pack.value})}).then(r=>r.text()).then(t=>msg.innerText=t)}
    </script>
    """)

@app.route('/get/<barcode>')
def get_product(barcode):
    db=load_db()
    if barcode in db:
        p=db[barcode]
        return jsonify(found=True,name=p['name'],cost=p.get('cost',0),price=p.get('price',0),stock=p.get('stock',0))
    return jsonify(found=False)

@app.route('/save_product', methods=['POST'])
def save_product():
    d=request.json
    db=load_db()
    bc=d['barcode'].strip()
    if not bc: return "No barcode!"
    if bc in db:
        db[bc]['stock']=db[bc].get('stock',0)+int(d['pack'] or 1)
    else:
        db[bc]={'name':d['name'],'cost':float(d['cost'] or 0),'price':float(d['price'] or 0),'stock':int(d['pack'] or 1)}
    db[bc]['name']=d['name']; db[bc]['cost']=float(d['cost'] or 0); db[bc]['price']=float(d['price'] or 0)
    save_db(db)
    return f"✅ Saved {d['name']} @ R{d['price']} Stock now: {db[bc]['stock']}"

@app.route('/sell')
def sell():
    return render_template_string(BASE_CSS + """
    <a href="/" class="big-btn black">⬅ HOME</a>
    <div class="card">
    <h2>🛒 TILL - SCAN TO SELL</h2>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <div id="reader" style="width:100%"></div>
    <div id="cart" style="background:#eee; padding:12px; border-radius:10px; min-height:80px; font-size:18px">No items yet - Scan!</div>
    <h2>Total: R<span id="total">0</span></h2>
    <input id="cash" type="number" placeholder="Cash given by customer" oninput="calcChange()">
    <h2 style="color:green">Change: R<span id="change">0.00</span></h2>
    <button onclick="completeSale()" class="big-btn blue">💰 COMPLETE SALE</button>
    <p id="msg" style="font-weight:bold"></p>
    </div>
    <script>
    let cart=[]; let barcodes=[]; let total=0;
    function addToCart(barcode){
     fetch('/get/'+barcode).then(r=>r.json()).then(d=>{
      if(!d.found){alert('Unknown! Go to STOCK IN to add first'); return;}
      fetch('/sell_item',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({barcode:barcode})}).then(r=>r.json()).then(res=>{
       if(res.error){alert(res.error);return;}
       cart.push({name:res.name,price:res.price,barcode:barcode}); barcodes.push(barcode); total+=res.price; render();
      })
     })
    }
    function render(){let html='';cart.forEach(i=>html+=i.name+' - R'+i.price+'<br>');document.getElementById('cart').innerHTML=html||'No items';document.getElementById('total').innerText=total;calcChange();}
    function calcChange(){let cash=parseFloat(document.getElementById('cash').value||0); document.getElementById('change').innerText=(cash-total).toFixed(2);}
    function onScan(s){addToCart(s);}
    let h=new Html5Qrcode("reader");h.start({facingMode:"environment"},{fps:10,qrbox:250},onScan);
    function completeSale(){if(cart.length==0){alert('Scan items first');return;} fetch('/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cart:cart,barcodes:barcodes,cash:cash.value,total:total})}).then(r=>r.text()).then(t=>{alert(t);cart=[];barcodes=[];total=0;render();cash.value='';})}
    </script>
    """)

@app.route('/sell_item', methods=['POST'])
def sell_item():
    db=load_db()
    bc=request.json['barcode']
    if bc not in db: return jsonify(error="Not found")
    if db[bc].get('stock',0)<=0: return jsonify(error="Out of stock!")
    return jsonify(name=db[bc]['name'],price=db[bc]['price'])

@app.route('/complete', methods=['POST'])
def complete():
    db=load_db(); sales=load_sales()
    data=request.json
    total=data.get('total',0)
    cost_total=0
    for bc in data.get('barcodes',[]):
        if bc in db and db[bc].get('stock',0)>0:
            db[bc]['stock']-=1
            cost_total+=float(db[bc].get('cost',0))
    save_db(db)
    profit=total-cost_total
    sales.append({'time':str(datetime.datetime.now()),'total':total,'profit':profit,'items':data.get('cart',[])})
    save_sales(sales)
    cash=float(data.get('cash') or 0)
    return f"SALE OK! Total R{total} | Profit R{profit:.2f} | Change R{cash-total:.2f}"

@app.route('/owner')
def owner():
    db=load_db(); sales=load_sales()
    low=[f"{v['name']} - ONLY {v.get('stock',0)} left!" for k,v in db.items() if v.get('stock',0)<6]
    today=str(datetime.date.today())
    today_total=sum([s['total'] for s in sales if today in s['time']])
    today_profit=sum([s.get('profit',0) for s in sales if today in s['time']])
    rows=""
    for k,v in db.items():
        rows+=f"<tr><td>{v['name']}</td><td>{v.get('stock',0)}</td><td>R{v.get('price',0)}</td><td><a href='/in'>Edit</a></td></tr>"
    return render_template_string(BASE_CSS + f"""
    <a href="/" class="big-btn black">⬅ HOME</a>
    <div class="card"><h2>👑 Owner Dashboard</h2>
    <h3>Today: R{today_total} Sales | R{today_profit:.2f} Profit</h3>
    <h3 style="color:red">Low Stock (&lt;6):</h3><div>{'<br>'.join(low) or 'All good! ✅'}</div></div>
    <div class="card"><table border=1 width=100% style="border-collapse:collapse"><tr><th>Product</th><th>Stock</th><th>Price</th><th>Edit</th></tr>{rows}</table></div>
    """)

if __name__=='__main__':
    app.run()
