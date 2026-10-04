from flask import Flask, request, render_template_string, jsonify
import json, os, datetime

app = Flask(__name__)
DB_FILE = "products.json"
SALES_FILE = "sales.json"

def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE,'r') as f:
            d=f.read().strip()
            if not d: return {}
            return json.loads(d)
    except: return {}
def save_db(db):
    with open(DB_FILE,'w') as f: json.dump(db,f, indent=2)
def load_sales():
    if not os.path.exists(SALES_FILE): return []
    try:
        with open(SALES_FILE,'r') as f:
            d=f.read().strip()
            if not d: return []
            return json.loads(d)
    except: return []
def save_sales(s):
    with open(SALES_FILE,'w') as f: json.dump(s,f, indent=2)

BASE_CSS = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;background:#fff;color:#111;margin:0;padding:12px}
.card{background:#fff;border:2px solid #eee;border-radius:15px;padding:15px;margin-bottom:12px}
.big-btn{display:block;width:100%;padding:18px;font-size:19px;font-weight:bold;border:none;border-radius:12px;margin:10px 0;text-align:center;text-decoration:none;color:white}
.small-btn{padding:8px 12px;border:none;border-radius:8px;font-weight:bold;cursor:pointer}
.green{background:#16a34a}.blue{background:#2563eb}.orange{background:#ea580c}.black{background:#111}.red{background:#dc2626}
input{width:100%;padding:14px;font-size:18px;border:2px solid #333;border-radius:10px;box-sizing:border-box;margin:8px 0;background:#fff;color:#000}
.item-row{display:flex;justify-content:space-between;align-items:center;padding:8px;border-bottom:1px solid #eee}
</style>
"""

@app.route('/')
def home():
    return render_template_string(BASE_CSS + """
    <h1 style="text-align:center">🥃 LIQUOR SHOP</h1>
    <div class="card" style="text-align:center">System LIVE ✅</div>
    <a class="big-btn blue" href="/sell">🛒 TILL - SELL</a>
    <a class="big-btn green" href="/in">📦 STOCK IN</a>
    <a class="big-btn orange" href="/owner">👑 OWNER</a>
    """)

@app.route('/in')
def stock_in():
    return render_template_string(BASE_CSS + """
    <a href="/" class="big-btn black">⬅ HOME</a>
    <div class="card">
    <h2>📦 STOCK IN - LIQUOR SHOP</h2>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <div id="reader"></div>
    <input id="barcode" placeholder="Barcode">
    <input id="name" placeholder="Product e.g Savanna 330ml">
    <input id="cost" type="number" placeholder="Cost Price">
    <input id="price" type="number" placeholder="Selling Price">
    <input id="pack" type="number" placeholder="Qty in case" value="24">
    <button onclick="save()" class="big-btn green">✅ SAVE</button>
    <p id="msg" style="font-weight:bold;color:green"></p>
    </div>
    <script>
    function onScan(s){document.getElementById('barcode').value=s; fetch('/get/'+s).then(r=>r.json()).then(d=>{if(d.found){name.value=d.name;cost.value=d.cost;price.value=d.price;msg.innerText='Found: '+d.name+' Stock:'+d.stock}})}
    let q=new Html5Qrcode("reader");q.start({facingMode:"environment"},{fps:10,qrbox:250},onScan);
    function save(){msg.innerText='Saving...';fetch('/save_product',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({barcode:barcode.value,name:name.value,cost:cost.value,price:price.value,pack:pack.value})}).then(r=>r.text()).then(t=>msg.innerText=t)}
    </script>
    """)

@app.route('/get/<barcode>')
def get_product(barcode):
    db=load_db()
    if barcode in db:
        p=db[barcode]
        return jsonify(found=True,name=p.get('name',''),cost=p.get('cost',0),price=p.get('price',0),stock=p.get('stock',0))
    return jsonify(found=False)

@app.route('/save_product', methods=['POST'])
def save_product():
    try:
        d=request.get_json()
        bc=str(d.get('barcode','')).strip()
        if not bc: return "❌ Barcode empty!"
        name=d.get('name','No Name').strip() or "No Name"
        cost=float(d.get('cost') or 0); price=float(d.get('price') or 0); pack=int(float(d.get('pack') or 1))
        db=load_db()
        if bc in db: db[bc]['stock']=int(db[bc].get('stock',0))+pack
        else: db[bc]={'name':name,'cost':cost,'price':price,'stock':pack}
        db[bc]['name']=name; db[bc]['cost']=cost; db[bc]['price']=price
        if 'stock' not in db[bc]: db[bc]['stock']=pack
        save_db(db)
        return f"✅ SAVED! {name} @ R{price} Stock: {db[bc]['stock']}"
    except Exception as e:
        return f"Error: {e}",500

@app.route('/sell')
def sell():
    return render_template_string(BASE_CSS + """
    <a href="/" class="big-btn black">⬅ HOME - LIQUOR SHOP</a>
    <div class="card">
    <h2>🛒 TILL - LIQUOR SHOP</h2>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <div id="reader"></div>
    <div id="cart" style="background:#f9f9f9;padding:10px;border-radius:10px;min-height:60px">No items - Scan!</div>
    <h2>Total: R<span id="total">0</span></h2>
    <button onclick="cancelLast()" class="big-btn red">❌ CANCEL LAST ITEM</button>
    <button onclick="clearCart()" class="big-btn black">🗑 CLEAR ALL</button>
    <input id="cash" type="number" placeholder="Cash given" oninput="calc()">
    <h2 style="color:green">Change: R<span id="change">0.00</span></h2>
    <button onclick="done()" class="big-btn blue">💰 COMPLETE SALE</button>
    <p id="msg"></p>
    </div>
    <script>
    let cart=[];let barcodes=[];let total=0;
    function add(bc){
     fetch('/get/'+bc).then(r=>r.json()).then(d=>{
      if(!d.found){alert('Not found! Add in STOCK IN first');return;}
      fetch('/sell_item',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({barcode:bc})}).then(r=>r.json()).then(res=>{
       if(res.error){alert(res.error);return;}
       cart.push({name:res.name,price:res.price,barcode:bc});barcodes.push(bc);total+=res.price;show();
      })
     })
    }
    function show(){
     let html='';
     cart.forEach((it,idx)=>{
       html+=`<div class="item-row"><span>${idx+1}. ${it.name} - R${it.price}</span><button class="small-btn red" onclick="removeOne(${idx})">X</button></div>`;
     });
     document.getElementById('cart').innerHTML=html||'No items - Scan!';
     document.getElementById('total').innerText=total;
     calc();
    }
    function removeOne(idx){
     total-=cart[idx].price;
     cart.splice(idx,1); barcodes.splice(idx,1);
     show();
    }
    function cancelLast(){
     if(cart.length==0)return;
     total-=cart[cart.length-1].price;
     cart.pop(); barcodes.pop();
     show();
    }
    function clearCart(){cart=[];barcodes=[];total=0;show();}
    function calc(){let c=parseFloat(document.getElementById('cash').value||0);document.getElementById('change').innerText=(c-total).toFixed(2);}
    function onScan(s){add(s);}
    let q=new Html5Qrcode("reader");q.start({facingMode:"environment"},{fps:10,qrbox:250},onScan);
    function done(){if(cart.length==0){alert('No items');return;}fetch('/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cart:cart,barcodes:barcodes,cash:cash.value,total:total})}).then(r=>r.text()).then(t=>{alert(t);cart=[];barcodes=[];total=0;show();cash.value='';})}
    </script>
    """)

@app.route('/sell_item', methods=['POST'])
def sell_item():
    db=load_db()
    bc=request.json.get('barcode','')
    if bc not in db: return jsonify(error="Not found")
    if db[bc].get('stock',0)<=0: return jsonify(error="Out of stock!")
    return jsonify(name=db[bc]['name'],price=db[bc]['price'])

@app.route('/complete', methods=['POST'])
def complete():
    db=load_db(); sales=load_sales()
    data=request.json
    total=float(data.get('total',0)); cost=0
    for bc in data.get('barcodes',[]):
        if bc in db and db[bc].get('stock',0)>0:
            db[bc]['stock']-=1
            cost+=float(db[bc].get('cost',0))
    save_db(db)
    profit=total-cost
    sales.append({'time':str(datetime.datetime.now()),'total':total,'profit':profit,'items':data.get('cart',[])})
    save_sales(sales)
    cash=float(data.get('cash') or 0)
    return f"OK! Total R{total} | Profit R{profit:.2f} | Change R{cash-total:.2f}"

@app.route('/owner')
def owner():
    db=load_db(); sales=load_sales()
    today=str(datetime.date.today())
    today_total=sum([s.get('total',0) for s in sales if today in s.get('time','')])
    today_profit=sum([s.get('profit',0) for s in sales if today in s.get('time','')])
    low=[f"{v.get('name')} - {v.get('stock',0)} left" for k,v in db.items() if v.get('stock',0)<6]
    rows="".join([f"<tr><td>{v.get('name')}</td><td>{v.get('stock',0)}</td><td>R{v.get('price',0)}</td></tr>" for v in db.values()])
    return render_template_string(BASE_CSS + f"""
    <a href="/" class="big-btn black">⬅ HOME</a>
    <div class="card"><h2>👑 LIQUOR SHOP - Owner</h2><b>Today: R{today_total} Sales | Profit R{today_profit:.2f}</b><br><br><span style="color:red"><b>Low Stock:</b><br>{'<br>'.join(low) or 'All good ✅'}</span></div>
    <div class="card"><table border=1 width=100%><tr><th>Name</th><th>Stock</th><th>Price</th></tr>{rows}</table></div>
    """)

if __name__=='__main__':
    app.run(host='0.0.0.0', port=10000)
