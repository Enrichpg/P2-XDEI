# FIWARE Smart Store – Práctica 2

## Descripción

Aplicación de gestión de cadenas de supermercados basada en **FIWARE Orion Context Broker (NGSIv2)**. Incluye:
- CRUD completo de Stores, Products, Employees, Shelves, InventoryItems
- Proveedores de contexto externo (temperatura, humedad, tweets)
- Suscripciones NGSIv2 y notificaciones en tiempo real vía **Flask-SocketIO**
- Interfaz multilingüe (ES/EN) con modo Dark/Light
- Mapa Leaflet JS, recorrido virtual Three.js, diagrama UML Mermaid

## Repositorio GitHub

🔗 [https://github.com/Enrichpg/P2-XDEI](https://github.com/Enrichpg/P2-XDEI)

## Requisitos previos

- Docker y Docker Compose instalados
- Python 3.10+

## Instalación

```bash
git clone https://github.com/Enrichpg/P2-XDEI.git
cd P2-XDEI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Compilar traducciones
pybabel compile -d translations
```

## Ejecución

```bash
# Opción 1: Script todo-en-uno
chmod +x start.sh
./start.sh

# Opción 2: Manual
docker compose up -d
# Esperar a que Orion arranque (~20 s)
docker run --rm -v $(pwd)/import-data:/import-data \
  --network fiware_default \
  --entrypoint /bin/ash quay.io/curl/curl /import-data
python app.py
```

La aplicación queda disponible en: **http://localhost:5000**

## Parada

```bash
./stop.sh
# o
docker compose down
```

## Variables de entorno (opcionales)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `FLASK_PORT` | `5000` | Puerto de Flask |
| `ORION_URL` | `http://localhost:1026/v2` | URL del Orion Context Broker |
| `LOW_STOCK_THRESHOLD` | `10` | Umbral de stock bajo para suscripción |
| `SECRET_KEY` | `dev-secret-p2-xdei` | Clave secreta Flask |
