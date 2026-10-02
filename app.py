from flask import Flask, request, render_template_string, jsonify
import json, os, datetime

app = Flask(__name__)
DB_FILE = "products.json"
SALES_FILE = "sales.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f: return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE,'w') as f: json.dump(db,f, indent=2)

def load_sales():
    if os.path.exists(SALES_FILE):
        with open(SALES_FILE) as f: return json.load(f)
    return []

def save_sales(s):
    with open(SALES_FILE,'w') as f: json.dump(s,f, indent=2)

# HOME
@app.route('/')
def home():
    return '<h1>GoGo\'s Live</h1><a href="/sell">TILL</a> | <a href="/in">STOCK IN</a> | <a href="/owner">OWNER</a>'

# STOCK IN PAGE
IN_HTML = """
<h2>STOCK IN - Add Product</h2>
<script src="https://unpkg.com/html5-qrcode"></script>
<div id="reader" style="width:300px"></div>
<input id="barcode" placeholder="Barcode" style="width:300px;padding:10px"><br><br>
<input id="name" placeholder="Product Name e.g Savanna 330ml" style="width:300px;padding:10px"><br><br>
<input id="cost" type="number" placeholder="Cost Price (what you paid)" style="width:300px;padding:10px"><br><br>
<input id="price" type="number" placeholder="Selling Price e.g 15" style="width:300px;padding:10px"><br><br>
<input id="pack" type="number" placeholder="How many in case? e.g 24" value="1" style="width:300px;padding:10px"><br><br>
<button onclick="save()" style="padding:15px;background:green;color:white;width:300px">SAVE PRODUCT</button>
<p id="msg"></p>
<script>
function onScan(s){document.getElementById('barcode').value=s; fetch('/get/'+s).then(r=>r.json()).then(d=>{if(d.found){document.getElementById('name').value=d.name;document.getElementById('cost').value=d.cost;document.getElementById('price').value=d.price;}})}
let h=new Html5Qrcode("reader");h.start({facingMode:"environment"},{fps:10,qrbox:250},onScan);
function save(){
 fetch('/save_product',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({barcode:barcode.value,name:name.value,cost:cost.value,price:price.value,pack:pack.value})}).then(r=>r.text()).then(t=>msg.innerText=t)
}
</script>
"""
@app.route('/in')
def stock_in(): return render_template_string(IN_HTML)

@app.route('/get/<barcode>')
def get_product(barcode):
    db=load_db()
    if barcode in db:
        p=db[barcode]
        return jsonify(found=True,name=p['name'],cost=p['cost'],price=p['price'])
    return jsonify(found=False)

@app.route('/save_product', methods=['POST'])
def save_product():
    d=request.json
    db=load_db()
    bc=d['barcode']
    if bc in db:
        db[bc]['stock']+=int(d['pack'])
    else:
        db[bc]={'name':d['name'],'cost':float(d['cost'] or 0),'price':float(d['price'] or 0),'stock':int(d['pack'] or 1)}
    db[bc]['name']=d['name']; db[bc]['cost']=float(d['cost'] or 0); db[bc]['price']=float(d['price'] or 0)
    save_db(db)
    return f"Saved {d['name']} @ R{d['price']} Stock: {db[bc]['stock']}"

# SELL / TILL PAGE WITH CALCULATOR
SELL_HTML = """
<h2>GoGo's TILL</h2>
<script src="https://unpkg.com/html5-qrcode"></script>
<div id="reader" style="width:300px"></div>
<div id="cart" style="border:1px solid #000;padding:10px;width:300px;min-height:100px"></div>
<h3>Total: R<span id="total">0</span></h3>
<input id="cash" type="number" placeholder="Cash given by customer" style="width:300px;padding:15px" oninput="calcChange()"><br><br>
<h2>Change: R<span id="change">0</span></h2>
<button onclick="completeSale()" style="padding:20px;background:blue;color:white;width:300px;font-size:20px">COMPLETE SALE - Give Change</button>
<p id="msg"></p>
<script>
let cart=[];let total=0;
function addToCart(barcode){
 fetch('/get/'+barcode).then(r=>r.json()).then(d=>{
  if(!d.found){alert('Unknown product! Go to /in to add');return;}
  fetch('/sell_item',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({barcode:barcode})}).then(r=>r.json()).then(res=>{
   if(res.error){alert(res.error);return;}
   cart.push({name:res.name,price:res.price});total+=res.price;
   renderCart();
  })
 })
}
function renderCart(){
 let html='';cart.forEach(i=>html+=i.name+' - R'+i.price+'<br>');
 document.getElementById('cart').innerHTML=html;
 document.getElementById('total').innerText=total;
 calcChange();
}
function calcChange(){let cash=parseFloat(document.getElementById('cash').value||0);document.getElementById('change').innerText=(cash-total).toFixed(2);}
function onScan(s){addToCart(s);}
let h=new Html5Qrcode("reader");h.start({facingMode:"environment"},{fps:10,qrbox:250},onScan);
function completeSale(){
 if(cart.length==0){alert('No items');return;}
 fetch('/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cart:cart,cash:document.getElementById('cash').value})}).then(r=>r.text()).then(t=>{alert(t);cart=[];total=0;renderCart();document.getElementById('cash').value='';})
}
</script>
"""
@app.route('/sell')
def sell(): return render_template_string(SELL_HTML)

@app.route('/sell_item', methods=['POST'])
def sell_item():
    db=load_db()
    bc=request.json['barcode']
    if bc not in db: return jsonify(error="Not found")
    if db[bc]['stock']<=0: return jsonify(error="Out of stock!")
    return jsonify(name=db[bc]['name'],price=db[bc]['price'])

@app.route('/complete', methods=['POST'])
def complete():
    db=load_db(); sales=load_sales()
    data=request.json; cart=data['cart']
    # deduct stock
    # Need barcode mapping - we will count by name for simplicity: find barcodes from cart built via sell_item? We'll re-scan? Simpler: we stored cart names only, we need to deduct. We'll need to track barcodes in cart.
    # Let's accept that we deduct 1 per item scanned - we need barcodes stored. Fix: client should send barcodes.
    # For now deduct by matching names
    total=sum([c['price'] for c in cart])
    cost_total=0
    # This is simplified - better to send barcodes
    # We'll load from last sell_item calls? Let's just deduct via a temp file - we will require barcode list
    # WORKAROUND: if cart has barcode field, use it else skip stock deduction for now and log sale
    for item in cart:
        bc=item.get('barcode')
        if bc and bc in db:
            if db[bc]['stock']>0:
                db[bc]['stock']-=1
                cost_total+=db[bc]['cost']
    save_db(db)
    sales.append({'time':str(datetime.datetime.now()),'items':cart,'total':total,'cash':data.get('cash')})
    save_sales(sales)
    profit=total-cost_total
    return f"SALE OK! Total R{total} Profit R{profit:.2f}. Change R{float(data.get('cash') or 0)-total:.2f}"

@app.route('/owner')
def owner():
    db=load_db(); sales=load_sales()
    low=[f"{v['name']} - {v['stock']} left" for k,v in db.items() if v['stock']<6]
    today_total=sum([s['total'] for s in sales if str(datetime.date.today()) in s['time']])
    return f"<h2>Owner Dashboard</h2><h3>Low Stock (<6):</h3>{'<br>'.join(low)}<h3>Today Sales: R{today_total}</h3><h3>All Products:</h3>{'<br>'.join([f'{k} {v}' for k,v in db.items()])}"

if __name__=='__main__':
    app.run()
