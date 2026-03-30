# PRD - FIWARE Smart Store (Práctica 2)

## Vision
The FIWARE Smart Store is a modern management platform for supermarket chains. It provides a real-time overview of stores and their filtered inventories, emphasizing localization, real-time event processing, and a premium user experience powered by FIWARE context-management components.

## Functional Requirements

### Core CRUD
- **Dashboard**: Real-time overview of the chain's statistics, including a Mermaid UML class diagram of the data model rendered directly in the Home page.
- **Store Management (CRUD)**: Create, view detail, edit, and delete store entities. Attributes: Name, Address, Location, Image, URL, Telephone, CountryCode (2 chars), Capacity (m³), Description, Temperature (context-provided), RelativeHumidity (context-provided). The detail view includes an interactive Leaflet map, inventory management (add/edit/delete products with stock), shelf management (full CRUD), and a Three.js virtual 3D walkthrough of the store.
- **Product Management (CRUD)**: Create, view detail, edit, and delete product entities. Attributes: Name, Price, Size, OriginCountry, Image, Color (RGB hex string). The detail view includes store association and stock management.
- **Employee Management (CRUD)**: Create, view detail, edit, and delete employee entities. Attributes: Name, Image, Salary, Role, Email, DateOfContract, Skills (`MachineryDriving`, `WritingReports`, `CustomerRelationships`), Username, Password. Each employee is assigned to exactly one Store (`refStore`).
- **Inventory Tracking**: Display specific stock per store.

### External Context Providers
The application registers **external context providers** in Orion at startup for the following Store attributes:
- **temperature** — supplied by the FIWARE tutorial context-provider container.
- **relativeHumidity** — supplied by the FIWARE tutorial context-provider container.
- **tweets** — supplied by the FIWARE tutorial context-provider container.

These values are not stored in Orion itself; Orion proxies requests to the external provider on demand.

### NGSIv2 Subscriptions
At application startup the backend creates **two NGSIv2 subscriptions** in Orion:
| Trigger | Watched attribute | Description |
|---|---|---|
| Price change | `price` on `Product` entities | Fires when any product's price is updated. |
| Low stock | `shelfCount` on `InventoryItem` entities | Fires when stock falls below a threshold in a specific store. |

> [!IMPORTANT]
> Subscription notification URLs must use `host.docker.internal` instead of `localhost` so that Orion (running inside Docker) can reach the Flask application running on the host machine.

### Real-Time Notifications
- **Server → Client push** via **Flask-SocketIO** (backend) and **Socket.IO** (frontend JS client).
- When a subscription notification arrives from Orion the backend emits a SocketIO event that the browser receives and displays as a toast/alert without page reload.

### Internationalization
- **Full Multilingual Support**: Comprehensive translation for **English (EN)** and **Spanish (ES)**, covering navigation menus, form labels, detail field titles, and action buttons (Edit, Delete, Back).
- Language selection is managed via URL parameters (for immediate response) and reinforced via session for persistence.

### Orion Context Broker Integration
The application supports FIWARE Orion Context Broker as an alternative data source. At startup, the app probes Orion at `http://localhost:1026/v2/version`. If reachable, all CRUD operations for Store, Product, and Employee are performed against Orion using the NGSIv2 API. If Orion is unavailable, the app transparently falls back to the local SQLite database with no change in user-facing behaviour.

## Fallback Mechanism
The data source selection is automatic and logged at application startup:
- **Orion available**: `[data_layer] Orion is reachable → using Orion Context Broker`
- **Orion unavailable**: `[data_layer] Orion not available → falling back to SQLite`

The two backends are **independent** — no data is synchronised between SQLite and Orion.

## User Experience (UX)
- **Premium Design**: Modern, responsive interface with deep teal and gold accents.
- **Dark / Light Mode**: User-toggleable dark and light themes with persistent preference.
- **Table-Based Layout**: List views for stores, products, and employees use responsive, data-rich tables featuring inline actions, badges, and circular thumbnail avatars. Product and store images are AI-generated and stored locally.
- **Visual Evidence**: Rich use of images, interactive Leaflet maps, and a Three.js 3D virtual store tour.
- **Responsive Layout**: Seamless transition across phone, tablet, and desktop views.
- **Font Awesome Icons**: Icon library integrated across navigation, buttons, and status indicators.
- **Mermaid UML Diagram**: Rendered on the Home/Dashboard page to visualize the entity model.

## Technical Requirements
- **Backend**: Python/Flask with SQLAlchemy ORM and SQLite database (default) or FIWARE Orion Context Broker (when available). Flask-SocketIO for WebSocket support.
- **Data Abstraction**: `data_layer.py` centralises all CRUD operations. It dispatches requests either to Orion (NGSIv2 REST API via `requests`) or to SQLite (SQLAlchemy), depending on availability.
- **Context Providers**: The FIWARE tutorial context-provider container is declared in `docker-compose.yml` and registered in Orion at startup to supply `temperature`, `relativeHumidity`, and `tweets` for Store entities.
- **Subscriptions**: Two NGSIv2 subscriptions are created in Orion at startup to watch for price changes and low-stock events.
- **Containerisation**: `docker-compose.yml` (extended from the official FIWARE tutorial) provides Orion Context Broker, MongoDB, and the tutorial context-provider container.
- **Internationalization**: Implemented via Flask-Babel with `.po` and `.mo` catalogs. Dynamic content extraction is supported by `dummy_translations.py`.
- **Image Serving**: Product and store images are **AI-generated** and stored locally in `static/img/products/` and `static/img/stores/`. These assets are excluded from version control via `.gitignore` and must be regenerated locally. Employee images use `randomuser.me` portrait URLs.
- **Import Data Script**: `import-data.sh` provisions the system with seed data: **4 stores**, **4 employees**, **4 shelves per store**, **10 products** (at least 4 products per shelf).
- **Frontend Libraries**:
  - [Leaflet.js](https://leafletjs.com/) — interactive store maps.
  - [Three.js](https://threejs.org/) — 3D virtual store walkthrough.
  - [Mermaid](https://mermaid.js.org/) — UML diagram rendering.
  - [Font Awesome](https://fontawesome.com/) — icon set.
  - [Socket.IO Client](https://socket.io/) — real-time notifications.
