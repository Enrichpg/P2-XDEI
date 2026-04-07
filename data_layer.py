"""
data_layer.py – Data abstraction layer for fiware-smart-store.

On startup, call init_data_layer(app) inside the Flask application context.
It probes Orion Context Broker at http://localhost:1026/v2/version:
  - If reachable  → USE_ORION = True  (all CRUD goes to Orion via NGSIv2)
  - If unreachable → USE_ORION = False (all CRUD falls back to SQLite/SQLAlchemy)

The active mode is logged at INFO level so it is visible in the Flask startup output.

NGSIv2 entity ID scheme: urn:ngsi-ld:<Type>:<zero-padded-3-digit-int>
  e.g. Store id=3  → "urn:ngsi-ld:Store:003"
       Product id=12 → "urn:ngsi-ld:Product:012"
"""

import logging
import types

import requests

logger = logging.getLogger(__name__)

ORION_BASE_URL = "http://localhost:1026/v2"
ORION_VERSION_URL = "http://localhost:1026/version"

# Module-level flag set by init_data_layer()
USE_ORION = False

# Will be set to the SQLAlchemy db instance by init_data_layer()
_db = None
_app = None

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_data_layer(app, db):
    """Call this once inside the Flask app context to probe Orion."""
    global USE_ORION, _db, _app
    _db = db
    _app = app
    try:
        resp = requests.get(ORION_VERSION_URL, timeout=3)
        resp.raise_for_status()
        USE_ORION = True
        logger.info("[data_layer] Orion is reachable → using Orion Context Broker")
    except Exception as exc:
        USE_ORION = False
        logger.info("[data_layer] Orion not available → falling back to SQLite (%s)", exc)


# ---------------------------------------------------------------------------
# ID helpers
# ---------------------------------------------------------------------------

def _to_urn(entity_type: str, int_id: int) -> str:
    return f"urn:ngsi-ld:{entity_type}:{int_id:03d}"


def _from_urn(urn: str) -> int:
    """Extract the integer part from a URN like urn:ngsi-ld:Store:003 → 3."""
    return int(urn.split(":")[-1])


# ---------------------------------------------------------------------------
# NGSIv2 payload builders
# ---------------------------------------------------------------------------

def _store_to_ngsi(data: dict) -> dict:
    """Convert a dict with store fields to NGSIv2 attribute format."""
    location_val = {"type": "Point", "coordinates": [0.0, 0.0]}
    if data.get("location"):
        try:
            parts = [p.strip() for p in str(data["location"]).split(",")]
            lat, lng = float(parts[0]), float(parts[1])
            location_val = {"type": "Point", "coordinates": [lng, lat]}
        except Exception:
            pass

    return {
        "name":        {"type": "Text",     "value": data.get("name", "")},
        "address":     {"type": "Text",     "value": data.get("address", "") or ""},
        "location":    {"type": "geo:json", "value": location_val},
        "image":       {"type": "Text",     "value": data.get("image", "") or ""},
        "url":         {"type": "Text",     "value": data.get("url", "") or ""},
        "telephone":   {"type": "Text",     "value": data.get("telephone", "") or ""},
        "countryCode": {"type": "Text",     "value": data.get("countryCode", "") or ""},
        "capacity":    {"type": "Number",   "value": int(data.get("capacity", 0)) if data.get("capacity") else 0},
        "description": {"type": "Text",     "value": data.get("description", "") or ""}
    }


def _product_to_ngsi(data: dict) -> dict:
    try:
        price_val = float(data.get("price", 0))
    except (TypeError, ValueError):
        price_val = 0.0
    return {
        "name":          {"type": "Text",   "value": data.get("name", "")},
        "price":         {"type": "Number", "value": price_val},
        "size":          {"type": "Text",   "value": data.get("size", "") or ""},
        "originCountry": {"type": "Text",   "value": data.get("originCountry", "") or ""},
        "image":         {"type": "Text",   "value": data.get("image", "") or ""},
        "color":         {"type": "Text",   "value": data.get("color", "") or ""}
    }


def _employee_to_ngsi(data: dict, store_int_id=None) -> dict:
    try:
        salary_val = float(data.get("salary", 0))
    except (TypeError, ValueError):
        salary_val = 0.0
    ref_store = ""
    if store_int_id:
        ref_store = _to_urn("Store", int(store_int_id))
    elif data.get("store_id"):
        ref_store = _to_urn("Store", int(data["store_id"]))
        
    import json
    skills_val = []
    if data.get("skills"):
        try:
            skills_val = json.loads(data["skills"]) if isinstance(data["skills"], str) else data["skills"]
        except Exception:
            pass

    return {
        "name":           {"type": "Text",            "value": data.get("name", "")},
        "salary":         {"type": "Number",          "value": salary_val},
        "category":       {"type": "Text",            "value": data.get("category", "") or ""},
        "refStore":       {"type": "Relationship",    "value": ref_store},
        "image":          {"type": "Text",            "value": data.get("image", "") or ""},
        "email":          {"type": "Text",            "value": data.get("email", "") or ""},
        "dateOfContract": {"type": "DateTime",        "value": data.get("dateOfContract", "") or ""},
        "skills":         {"type": "StructuredValue", "value": skills_val},
        "username":       {"type": "Text",            "value": data.get("username", "") or ""},
        "password":       {"type": "Text",            "value": data.get("password", "") or ""}
    }


# ---------------------------------------------------------------------------
# NGSIv2 response → SimpleNamespace (template-compatible object)
# ---------------------------------------------------------------------------

def _ngsi_to_store(entity: dict):
    def _val(key):
        return entity.get(key, {}).get("value", "")

    location_str = ""
    loc = entity.get("location", {}).get("value", {})
    if isinstance(loc, dict) and loc.get("coordinates"):
        coords = loc["coordinates"]  # [lng, lat]
        location_str = f"{coords[1]}, {coords[0]}"

    return types.SimpleNamespace(
        id=_from_urn(entity["id"]),
        name=_val("name"),
        address=_val("address"),
        location=location_str,
        image=_val("image"),
        url=_val("url"),
        telephone=_val("telephone"),
        countryCode=_val("countryCode"),
        capacity=_val("capacity"),
        description=_val("description"),
        inventory_items=[],  # Not managed via Orion
        shelves=[],          # Not managed via Orion
        employees=[],        # Not managed via Orion
    )


def _ngsi_to_product(entity: dict):
    def _val(key):
        return entity.get(key, {}).get("value", "")

    return types.SimpleNamespace(
        id=_from_urn(entity["id"]),
        name=_val("name"),
        price=_val("price"),
        originCountry=_val("originCountry"),
        image=_val("image"),
        color=_val("color"),
        size=_val("size"),
        inventory_items=[],
    )


def _ngsi_to_employee(entity: dict):
    def _val(key):
        return entity.get(key, {}).get("value", "")

    ref = _val("refStore")
    store_id = _from_urn(ref) if ref else None

    import json
    skills_val = entity.get("skills", {}).get("value", [])
    skills_str = json.dumps(skills_val) if isinstance(skills_val, list) else str(skills_val)

    return types.SimpleNamespace(
        id=_from_urn(entity["id"]),
        name=_val("name"),
        salary=_val("salary"),
        category=_val("category"),
        image=_val("image"),
        email=_val("email"),
        dateOfContract=_val("dateOfContract"),
        skills=skills_str,
        username=_val("username"),
        password=_val("password"),
        store_id=store_id,
        store=None,  # Lazy – not fetched
    )


# ---------------------------------------------------------------------------
# Helper: safe Orion request with logging
# ---------------------------------------------------------------------------

def _orion_request(method: str, path: str, **kwargs):
    url = ORION_BASE_URL + path
    try:
        resp = requests.request(method, url, timeout=5, **kwargs)
        if not resp.ok:
            logger.error(
                "[data_layer] Orion %s %s → HTTP %s: %s",
                method.upper(), path, resp.status_code, resp.text[:200],
            )
        return resp
    except Exception as exc:
        logger.error("[data_layer] Orion %s %s failed: %s", method.upper(), path, exc)
        return None


# ===========================================================================
# STORE CRUD
# ===========================================================================

# ── Orion backend ──────────────────────────────────────────────────────────

def _orion_get_all_stores():
    resp = _orion_request("GET", "/entities?type=Store&limit=1000")
    if resp and resp.ok:
        return [_ngsi_to_store(e) for e in resp.json()]
    return []


def _orion_get_store(int_id: int):
    resp = _orion_request("GET", f"/entities/{_to_urn('Store', int_id)}")
    if resp and resp.ok:
        return _ngsi_to_store(resp.json())
    return None


def _orion_create_store(data: dict):
    # Find next available numeric ID
    existing = _orion_get_all_stores()
    next_id = max((s.id for s in existing), default=0) + 1
    entity = {"id": _to_urn("Store", next_id), "type": "Store"}
    entity.update(_store_to_ngsi(data))
    resp = _orion_request(
        "POST", "/entities",
        json=entity,
        headers={"Content-Type": "application/json"},
    )
    if resp and resp.status_code == 201:
        return _ngsi_to_store(entity)
    return None


def _orion_update_store(int_id: int, data: dict):
    attrs = _store_to_ngsi(data)
    resp = _orion_request(
        "PATCH", f"/entities/{_to_urn('Store', int_id)}/attrs",
        json=attrs,
        headers={"Content-Type": "application/json"},
    )
    return resp and resp.ok


def _orion_delete_store(int_id: int):
    resp = _orion_request("DELETE", f"/entities/{_to_urn('Store', int_id)}")
    return resp and resp.ok


# ── SQLite backend ─────────────────────────────────────────────────────────

def _sqlite_get_all_stores():
    from app import Store
    return Store.query.all()


def _sqlite_get_store(int_id: int):
    from app import Store
    return Store.query.get(int_id)


def _sqlite_create_store(data: dict):
    from app import Store, db
    store = Store(
        name=data.get("name"),
        address=data.get("address"),
        location=data.get("location"),
        image=data.get("image"),
        url=data.get("url"),
        telephone=data.get("telephone"),
        countryCode=data.get("countryCode"),
        capacity=int(data.get("capacity")) if data.get("capacity") else None,
        description=data.get("description"),
    )
    db.session.add(store)
    db.session.commit()
    return store


def _sqlite_update_store(int_id: int, data: dict):
    from app import Store, db
    store = Store.query.get(int_id)
    if not store:
        return False
    store.name = data.get("name", store.name)
    store.address = data.get("address", store.address)
    store.location = data.get("location", store.location)
    store.image = data.get("image", store.image)
    store.url = data.get("url", store.url)
    store.telephone = data.get("telephone", store.telephone)
    store.countryCode = data.get("countryCode", store.countryCode)
    if data.get("capacity") is not None:
        store.capacity = int(data.get("capacity"))
    store.description = data.get("description", store.description)
    db.session.commit()
    return True


def _sqlite_delete_store(int_id: int):
    from app import Store, db
    store = Store.query.get(int_id)
    if not store:
        return False
    db.session.delete(store)
    db.session.commit()
    return True


# ── Public API ─────────────────────────────────────────────────────────────

def get_all_stores():
    return _orion_get_all_stores() if USE_ORION else _sqlite_get_all_stores()


def get_store(int_id: int):
    return _orion_get_store(int_id) if USE_ORION else _sqlite_get_store(int_id)


def create_store(data: dict):
    return _orion_create_store(data) if USE_ORION else _sqlite_create_store(data)


def update_store(int_id: int, data: dict):
    return _orion_update_store(int_id, data) if USE_ORION else _sqlite_update_store(int_id, data)


def delete_store(int_id: int):
    return _orion_delete_store(int_id) if USE_ORION else _sqlite_delete_store(int_id)


# ===========================================================================
# PRODUCT CRUD
# ===========================================================================

def _orion_get_all_products():
    resp = _orion_request("GET", "/entities?type=Product&limit=1000")
    if resp and resp.ok:
        products = [_ngsi_to_product(e) for e in resp.json()]
        unique_prods = []
        seen = set()
        for p in products:
            if p.name not in seen:
                seen.add(p.name)
                unique_prods.append(p)
        return unique_prods
    return []


def _orion_get_product(int_id: int):
    resp = _orion_request("GET", f"/entities/{_to_urn('Product', int_id)}")
    if resp and resp.ok:
        return _ngsi_to_product(resp.json())
    return None


def _orion_create_product(data: dict):
    existing = _orion_get_all_products()
    next_id = max((p.id for p in existing), default=0) + 1
    entity = {"id": _to_urn("Product", next_id), "type": "Product"}
    entity.update(_product_to_ngsi(data))
    resp = _orion_request(
        "POST", "/entities",
        json=entity,
        headers={"Content-Type": "application/json"},
    )
    if resp and resp.status_code == 201:
        return _ngsi_to_product(entity)
    return None


def _orion_update_product(int_id: int, data: dict):
    attrs = _product_to_ngsi(data)
    resp = _orion_request(
        "PATCH", f"/entities/{_to_urn('Product', int_id)}/attrs",
        json=attrs,
        headers={"Content-Type": "application/json"},
    )
    return resp and resp.ok


def _orion_delete_product(int_id: int):
    resp = _orion_request("DELETE", f"/entities/{_to_urn('Product', int_id)}")
    return resp and resp.ok


def _sqlite_get_all_products():
    from app import Product
    products = Product.query.all()
    unique_prods = []
    seen = set()
    for p in products:
        if p.name not in seen:
            seen.add(p.name)
            unique_prods.append(p)
    return unique_prods


def _sqlite_get_product(int_id: int):
    from app import Product
    return Product.query.get(int_id)


def _sqlite_create_product(data: dict):
    from app import Product, db
    product = Product(
        name=data.get("name"),
        price=data.get("price"),
        size=data.get("size"),
        originCountry=data.get("originCountry"),
        image=data.get("image"),
        color=data.get("color"),
    )
    db.session.add(product)
    db.session.commit()
    return product


def _sqlite_update_product(int_id: int, data: dict):
    from app import Product, db
    product = Product.query.get(int_id)
    if not product:
        return False
    product.name = data.get("name", product.name)
    product.price = data.get("price", product.price)
    product.size = data.get("size", product.size)
    product.originCountry = data.get("originCountry", product.originCountry)
    product.image = data.get("image", product.image)
    product.color = data.get("color", product.color)
    db.session.commit()
    return True


def _sqlite_delete_product(int_id: int):
    from app import Product, db
    product = Product.query.get(int_id)
    if not product:
        return False
    db.session.delete(product)
    db.session.commit()
    return True


def get_all_products():
    return _orion_get_all_products() if USE_ORION else _sqlite_get_all_products()


def get_product(int_id: int):
    return _orion_get_product(int_id) if USE_ORION else _sqlite_get_product(int_id)


def create_product(data: dict):
    return _orion_create_product(data) if USE_ORION else _sqlite_create_product(data)


def update_product(int_id: int, data: dict):
    return _orion_update_product(int_id, data) if USE_ORION else _sqlite_update_product(int_id, data)


def delete_product(int_id: int):
    return _orion_delete_product(int_id) if USE_ORION else _sqlite_delete_product(int_id)


# ===========================================================================
# EMPLOYEE CRUD
# ===========================================================================

def _orion_get_all_employees():
    resp = _orion_request("GET", "/entities?type=Employee&limit=1000")
    if resp and resp.ok:
        return [_ngsi_to_employee(e) for e in resp.json()]
    return []


def _orion_get_employee(int_id: int):
    resp = _orion_request("GET", f"/entities/{_to_urn('Employee', int_id)}")
    if resp and resp.ok:
        return _ngsi_to_employee(resp.json())
    return None


def _orion_create_employee(data: dict):
    existing = _orion_get_all_employees()
    next_id = max((e.id for e in existing), default=0) + 1
    entity = {"id": _to_urn("Employee", next_id), "type": "Employee"}
    entity.update(_employee_to_ngsi(data))
    resp = _orion_request(
        "POST", "/entities",
        json=entity,
        headers={"Content-Type": "application/json"},
    )
    if resp and resp.status_code == 201:
        return _ngsi_to_employee(entity)
    return None


def _orion_update_employee(int_id: int, data: dict):
    attrs = _employee_to_ngsi(data)
    resp = _orion_request(
        "PATCH", f"/entities/{_to_urn('Employee', int_id)}/attrs",
        json=attrs,
        headers={"Content-Type": "application/json"},
    )
    return resp and resp.ok


def _orion_delete_employee(int_id: int):
    resp = _orion_request("DELETE", f"/entities/{_to_urn('Employee', int_id)}")
    return resp and resp.ok


def _sqlite_get_all_employees():
    from app import Employee
    return Employee.query.all()


def _sqlite_get_employee(int_id: int):
    from app import Employee
    return Employee.query.get(int_id)


def _sqlite_create_employee(data: dict):
    from app import Employee, db
    employee = Employee(
        name=data.get("name"),
        image=data.get("image"),
        salary=data.get("salary"),
        category=data.get("category"),
        store_id=data.get("store_id"),
        email=data.get("email"),
        dateOfContract=data.get("dateOfContract"),
        skills=data.get("skills"),
        username=data.get("username"),
        password=data.get("password"),
    )
    db.session.add(employee)
    db.session.commit()
    return employee


def _sqlite_update_employee(int_id: int, data: dict):
    from app import Employee, db
    employee = Employee.query.get(int_id)
    if not employee:
        return False
    employee.name = data.get("name", employee.name)
    employee.image = data.get("image", employee.image)
    employee.salary = data.get("salary", employee.salary)
    employee.category = data.get("category", employee.category)
    employee.email = data.get("email", employee.email)
    employee.dateOfContract = data.get("dateOfContract", employee.dateOfContract)
    employee.skills = data.get("skills", employee.skills)
    employee.username = data.get("username", employee.username)
    employee.password = data.get("password", employee.password)
    if data.get("store_id"):
        employee.store_id = int(data["store_id"])
    db.session.commit()
    return True


def _sqlite_delete_employee(int_id: int):
    from app import Employee, db
    employee = Employee.query.get(int_id)
    if not employee:
        return False
    db.session.delete(employee)
    db.session.commit()
    return True


def get_all_employees():
    return _orion_get_all_employees() if USE_ORION else _sqlite_get_all_employees()


def get_employee(int_id: int):
    return _orion_get_employee(int_id) if USE_ORION else _sqlite_get_employee(int_id)


def create_employee(data: dict):
    return _orion_create_employee(data) if USE_ORION else _sqlite_create_employee(data)


def update_employee(int_id: int, data: dict):
    return _orion_update_employee(int_id, data) if USE_ORION else _sqlite_update_employee(int_id, data)


def delete_employee(int_id: int):
    return _orion_delete_employee(int_id) if USE_ORION else _sqlite_delete_employee(int_id)
