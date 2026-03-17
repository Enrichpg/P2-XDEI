from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
class Inventory(db.Model):
    __tablename__ = 'inventory'
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    stock = db.Column(db.Integer, default=0)
    store = db.relationship("Store", back_populates="inventory_items")
    product = db.relationship("Product", back_populates="inventory_items")

class Shelf(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    store = db.relationship('Store', backref=db.backref('shelves', lazy=True, cascade="all, delete-orphan"))

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    location = db.Column(db.String(200))
    image = db.Column(db.String(255))
    inventory_items = db.relationship("Inventory", back_populates="store", cascade="all, delete-orphan")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(50))
    image = db.Column(db.String(255))
    originCountry = db.Column(db.String(50))
    inventory_items = db.relationship("Inventory", back_populates="product", cascade="all, delete-orphan")

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(255))
    salary = db.Column(db.Float)
    role = db.Column(db.String(50), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    store = db.relationship('Store', backref=db.backref('employees', lazy=True))

def seed_data():
    # Only seed if DB is empty
    if Store.query.count() > 0:
        return

    # Create Products
    products = [
        Product(name='Leche', price=1.20, size='1L', originCountry='ES', image='/static/img/products/leche.png'),
        Product(name='Pan', price=0.85, size='250g', originCountry='FR', image='https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=300&q=80'),
        Product(name='Huevos', price=2.10, size='12 unidades', originCountry='ES', image='https://images.unsplash.com/photo-1506976785307-8732e854ad03?auto=format&fit=crop&w=300&q=80'),
        Product(name='Arroz', price=1.10, size='1kg', originCountry='IT', image='https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=300&q=80'),
        Product(name='Pasta', price=0.95, size='500g', originCountry='IT', image='https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=300&q=80'),
        Product(name='Manzanas', price=1.50, size='1kg', originCountry='ES', image='/static/img/products/manzanas.png'),
        Product(name='Plátanos', price=1.30, size='1kg', originCountry='EC', image='https://images.unsplash.com/photo-1603833665858-e61d17a86224?auto=format&fit=crop&w=300&q=80'),
        Product(name='Pollo', price=5.50, size='1.5kg', originCountry='ES', image='https://images.unsplash.com/photo-1587593810167-a84920ea0781?auto=format&fit=crop&w=300&q=80'),
        Product(name='Ternera', price=9.80, size='500g', originCountry='AR', image='/static/img/products/ternera.png'),
        Product(name='Agua', price=0.50, size='1.5L', originCountry='ES', image='https://images.unsplash.com/photo-1548839140-29a749e1cf4d?auto=format&fit=crop&w=300&q=80')
    ]
    for p in products:
        db.session.add(p)
    db.session.commit()

    # Create Stores
    stores = [
        Store(name='Store Alpha', address='Friedrichstraße 44, 10969 Kreuzberg, Berlin', location='52.5075, 13.3903', image='https://images.unsplash.com/photo-1628177142898-93e36e4e3a50?w=600'),
        Store(name='Store Beta', address='Gran Vía 1, 28013 Madrid, Spain', location='40.4196, -3.6991', image='https://images.unsplash.com/photo-1534723452862-4c874018d66d?auto=format&fit=crop&w=300&q=80'),
        Store(name='Store Gamma', address='Corso Vittorio Emanuele II, 10123 Torino TO, Italy', location='45.0623, 7.6785', image='https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=300&q=80'),
        Store(name='Store Delta', address='Champs-Élysées, 75008 Paris, France', location='48.8698, 2.3075', image='https://images.unsplash.com/photo-1578916171728-46686eac8d58?auto=format&fit=crop&w=300&q=80')
    ]
    for s in stores:
        db.session.add(s)
    db.session.commit()

    # Assign Products to Stores with Stock (Inventory)
    ps = Product.query.all()
    ss = Store.query.all()
    # Store Alpha with first 5 products
    for i in range(5):
        db.session.add(Inventory(store_id=ss[0].id, product_id=ps[i].id, stock=100))
    # Store Beta with next 5 products
    for i in range(5, 10):
        db.session.add(Inventory(store_id=ss[1].id, product_id=ps[i].id, stock=150))
    # Store Gamma with mixed products
    for i in [0, 2, 4, 6, 9]:
        db.session.add(Inventory(store_id=ss[2].id, product_id=ps[i].id, stock=80))
    # Store Delta with remaining products
    for i in [1, 3, 5, 7, 8]:
        db.session.add(Inventory(store_id=ss[3].id, product_id=ps[i].id, stock=120))
    db.session.commit()

    # Create Shelves
    for s in ss:
        for i in range(1, 4):
            db.session.add(Shelf(store_id=s.id, name=f'Balda {i}'))
    db.session.commit()

    # Create Employees
    employees = [
        Employee(name='Ana', role='Manager', store_id=ss[0].id, salary=2500.0, image='https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=300'),
        Employee(name='Luis', role='Cashier', store_id=ss[0].id, salary=1400.0, image='https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300'),
        Employee(name='Marta', role='Manager', store_id=ss[1].id, salary=2600.0, image='https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=300'),
        Employee(name='Jorge', role='Stock Clerk', store_id=ss[2].id, salary=1300.0, image='https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=300'),
        Employee(name='Elena', role='Cashier', store_id=ss[3].id, salary=1450.0, image='https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=300')
    ]
    for e in employees:
        db.session.add(e)
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
        
        if not name:
            return "Name is required", 400
            
        store = Store(name=name, address=address, location=location, image=image)
        db.session.add(store)
        db.session.commit()
        return redirect(url_for('list_stores'))
    return render_template('store_form.html', store=None)

@app.route('/stores/edit/<int:id>', methods=['GET', 'POST'])
def edit_store(id):
    store = Store.query.get(id)
    if not store:
        return "Store not found", 404
    if request.method == 'POST':
        store.name = request.form.get('name')
        store.address = request.form.get('address')
        store.location = request.form.get('location')
        store.image = request.form.get('image')
        db.session.commit()
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
        price = float(request.form.get('price', 0))
        size = request.form.get('size')
        originCountry = request.form.get('originCountry')
        image = request.form.get('image')
        
        if not name or not price:
            return "Name and Price are required", 400
            
        product = Product(name=name, price=price, size=size, originCountry=originCountry, image=image)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('list_products'))
    return render_template('product_form.html', product=None)

@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    product = Product.query.get(id)
    if not product:
        return "Product not found", 404
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.price = float(request.form.get('price', 0))
        product.size = request.form.get('size')
        product.originCountry = request.form.get('originCountry')
        product.image = request.form.get('image')
        db.session.commit()
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
        item = Inventory.query.filter_by(store_id=store_id, product_id=product_id).first()
        if not item:
            item = Inventory(store_id=store_id, product_id=product_id, stock=stock)
            db.session.add(item)
        else:
            item.stock += stock
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
        item = Inventory.query.filter_by(store_id=store_id, product_id=product_id).first()
        if not item:
            item = Inventory(store_id=store_id, product_id=product_id, stock=stock)
            db.session.add(item)
        else:
            item.stock += stock
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
        salary = float(request.form.get('salary', 0))
        role = request.form.get('role')
        store_id = request.form.get('store_id')
        
        if not name or not role or not store_id:
            return "Name, Role, and Store are required", 400
            
        employee = Employee(name=name, image=image, salary=salary, role=role, store_id=int(store_id))
        db.session.add(employee)
        db.session.commit()
        return redirect(url_for('list_employees'))
    return render_template('employee_form.html', employee=None, stores=stores)

@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    employee = Employee.query.get(id)
    if not employee:
        return "Employee not found", 404
    stores = Store.query.all()
    if request.method == 'POST':
        employee.name = request.form.get('name')
        employee.image = request.form.get('image')
        employee.salary = float(request.form.get('salary', 0))
        employee.role = request.form.get('role')
        employee.store_id = int(request.form.get('store_id'))
        db.session.commit()
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

    socketio.run(app, debug=True)
