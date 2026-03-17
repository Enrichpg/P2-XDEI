"""
orion.py – NGSIv2 client for FIWARE Smart Store (Práctica 2)
All data operations go through Orion Context Broker.
"""
import os
import requests

ORION_URL = os.getenv("ORION_URL", "http://localhost:1026/v2")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
NOTIFY_URL = f"http://host.docker.internal:{FLASK_PORT}/notify"
LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", 10))

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


# ---------------------------------------------------------------------------
# Generic entity helpers
# ---------------------------------------------------------------------------

def _get(path, params=None):
    r = requests.get(f"{ORION_URL}{path}", headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def _post(path, payload):
    r = requests.post(f"{ORION_URL}{path}", headers=HEADERS, json=payload, timeout=10)
    r.raise_for_status()
    return r


def _patch(path, payload):
    r = requests.patch(f"{ORION_URL}{path}", headers=HEADERS, json=payload, timeout=10)
    r.raise_for_status()
    return r


def _delete(path):
    r = requests.delete(f"{ORION_URL}{path}", headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r


def get_entities(entity_type, limit=100, offset=0, extra_params=None):
    params = {"type": entity_type, "limit": limit, "offset": offset,
              "options": "keyValues"}
    if extra_params:
        params.update(extra_params)
    return _get("/entities", params=params)


def get_entity(entity_id, options="keyValues"):
    params = {"options": options} if options else {}
    return _get(f"/entities/{entity_id}", params=params)


def create_entity(payload):
    return _post("/entities", payload)


def update_entity_attrs(entity_id, attrs_payload):
    """PATCH /v2/entities/<id>/attrs  (plain attrs dict, not keyValues)"""
    return _patch(f"/entities/{entity_id}/attrs", attrs_payload)


def delete_entity(entity_id):
    return _delete(f"/entities/{entity_id}")


# ---------------------------------------------------------------------------
# Typed helpers
# ---------------------------------------------------------------------------

def _attr(typ, value):
    return {"type": typ, "value": value}


def _text(v):    return _attr("Text", v)
def _number(v):  return _attr("Number", v)
def _integer(v): return _attr("Integer", v)
def _rel(v):     return _attr("Relationship", v)
def _geo(lat, lng): return _attr("geo:json", {"type": "Point", "coordinates": [lng, lat]})
def _postal(street, region, locality, postal):
    return _attr("PostalAddress", {
        "streetAddress": street, "addressRegion": region,
        "addressLocality": locality, "postalCode": postal
    })


# ---------------------------------------------------------------------------
# Store CRUD
# ---------------------------------------------------------------------------

def get_stores(limit=100):
    return get_entities("Store", limit=limit)


def get_store(store_id):
    return get_entity(store_id, options="")


def create_store(data):
    """data: dict with flat keys (name, street, region, locality, postal,
    lat, lng, image, url, telephone, countryCode, capacity, description)"""
    payload = {
        "id": data["id"],
        "type": "Store",
        "name":        _text(data.get("name", "")),
        "address":     _postal(data.get("street",""), data.get("region",""),
                                data.get("locality",""), data.get("postal","")),
        "location":    _geo(float(data.get("lat", 0)), float(data.get("lng", 0))),
        "image":       _text(data.get("image", "")),
        "url":         _text(data.get("url", "")),
        "telephone":   _text(data.get("telephone", "")),
        "countryCode": _text(data.get("countryCode", "")),
        "capacity":    _number(float(data.get("capacity", 0))),
        "description": _text(data.get("description", "")),
    }
    return create_entity(payload)


def update_store(store_id, data):
    attrs = {}
    for key in ("name", "image", "url", "telephone", "countryCode", "description"):
        if key in data:
            attrs[key] = _text(data[key])
    if "capacity" in data:
        attrs["capacity"] = _number(float(data["capacity"]))
    if all(k in data for k in ("street", "region", "locality", "postal")):
        attrs["address"] = _postal(data["street"], data["region"],
                                    data["locality"], data["postal"])
    if "lat" in data and "lng" in data:
        attrs["location"] = _geo(float(data["lat"]), float(data["lng"]))
    return update_entity_attrs(store_id, attrs)


# ---------------------------------------------------------------------------
# Product CRUD
# ---------------------------------------------------------------------------

def get_products(limit=100):
    return get_entities("Product", limit=limit)


def get_product(product_id):
    return get_entity(product_id, options="")


def create_product(data):
    payload = {
        "id": data["id"],
        "type": "Product",
        "name":          _text(data.get("name", "")),
        "price":         _integer(int(data.get("price", 0))),
        "size":          _text(data.get("size", "")),
        "image":         _text(data.get("image", "")),
        "originCountry": _text(data.get("originCountry", "")),
        "color":         _text(data.get("color", "#FFFFFF")),
    }
    return create_entity(payload)


def update_product(product_id, data):
    attrs = {}
    for key in ("name", "size", "image", "originCountry", "color"):
        if key in data:
            attrs[key] = _text(data[key])
    if "price" in data:
        attrs["price"] = _integer(int(data["price"]))
    return update_entity_attrs(product_id, attrs)


# ---------------------------------------------------------------------------
# Employee CRUD
# ---------------------------------------------------------------------------

def get_employees(limit=100):
    return get_entities("Employee", limit=limit)


def get_employee(employee_id):
    return get_entity(employee_id, options="")


def create_employee(data):
    payload = {
        "id": data["id"],
        "type": "Employee",
        "name":           _text(data.get("name", "")),
        "image":          _text(data.get("image", "")),
        "salary":         _number(float(data.get("salary", 0))),
        "category":       _text(data.get("category", "")),
        "email":          _text(data.get("email", "")),
        "dateOfContract": _attr("DateTime", data.get("dateOfContract", "2020-01-01T00:00:00Z")),
        "skills":         _attr("StructuredValue", data.get("skills", [])),
        "username":       _text(data.get("username", "")),
        "password":       _text(data.get("password", "")),
        "refStore":       _rel(data.get("refStore", "")),
    }
    return create_entity(payload)


def update_employee(employee_id, data):
    attrs = {}
    for key in ("name", "image", "category", "email", "username", "password"):
        if key in data:
            attrs[key] = _text(data[key])
    if "salary" in data:
        attrs["salary"] = _number(float(data["salary"]))
    if "dateOfContract" in data:
        attrs["dateOfContract"] = _attr("DateTime", data["dateOfContract"])
    if "skills" in data:
        attrs["skills"] = _attr("StructuredValue", data["skills"])
    if "refStore" in data:
        attrs["refStore"] = _rel(data["refStore"])
    return update_entity_attrs(employee_id, attrs)


# ---------------------------------------------------------------------------
# Shelf CRUD
# ---------------------------------------------------------------------------

def get_shelves(store_id=None, limit=100):
    params = {}
    if store_id:
        params = {"q": f"refStore=={store_id}"}
    return get_entities("Shelf", limit=limit, extra_params=params)


def get_shelf(shelf_id):
    return get_entity(shelf_id, options="")


def create_shelf(data):
    payload = {
        "id": data["id"],
        "type": "Shelf",
        "name":        _text(data.get("name", "")),
        "maxCapacity": _integer(int(data.get("maxCapacity", 50))),
        "refStore":    _rel(data.get("refStore", "")),
    }
    if "lat" in data and "lng" in data:
        payload["location"] = _geo(float(data["lat"]), float(data["lng"]))
    return create_entity(payload)


def update_shelf(shelf_id, data):
    attrs = {}
    if "name" in data:
        attrs["name"] = _text(data["name"])
    if "maxCapacity" in data:
        attrs["maxCapacity"] = _integer(int(data["maxCapacity"]))
    return update_entity_attrs(shelf_id, attrs)


# ---------------------------------------------------------------------------
# InventoryItem CRUD
# ---------------------------------------------------------------------------

def get_inventory_items(store_id=None, shelf_id=None, product_id=None, limit=1000):
    q_parts = []
    if store_id:
        q_parts.append(f"refStore=={store_id}")
    if shelf_id:
        q_parts.append(f"refShelf=={shelf_id}")
    if product_id:
        q_parts.append(f"refProduct=={product_id}")
    params = {}
    if q_parts:
        params["q"] = ";".join(q_parts)
    return get_entities("InventoryItem", limit=limit, extra_params=params)


def get_inventory_item(item_id):
    return get_entity(item_id, options="")


def create_inventory_item(data):
    payload = {
        "id": data["id"],
        "type": "InventoryItem",
        "refStore":   _rel(data["refStore"]),
        "refShelf":   _rel(data["refShelf"]),
        "refProduct": _rel(data["refProduct"]),
        "stockCount": _integer(int(data.get("stockCount", 1000))),
        "shelfCount": _integer(int(data.get("shelfCount", 10))),
    }
    return create_entity(payload)


def update_inventory_item(item_id, data):
    attrs = {}
    if "stockCount" in data:
        attrs["stockCount"] = _integer(int(data["stockCount"]))
    if "shelfCount" in data:
        attrs["shelfCount"] = _integer(int(data["shelfCount"]))
    return update_entity_attrs(item_id, attrs)


# ---------------------------------------------------------------------------
# Context Providers Registration
# ---------------------------------------------------------------------------

def register_context_providers(store_ids):
    """Register weather and tweets context providers for each store."""
    existing_descs = set()
    try:
        regs = _get("/registrations", params={"limit": 200})
        existing_descs = {r.get("description", "") for r in regs}
    except Exception:
        pass

    for sid in store_ids:
        # Weather
        weather_desc = f"Weather Conditions {sid}"
        if weather_desc not in existing_descs:
            try:
                _post("/registrations", {
                    "description": weather_desc,
                    "dataProvided": {
                        "entities": [{"id": sid, "type": "Store"}],
                        "attrs": ["temperature", "relativeHumidity"]
                    },
                    "provider": {
                        "http": {"url": "http://tutorial:3000/proxy/v1/random/weatherConditions"},
                        "legacyForwarding": True
                    },
                    "status": "active"
                })
            except Exception as e:
                print(f"[orion] Warning: could not register weather provider for {sid}: {e}")

        # Tweets
        tweets_desc = f"Tweeting Cat Facts {sid}"
        if tweets_desc not in existing_descs:
            try:
                _post("/registrations", {
                    "description": tweets_desc,
                    "dataProvided": {
                        "entities": [{"id": sid, "type": "Store"}],
                        "attrs": ["tweets"]
                    },
                    "provider": {
                        "http": {"url": "http://tutorial:3000/proxy/v1/catfacts/tweets"},
                        "legacyForwarding": True
                    },
                    "status": "active"
                })
            except Exception as e:
                print(f"[orion] Warning: could not register tweets provider for {sid}: {e}")


# ---------------------------------------------------------------------------
# Subscriptions Registration
# ---------------------------------------------------------------------------

def register_subscriptions():
    """Register price-change and low-stock subscriptions (idempotent)."""
    existing = set()
    try:
        subs = _get("/subscriptions", params={"limit": 200})
        existing = {s.get("description", "") for s in subs}
    except Exception:
        pass

    # Subscription: product price change
    price_desc = "Product price change notification"
    if price_desc not in existing:
        try:
            _post("/subscriptions", {
                "description": price_desc,
                "subject": {
                    "entities": [{"idPattern": ".*", "type": "Product"}],
                    "condition": {"attrs": ["price"]}
                },
                "notification": {
                    "http": {"url": NOTIFY_URL},
                    "attrs": ["price", "name"]
                }
            })
            print(f"[orion] Registered subscription: {price_desc}")
        except Exception as e:
            print(f"[orion] Warning: could not register price subscription: {e}")

    # Subscription: low stock
    stock_desc = "Low stock notification"
    if stock_desc not in existing:
        try:
            _post("/subscriptions", {
                "description": stock_desc,
                "subject": {
                    "entities": [{"idPattern": ".*", "type": "InventoryItem"}],
                    "condition": {
                        "attrs": ["shelfCount"],
                        "expression": {"q": f"shelfCount<{LOW_STOCK_THRESHOLD}"}
                    }
                },
                "notification": {
                    "http": {"url": NOTIFY_URL},
                    "attrs": ["shelfCount", "stockCount", "refProduct", "refStore", "refShelf"]
                }
            })
            print(f"[orion] Registered subscription: {stock_desc}")
        except Exception as e:
            print(f"[orion] Warning: could not register stock subscription: {e}")


# ---------------------------------------------------------------------------
# ID helpers
# ---------------------------------------------------------------------------

def next_id(entity_type, pad=3):
    """Find the next available URN ID for a given type."""
    prefix = f"urn:ngsi-ld:{entity_type}:"
    try:
        entities = get_entities(entity_type, limit=1000)
        ids = [e.get("id","") for e in entities if e.get("id","").startswith(prefix)]
        nums = []
        for eid in ids:
            suffix = eid[len(prefix):]
            # Handle InventoryItem:NNN and Shelf:unitNNN
            s = suffix.replace("unit", "")
            try:
                nums.append(int(s))
            except ValueError:
                pass
        nxt = max(nums) + 1 if nums else 1
        if entity_type == "Shelf":
            return f"{prefix}unit{str(nxt).zfill(pad)}"
        return f"{prefix}{str(nxt).zfill(pad)}"
    except Exception:
        return f"{prefix}{'001'.zfill(pad)}"
