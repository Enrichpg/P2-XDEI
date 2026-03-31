from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel, gettext as _, refresh
from flask_socketio import SocketIO
import logging
import os

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'smart_store.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'super-secret-key' # Required for sessions

db = SQLAlchemy(app)
socketio = SocketIO(app)

def get_locale():
    # 1. Check if lang is in query params (highest priority)
    lang = request.args.get('lang')
    if lang in ['en', 'es']:
        session['lang'] = lang
        return lang

    # 2. Check if lang is in session
    if session.get('lang'):
        return session.get('lang')
    
    # 3. Fallback to accept header or default
    return request.accept_languages.best_match(['en', 'es']) or 'en'

babel = Babel(app, locale_selector=get_locale)

@app.before_request
def before_req():
    refresh()

@app.context_processor
def inject_conf_var():
    return dict(get_locale=get_locale)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'es']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('dashboard'))

# Models
class Shelf(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    store = db.relationship('Store', backref=db.backref('shelves', lazy=True, cascade="all, delete-orphan"))

class Inventory(db.Model):
    __tablename__ = 'inventory'
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    shelf_id = db.Column(db.Integer, db.ForeignKey('shelf.id'), primary_key=True)
    stock = db.Column(db.Integer, default=0)
    store = db.relationship("Store", back_populates="inventory_items")
    product = db.relationship("Product", back_populates="inventory_items")
    shelf = db.relationship("Shelf", backref=db.backref('inventory_items', cascade="all, delete-orphan"))

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    location = db.Column(db.String(200))
    image = db.Column(db.String(255))
    url = db.Column(db.String(255))
    telephone = db.Column(db.String(50))
    countryCode = db.Column(db.String(2))
    capacity = db.Column(db.Integer)
    description = db.Column(db.Text)
    inventory_items = db.relationship("Inventory", back_populates="store", cascade="all, delete-orphan")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(50))
    image = db.Column(db.String(255))
    originCountry = db.Column(db.String(50))
    color = db.Column(db.String(20))
    inventory_items = db.relationship("Inventory", back_populates="product", cascade="all, delete-orphan")

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(255))
    salary = db.Column(db.Float)
    role = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100))
    dateOfContract = db.Column(db.String(50))
    skills = db.Column(db.String(255))
    username = db.Column(db.String(50))
    password = db.Column(db.String(255))
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    store = db.relationship('Store', backref=db.backref('employees', lazy=True))

def seed_data():
    # Only seed if DB is empty
    if Store.query.count() > 0:
        return

    import json

    # Create Products
    products_data = [
        ("Apples", 0.99, "S", "ES", "#FF5733", "/static/img/products/apples.png"),
        ("Bananas", 1.49, "M", "EC", "#FFD700", "/static/img/products/bananas.png"),
        ("Coconuts", 2.99, "M", "PH", "#8B4513", "/static/img/products/coconuts.png"),
        ("Melons", 4.99, "XL", "ES", "#90EE90", "/static/img/products/melons.png"),
        ("Kiwi Fruits", 1.89, "S", "NZ", "#6B8E23", "/static/img/products/kiwi.png"),
        ("Strawberries", 2.49, "S", "ES", "#DC143C", "/static/img/products/strawberries.png"),
        ("Raspberries", 3.29, "S", "FR", "#C71585", "/static/img/products/raspberries.png"),
        ("Pineapples", 1.89, "L", "CR", "#FFA500", "/static/img/products/pineapples.png"),
        ("Oranges", 1.29, "M", "ES", "#FF8C00", "/static/img/products/oranges.png"),
        ("Grapes", 2.19, "S", "IT", "#800080", "/static/img/products/grapes.png")
    ]
    products = []
    for p in products_data:
        prod = Product(name=p[0], price=p[1], size=p[2], originCountry=p[3], color=p[4], image=p[5])
        db.session.add(prod)
        products.append(prod)
    db.session.commit()

    # Create Stores
    stores_data = [
        ("Bösebrücke Einkauf", "Bornholmer Straße 65, 10439 Berlin", "13.3986, 52.5547", "/static/img/stores/store_001.png", "https://bosebrucke.example.com", "+49 30 1234567", "DE", 1500, "Main Berlin flagship store located near the famous Bösebrücke bridge in Prenzlauer Berg."),
        ("Checkpoint Markt", "Friedrichstraße 44, 10969 Berlin", "13.3903, 52.5075", "/static/img/stores/store_002.png", "https://checkpoint.example.com", "+49 30 2345678", "DE", 2200, "Historic Kreuzberg store near Checkpoint Charlie. Specialises in international products."),
        ("East Side Galleria", "Mühlenstrasse 10, 10243 Berlin", "13.4447, 52.5031", "/static/img/stores/store_003.png", "https://eastside.example.com", "+49 30 3456789", "DE", 1800, "Trendy Friedrichshain store adjacent to the East Side Gallery, Berlin art wall landmark."),
        ("Tower Trödelmarkt", "Panoramastraße 1A, 10178 Berlin", "13.4094, 52.5208", "/static/img/stores/store_004.png", "https://tower.example.com", "+49 30 4567890", "DE", 3000, "Premium store in Berlin Mitte, steps from the TV Tower and Museum Island.")
    ]
    stores = []
    for s in stores_data:
        store = Store(name=s[0], address=s[1], location=s[2], image=s[3], url=s[4], telephone=s[5], countryCode=s[6], capacity=s[7], description=s[8])
        db.session.add(store)
        stores.append(store)
    db.session.commit()

    # Create Shelves
    shelf_names = ["Corner Unit", "Wall Unit 1", "Wall Unit 2", "Long Wall Unit"]
    shelves = {}
    for store in stores:
        shelves[store.id] = []
        for name in shelf_names:
            shelf = Shelf(name=name, store_id=store.id)
            db.session.add(shelf)
            shelves[store.id].append(shelf)
    db.session.commit()

    # Create Employees
    employees_data = [
        ("Alice Smith", "https://randomuser.me/api/portraits/women/44.jpg", 2800, "Manager", "alice.smith@bosebrucke.example", "2019-06-15T00:00:00Z", ["MachineryDriving","WritingReports","CustomerRelationships"], "alice", "hashed_alice123", stores[0].id),
        ("Bob Jones", "https://randomuser.me/api/portraits/men/32.jpg", 1900, "Cashier", "bob.jones@checkpoint.example", "2021-03-01T00:00:00Z", ["CustomerRelationships"], "bob", "hashed_bob456", stores[1].id),
        ("Clara Müller", "https://randomuser.me/api/portraits/women/68.jpg", 2100, "StockClerk", "clara.muller@eastside.example", "2020-09-10T00:00:00Z", ["MachineryDriving","WritingReports"], "clara", "hashed_clara789", stores[2].id),
        ("David López", "https://randomuser.me/api/portraits/men/75.jpg", 3200, "Manager", "david.lopez@tower.example", "2018-01-20T00:00:00Z", ["WritingReports","CustomerRelationships"], "david", "hashed_david000", stores[3].id)
    ]
    for e in employees_data:
        emp = Employee(name=e[0], image=e[1], salary=e[2], role=e[3], email=e[4], dateOfContract=e[5], skills=json.dumps(e[6]), username=e[7], password=e[8], store_id=e[9])
        db.session.add(emp)
    db.session.commit()

    # Assign Products to Shelves/Stores (Inventory)
    # Give a subset of products to each shelf so there's at least 4 per shelf
    inv_data = [
        # Store 1 Shelves
        (stores[0].id, products[0].id, shelves[stores[0].id][0].id, 10000),
        (stores[0].id, products[1].id, shelves[stores[0].id][0].id, 8000),
        (stores[0].id, products[2].id, shelves[stores[0].id][0].id, 5000),
        (stores[0].id, products[3].id, shelves[stores[0].id][0].id, 3000),
        (stores[0].id, products[4].id, shelves[stores[0].id][1].id, 12000),
        (stores[0].id, products[5].id, shelves[stores[0].id][1].id, 6000),
        (stores[0].id, products[6].id, shelves[stores[0].id][1].id, 4000),
        (stores[0].id, products[7].id, shelves[stores[0].id][1].id, 7000),
        (stores[0].id, products[8].id, shelves[stores[0].id][2].id, 9000),
        (stores[0].id, products[9].id, shelves[stores[0].id][2].id, 11000),
        (stores[0].id, products[0].id, shelves[stores[0].id][2].id, 5000),
        (stores[0].id, products[1].id, shelves[stores[0].id][2].id, 3000),
        (stores[0].id, products[2].id, shelves[stores[0].id][3].id, 8000),
        (stores[0].id, products[3].id, shelves[stores[0].id][3].id, 2000),
        (stores[0].id, products[4].id, shelves[stores[0].id][3].id, 6000),
        (stores[0].id, products[5].id, shelves[stores[0].id][3].id, 4000),

        # Store 2 Shelves
        (stores[1].id, products[2].id, shelves[stores[1].id][0].id, 5000),
        (stores[1].id, products[3].id, shelves[stores[1].id][0].id, 3000),
        (stores[1].id, products[4].id, shelves[stores[1].id][0].id, 7000),
        (stores[1].id, products[5].id, shelves[stores[1].id][0].id, 9000),
        (stores[1].id, products[6].id, shelves[stores[1].id][1].id, 4000),
        (stores[1].id, products[7].id, shelves[stores[1].id][1].id, 6000),
        (stores[1].id, products[8].id, shelves[stores[1].id][1].id, 8000),
        (stores[1].id, products[9].id, shelves[stores[1].id][1].id, 5000),
        (stores[1].id, products[0].id, shelves[stores[1].id][2].id, 12000),
        (stores[1].id, products[1].id, shelves[stores[1].id][2].id, 8000),
        (stores[1].id, products[2].id, shelves[stores[1].id][2].id, 3000),
        (stores[1].id, products[3].id, shelves[stores[1].id][2].id, 1500),
        (stores[1].id, products[4].id, shelves[stores[1].id][3].id, 9000),
        (stores[1].id, products[5].id, shelves[stores[1].id][3].id, 7000),
        (stores[1].id, products[6].id, shelves[stores[1].id][3].id, 5000),
        (stores[1].id, products[7].id, shelves[stores[1].id][3].id, 3000),

        # Store 3 Shelves
        (stores[2].id, products[0].id, shelves[stores[2].id][0].id, 10000),
        (stores[2].id, products[4].id, shelves[stores[2].id][0].id, 6000),
        (stores[2].id, products[5].id, shelves[stores[2].id][0].id, 4000),
        (stores[2].id, products[6].id, shelves[stores[2].id][0].id, 2000),
        (stores[2].id, products[7].id, shelves[stores[2].id][1].id, 7000),
        (stores[2].id, products[8].id, shelves[stores[2].id][1].id, 5000),
        (stores[2].id, products[9].id, shelves[stores[2].id][1].id, 8000),
        (stores[2].id, products[1].id, shelves[stores[2].id][1].id, 3000),
        (stores[2].id, products[2].id, shelves[stores[2].id][2].id, 4000),
        (stores[2].id, products[3].id, shelves[stores[2].id][2].id, 2500),
        (stores[2].id, products[4].id, shelves[stores[2].id][2].id, 6500),
        (stores[2].id, products[5].id, shelves[stores[2].id][2].id, 5000),
        (stores[2].id, products[6].id, shelves[stores[2].id][3].id, 9000),
        (stores[2].id, products[7].id, shelves[stores[2].id][3].id, 7000),
        (stores[2].id, products[8].id, shelves[stores[2].id][3].id, 11000),
        (stores[2].id, products[9].id, shelves[stores[2].id][3].id, 4000),

        # Store 4 Shelves
        (stores[3].id, products[0].id, shelves[stores[3].id][0].id, 15000),
        (stores[3].id, products[1].id, shelves[stores[3].id][0].id, 10000),
        (stores[3].id, products[8].id, shelves[stores[3].id][0].id, 8000),
        (stores[3].id, products[9].id, shelves[stores[3].id][0].id, 6000),
        (stores[3].id, products[2].id, shelves[stores[3].id][1].id, 7000),
        (stores[3].id, products[3].id, shelves[stores[3].id][1].id, 4000),
        (stores[3].id, products[4].id, shelves[stores[3].id][1].id, 9000),
        (stores[3].id, products[5].id, shelves[stores[3].id][1].id, 5000),
        (stores[3].id, products[6].id, shelves[stores[3].id][2].id, 6000),
        (stores[3].id, products[7].id, shelves[stores[3].id][2].id, 8000),
        (stores[3].id, products[8].id, shelves[stores[3].id][2].id, 12000),
        (stores[3].id, products[9].id, shelves[stores[3].id][2].id, 9000),
        (stores[3].id, products[0].id, shelves[stores[3].id][3].id, 20000),
        (stores[3].id, products[1].id, shelves[stores[3].id][3].id, 15000),
        (stores[3].id, products[2].id, shelves[stores[3].id][3].id, 7000),
        (stores[3].id, products[3].id, shelves[stores[3].id][3].id, 3000)
    ]
    for s_id, p_id, sh_id, stock in inv_data:
        db.session.add(Inventory(store_id=s_id, product_id=p_id, shelf_id=sh_id, stock=stock))
    
    db.session.commit()

# --- ROUTES ---
@app.route('/')
@app.route('/dashboard')
def dashboard():
    stores_count = Store.query.count()
    products_count = Product.query.count()
    employees_count = Employee.query.count()
    stores = Store.query.all()
    products = Product.query.all()
    return render_template('dashboard.html', 
                          stores_count=stores_count, 
                          products_count=products_count, 
                          employees_count=employees_count,
                          stores=stores,
                          products=products)

@app.route('/architecture')
def architecture():
    return render_template('architecture.html')

# --- STORES ---
@app.route('/stores', methods=['GET', 'POST'])
def list_stores():
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('name'):
            return "Missing required fields", 400
        store = Store(name=data['name'], address=data.get('address'), 
                      location=data.get('location'), image=data.get('image'))
        db.session.add(store)
        db.session.commit()
        return {"id": store.id, "name": store.name, "address": store.address, 
                "location": store.location, "image": store.image}, 201
    stores = Store.query.all()
    return render_template('stores.html', stores=stores)

@app.route('/stores/map')
def stores_map():
    stores = Store.query.all()
    return render_template('stores_map.html', stores=stores)

@app.route('/stores/<int:id>', methods=['GET', 'DELETE'])
def store_detail(id):
    store = Store.query.get(id)
    if request.method == 'DELETE':
        if store:
            db.session.delete(store)
            db.session.commit()
            return {"message": "Store deleted"}, 200
        return {"error": "Store not found"}, 404
    if not store:
        return "Store not found", 404
    all_products = Product.query.all()
    
    temperature = None
    relativeHumidity = None
    tweets = []
    
    import data_layer
    if getattr(data_layer, 'USE_ORION', False):
        import orion
        urn = f"urn:ngsi-ld:Store:{store.id:03d}"
        try:
            orion_store = orion.get_store(urn)
            if orion_store:
                temp_obj = orion_store.get('temperature', {})
                if 'value' in temp_obj:
                    temperature = temp_obj['value']
                    
                hum_obj = orion_store.get('relativeHumidity', {})
                if 'value' in hum_obj:
                    relativeHumidity = hum_obj['value']
                    
                tweets_obj = orion_store.get('tweets', {})
                t_val = tweets_obj.get('value', [])
                if isinstance(t_val, list):
                    tweets = t_val
        except Exception as e:
            app.logger.warning("Could not fetch context for %s: %s", urn, e)
            
    return render_template('store_detail.html', store=store, all_products=all_products,
                           temperature=temperature, relativeHumidity=relativeHumidity, tweets=tweets)

@app.route('/stores/new', methods=['GET', 'POST'])
def create_store():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        location = request.form.get('location')
        image = request.form.get('image')
        url = request.form.get('url')
        telephone = request.form.get('telephone')
        countryCode = request.form.get('countryCode')
        capacity = request.form.get('capacity')
        description = request.form.get('description')
        
        if not name or len(name) < 2:
            flash(_('El nombre es obligatorio y debe tener al menos 2 caracteres.'), 'error')
            return render_template('store_form.html', store=None)
            
        store = Store(name=name, address=address, location=location, image=image,
                     url=url, telephone=telephone, countryCode=countryCode,
                     capacity=int(capacity) if capacity else None, description=description)
        db.session.add(store)
        db.session.commit()
        flash(_('Store created successfully!'), 'success')
        return redirect(url_for('list_stores'))
    return render_template('store_form.html', store=None)

@app.route('/stores/edit/<int:id>', methods=['GET', 'POST'])
def edit_store(id):
    store = Store.query.get(id)
    if not store:
        flash(_('Store not found.'), 'error')
        return redirect(url_for('list_stores'))
    if request.method == 'POST':
        name = request.form.get('name')
        if not name or len(name) < 2:
            flash(_('El nombre es obligatorio y debe tener al menos 2 caracteres.'), 'error')
            return render_template('store_form.html', store=store)

        store.name = name
        store.address = request.form.get('address')
        store.location = request.form.get('location')
        store.image = request.form.get('image')
        store.url = request.form.get('url')
        store.telephone = request.form.get('telephone')
        store.countryCode = request.form.get('countryCode')
        cap = request.form.get('capacity')
        store.capacity = int(cap) if cap else None
        store.description = request.form.get('description')
        db.session.commit()
        flash(_('Store updated successfully!'), 'success')
        return redirect(url_for('store_detail', id=id))
    return render_template('store_form.html', store=store)

@app.route('/stores/delete/<int:id>', methods=['POST'])
def delete_store(id):
    store = Store.query.get(id)
    if store:
        db.session.delete(store)
        db.session.commit()
    return redirect(url_for('list_stores'))

# --- PRODUCTS ---
@app.route('/products', methods=['GET', 'POST'])
def list_products():
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('name') or not data.get('price'):
            return "Missing required fields", 400
        if not isinstance(data.get('price'), (int, float)):
            return "Invalid price type", 400
        product = Product(name=data['name'], price=data['price'], size=data.get('size'),
                          originCountry=data.get('originCountry'), image=data.get('image'))
        db.session.add(product)
        db.session.commit()
        return {"id": product.id, "name": product.name, "price": product.price,
                "size": product.size, "originCountry": product.originCountry, "image": product.image}, 201
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/products/<int:id>')
def product_detail(id):
    product = Product.query.get(id)
    if not product:
        return "Product not found", 404
    all_stores = Store.query.all()
    return render_template('product_detail.html', product=product, all_stores=all_stores)

@app.route('/products/new', methods=['GET', 'POST'])
def create_product():
    if request.method == 'POST':
        name = request.form.get('name')
        try:
            price = float(request.form.get('price', 0))
        except ValueError:
            price = 0
            
        size = request.form.get('size')
        originCountry = request.form.get('originCountry')
        image = request.form.get('image')
        color = request.form.get('color')
        
        if not name or price <= 0:
            flash(_('El nombre es obligatorio y el precio debe ser mayor a 0.'), 'error')
            return render_template('product_form.html', product=None)
            
        product = Product(name=name, price=price, size=size, originCountry=originCountry, image=image, color=color)
        db.session.add(product)
        db.session.commit()
        flash(_('Product created successfully!'), 'success')
        return redirect(url_for('list_products'))
    return render_template('product_form.html', product=None)

@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    product = Product.query.get(id)
    if not product:
        flash(_('Product not found.'), 'error')
        return redirect(url_for('list_products'))
    if request.method == 'POST':
        name = request.form.get('name')
        try:
            price = float(request.form.get('price', 0))
        except ValueError:
            price = 0
            
        if not name or price <= 0:
            flash(_('El nombre es obligatorio y el precio debe ser mayor a 0.'), 'error')
            return render_template('product_form.html', product=product)

        product.name = name
        product.price = price
        product.size = request.form.get('size')
        product.originCountry = request.form.get('originCountry')
        product.image = request.form.get('image')
        product.color = request.form.get('color')
        db.session.commit()
        flash(_('Product updated successfully!'), 'success')
        return redirect(url_for('product_detail', id=id))
    return render_template('product_form.html', product=product)

@app.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
    return redirect(url_for('list_products'))

# --- INVENTORY & SHELVES ---
@app.route('/stores/inventory/add/<int:store_id>', methods=['POST'])
def add_to_inventory(store_id):
    product_id = request.form.get('product_id', type=int)
    stock = request.form.get('stock', default=0, type=int)
    if product_id:
        # Try to find an existing Inventory row for this store+product (any shelf)
        item = Inventory.query.filter_by(store_id=store_id, product_id=product_id).first()
        if item:
            item.stock += stock
        else:
            # Need a shelf_id for the composite PK — use the store's first shelf
            shelf = Shelf.query.filter_by(store_id=store_id).first()
            if shelf:
                item = Inventory(store_id=store_id, product_id=product_id,
                                 shelf_id=shelf.id, stock=stock)
                db.session.add(item)
        db.session.commit()
    return redirect(url_for('store_detail', id=store_id))

@app.route('/stores/inventory/edit/<int:store_id>/<int:product_id>', methods=['POST'])
def edit_inventory(store_id, product_id):
    stock = request.form.get('stock', type=int)
    item = Inventory.query.filter_by(store_id=store_id, product_id=product_id).first()
    if item:
        item.stock = stock
        db.session.commit()
    return redirect(url_for('store_detail', id=store_id))

@app.route('/stores/inventory/delete/<int:store_id>/<int:product_id>', methods=['POST'])
def delete_from_inventory(store_id, product_id):
    item = Inventory.query.filter_by(store_id=store_id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('store_detail', id=store_id))

@app.route('/products/inventory/add/<int:product_id>', methods=['POST'])
def add_product_to_store(product_id):
    store_id = request.form.get('store_id', type=int)
    stock = request.form.get('stock', default=0, type=int)
    if store_id:
        # Try to find an existing Inventory row for this store+product (any shelf)
        item = Inventory.query.filter_by(store_id=store_id, product_id=product_id).first()
        if item:
            item.stock += stock
        else:
            # Need a shelf_id for the composite PK — use the store's first shelf
            shelf = Shelf.query.filter_by(store_id=store_id).first()
            if shelf:
                item = Inventory(store_id=store_id, product_id=product_id,
                                 shelf_id=shelf.id, stock=stock)
                db.session.add(item)
        db.session.commit()
    return redirect(url_for('product_detail', id=product_id))

@app.route('/stores/<int:store_id>/shelves/new', methods=['POST'])
def create_shelf(store_id):
    name = request.form.get('name')
    if name:
        shelf = Shelf(store_id=store_id, name=name)
        db.session.add(shelf)
        db.session.commit()
    return redirect(url_for('store_detail', id=store_id))

@app.route('/stores/<int:store_id>/shelves/edit/<int:shelf_id>', methods=['POST'])
def edit_shelf(store_id, shelf_id):
    name = request.form.get('name')
    shelf = Shelf.query.get(shelf_id)
    if shelf:
        shelf.name = name
        db.session.commit()
    return redirect(url_for('store_detail', id=store_id))

@app.route('/stores/<int:store_id>/shelves/delete/<int:shelf_id>', methods=['POST'])
def delete_shelf(store_id, shelf_id):
    shelf = Shelf.query.get(shelf_id)
    if shelf:
        db.session.delete(shelf)
        db.session.commit()
    return redirect(url_for('store_detail', id=store_id))

# --- EMPLOYEES ---
@app.route('/employees', methods=['GET', 'POST'])
def list_employees():
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('name') or not data.get('role') or not data.get('store_id'):
            return "Missing required fields", 400
        employee = Employee(name=data['name'], role=data['role'], store_id=data['store_id'],
                            image=data.get('image'), salary=data.get('salary'))
        db.session.add(employee)
        db.session.commit()
        return {"id": employee.id, "name": employee.name, "role": employee.role,
                "store_id": employee.store_id, "image": employee.image, "salary": employee.salary}, 201
    employees = Employee.query.all()
    return render_template('employees.html', employees=employees)

@app.route('/employees/<int:id>')
def employee_detail(id):
    employee = Employee.query.get(id)
    if not employee:
        return "Employee not found", 404
    return render_template('employee_detail.html', employee=employee)

@app.route('/employees/new', methods=['GET', 'POST'])
def create_employee():
    stores = Store.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        image = request.form.get('image')
        try:
            salary = float(request.form.get('salary', 0))
        except ValueError:
            salary = 0
        role = request.form.get('role')
        store_id = request.form.get('store_id')
        email = request.form.get('email')
        dateOfContract = request.form.get('dateOfContract')
        skills = request.form.getlist('skills')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not name or not role or not store_id or not username or not password or not email:
            flash(_('Information is incomplete. Please check required fields.'), 'error')
            return render_template('employee_form.html', employee=None, stores=stores)
            
        import json
        employee = Employee(
            name=name, image=image, salary=salary, role=role, 
            store_id=int(store_id), email=email, dateOfContract=dateOfContract,
            skills=json.dumps(skills), username=username, password=password
        )
        db.session.add(employee)
        db.session.commit()
        flash(_('Employee created successfully!'), 'success')
        return redirect(url_for('list_employees'))
    return render_template('employee_form.html', employee=None, stores=stores)

@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    employee = Employee.query.get(id)
    if not employee:
        flash(_('Employee not found.'), 'error')
        return redirect(url_for('list_employees'))
    stores = Store.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        store_id = request.form.get('store_id')
        username = request.form.get('username')
        email = request.form.get('email')

        if not name or not role or not store_id or not username or not email:
            flash(_('Information is incomplete. Please check required fields.'), 'error')
            return render_template('employee_form.html', employee=employee, stores=stores)

        employee.name = name
        employee.image = request.form.get('image')
        try:
            employee.salary = float(request.form.get('salary', 0))
        except ValueError:
            pass
        employee.role = role
        employee.store_id = int(store_id)
        employee.email = email
        employee.dateOfContract = request.form.get('dateOfContract')
        import json
        employee.skills = json.dumps(request.form.getlist('skills'))
        employee.username = username
        
        password = request.form.get('password')
        if password:  # ONLY update if provided
            employee.password = password

        db.session.commit()
        flash(_('Employee updated successfully!'), 'success')
        return redirect(url_for('employee_detail', id=id))
    return render_template('employee_form.html', employee=employee, stores=stores)

@app.route('/employees/delete/<int:id>', methods=['POST'])
def delete_employee(id):
    employee = Employee.query.get(id)
    if employee:
        db.session.delete(employee)
        db.session.commit()
    return redirect(url_for('list_employees'))

# ---------------------------------------------------------------------------
# Orion subscription callback endpoints
# ---------------------------------------------------------------------------

@app.route('/subscriptions/price-change', methods=['POST'])
def subscription_price_change():
    """Receive Orion notification when a Product price changes."""
    payload = request.get_json(silent=True) or {}
    app.logger.info('[subscription] Price-change notification received: %s', payload)
    for entity in payload.get('data', []):
        product_id = entity.get('id', '')
        price = entity.get('price', {}).get('value') if isinstance(entity.get('price'), dict) else entity.get('price')
        name = entity.get('name', {}).get('value') if isinstance(entity.get('name'), dict) else entity.get('name', '')
        socketio.emit('price_change', {
            'product_id': product_id,
            'price': price,
            'name': name,
        })
    return jsonify(status='ok'), 200


@app.route('/subscriptions/low-stock', methods=['POST'])
def subscription_low_stock():
    """Receive Orion notification when InventoryItem shelfCount is low."""
    payload = request.get_json(silent=True) or {}
    app.logger.info('[subscription] Low-stock notification received: %s', payload)
    for entity in payload.get('data', []):
        item_id = entity.get('id', '')
        shelf_count = entity.get('shelfCount', {}).get('value') if isinstance(entity.get('shelfCount'), dict) else entity.get('shelfCount')
        product_ref = entity.get('refProduct', {}).get('value') if isinstance(entity.get('refProduct'), dict) else entity.get('refProduct', '')
        store_ref = entity.get('refStore', {}).get('value') if isinstance(entity.get('refStore'), dict) else entity.get('refStore', '')
        socketio.emit('low_stock', {
            'item_id': item_id,
            'product_id': product_ref,
            'store_id': store_ref,
            'shelfCount': shelf_count,
        })
    return jsonify(status='ok'), 200


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with app.app_context():
        db.create_all()
        seed_data()

        # Update product image seeds to be more descriptive
        products_update_map = {
            "Apples": "/static/img/products/apples.png",
            "Bananas": "/static/img/products/bananas.png",
            "Coconuts": "/static/img/products/coconuts.png",
            "Melons": "/static/img/products/melons.png",
            "Kiwi Fruits": "/static/img/products/kiwi.png",
            "Strawberries": "/static/img/products/strawberries.png",
            "Raspberries": "/static/img/products/raspberries.png",
            "Pineapples": "/static/img/products/pineapples.png",
            "Oranges": "/static/img/products/oranges.png",
            "Grapes": "/static/img/products/grapes.png"
        }
        for name, img_url in products_update_map.items():
            prod = Product.query.filter_by(name=name).first()
            if prod and "wikimedia" in prod.image or "picsum" in prod.image:
                prod.image = img_url
        db.session.commit()

        # Cleanup orphan inventory items (broken FK references)
        orphans = Inventory.query.all()
        deleted = False
        for inv in orphans:
            missing_product = not Product.query.get(inv.product_id)
            missing_store = not Store.query.get(inv.store_id)
            missing_shelf = not Shelf.query.get(inv.shelf_id)
            if missing_product or missing_store or missing_shelf:
                db.session.delete(inv)
                deleted = True
        if deleted:
            db.session.commit()
    # Initialise the data layer (probes Orion; falls back to SQLite if unavailable)
    import data_layer
    data_layer.init_data_layer(app, db)

    if data_layer.USE_ORION:
        import orion
        with app.app_context():
            store_ids = [f"urn:ngsi-ld:Store:{s.id:03d}" for s in Store.query.all()]
        if store_ids:
            orion.register_context_providers(store_ids)
        orion.register_subscriptions()

    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=int(os.getenv("FLASK_PORT", 5000)))
