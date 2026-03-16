# PRD - FIWARE Smart Store

## Vision
The FIWARE Smart Store is a modern management platform for supermarket chains. It provides a real-time overview of stores and their filtered inventories, emphasizing localization and a premium user experience.

## Functional Requirements
- **Dashboard**: Real-time overview of the chain's statistics.
- **Store Management (CRUD)**: Create, view detail, edit, and delete store entities. Attributes: Name, Address, Location, Image. The detail view includes an interactive map, inventory management (add/edit/delete products with stock), and shelf management (full CRUD for shelves).
- **Product Management (CRUD)**: Create, view detail, edit, and delete product entities. Attributes: Name, Price, Size, OriginCountry, Image. The detail view includes store association and stock management.
- **Employee Management (CRUD)**: Create, view detail, edit, and delete employee entities. Attributes: Name, Image, Salary, Role, refStore.
- **Inventory Tracking**: Display specific stock for each store.
- **Full Multilingual Support**: Comprehensive translation for English and Spanish, covering navigation menus, form labels, detail field titles, and action buttons (Edit, Delete, Back). Language selection is managed via URL parameters (for immediate response) and reinforced via session for persistence.
- **Orion Context Broker Integration**: The application supports FIWARE Orion Context Broker as an alternative data source. At startup, the app probes Orion at `http://localhost:1026/v2/version`. If reachable, all CRUD operations for Store, Product, and Employee are performed against Orion using the NGSIv2 API. If Orion is unavailable, the app transparently falls back to the local SQLite database with no change in user-facing behaviour.

## Fallback Mechanism
The data source selection is automatic and logged at application startup:
- **Orion available**: `[data_layer] Orion is reachable → using Orion Context Broker`
- **Orion unavailable**: `[data_layer] Orion not available → falling back to SQLite`

The two backends are **independent** — no data is synchronised between SQLite and Orion.

## User Experience (UX)
- **Premium Design**: Modern, responsive interface with deep teal and gold accents.
- **Card-Based Layout**: List views for stores, products, and employees use centered cards with optimized image display (`object-fit: cover`) and centered information for a balanced look.
- **Visual Evidence**: Rich use of images and interactive maps to enhance recognition and localization.
- **Responsive Layout**: Seamless transition across phone, tablet, and desktop views.

## Technical Requirements
- **Backend**: Python/Flask with SQLAlchemy ORM and SQLite database (default) or FIWARE Orion Context Broker (when available).
- **Data Abstraction**: `data_layer.py` centralises all CRUD operations. It dispatches requests either to Orion (NGSIv2 REST API via `requests`) or to SQLite (SQLAlchemy), depending on availability.
- **Containerisation**: `docker-compose.yml` (based on the official FIWARE CRUD-Operations tutorial) provides Orion Context Broker and MongoDB services for local development.
- **Internationalization**: Implemented via Flask-Babel with `.po` and `.mo` catalogs. Dynamic content extraction is supported by `dummy_translations.py`.
- **Image Serving**: Optimized image handling ensures consistent presentation regardless of source (local or external).
