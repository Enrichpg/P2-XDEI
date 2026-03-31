# Pending Issues (FIWARE Smart Store)

Aquí tienes la lista de los próximos hitos a abordar para finalizar la **Práctica 2** del FIWARE Smart Store y pulir al 100% sus funcionalidades avanzadas.

---

### [ ] Issue 3: Refactorización y Enriquecimiento de Vistas de Detalle
El objetivo es transformar la vista interna de las Tiendas (`store_detail.html`) y Productos (`product_detail.html`) en consolas de administración interactivas:
- **Mapas Interactivos (`Leaflet.js`)**: Incorporar un mapa que apunte mediante pines a las coordenadas reales de la tienda cargada.
- **Recorrido Virtual 3D (`Three.js`)**: Interfaz jugable/visual que represente volumétricamente el diseño de los pasillos de la tienda.
- **Micro-gestión de Inventario**: Mejorar los controles de stock en las estanterías (Añadir/Editar/Borrar producto desde su propia vista).

---

### [ ] Issue 4: Mejoras Visuales del Dashboard y Formularios
Centraremos el esfuerzo en la puerta de entrada (`Home / Dashboard`) de la plataforma y en la ingesta de datos limpios:
- **Diagrama UML en Vivo (`Mermaid.js`)**: Renderizar esquemas *Live* autodescriptivos de la estructura de las bases de datos o clases al iniciar sesión.
- **Validaciones Front y Back (A11y)**: Añadir un control más robusto, mensajes de advertencia, y chequeos visuales a los formularios a la hora de inyectar Tiendas, Empleados o Productos nuevos a Orion/SQLite, de modo que rechace entradas ilógicas antes de recargar.

---

### [ ] Issue 5: Notificaciones en Tiempo Real y Traducción (i18n)
La cereza del pastel del backend para tener una aplicación completamente responsiva y universal:
- **Push en Tiempo Real (`FIWARE Subscriptions` + `Socket.IO`)**: Atar cabos con la suscripción a eventos críticos de OrionBroker. Cuando baje el inventario o se altere un precio y notifique por vía REST al servidor, las ventanas front de todos los administradores deben iluminarse con avisos "Toasts" dinámicos en pantalla.
- **Internacionalización Total (`Flask-Babel`)**: Revisar y asegurar mediante inspección (usando comandos `.po`/`.mo`) que todos los literales incrustados, validaciones de los nuevos formularios y mensajes de los nuevos mapas se puedan intercambiar al 100% entre Español (ES) e Inglés (EN).

---

> [!NOTE]
> ***Recordatorio para la próxima sesión:*** Las bases técnicas actuales alojan el proyecto sin bloqueos en `main` bajo una arquitectura híbrida SQLite/Orion y con interfaces tipo Tabla CSS pulidas y adaptables al *Dark Mode*. Al retomar el proyecto y arrancar el `start.sh`, reanudaremos la Metodología `GitHub Flow` (Plan ➔ Branch ➔ Desarrollo ➔ Pull Request ➔ Close Issue).
