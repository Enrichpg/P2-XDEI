# AGENTS.md

## Instrucciones generales

- Al finalizar la implementación de cada issue, actualizar siempre `PRD.md`, `architecture.md` y `data_model.md` para reflejar los cambios introducidos.

## Principios de interfaz HTML + CSS + JS

- Cuando algo se pueda hacer tanto mediante CSS como mediante JS, usar **CSS**.
- Evitar al máximo generar código HTML en el código JS. Siempre que se pueda, el código JS deberá actualizar el valor de los atributos de elementos HTML ya presentes en la página en lugar de añadir nuevos elementos.

## Flujos de Trabajo y Calidad

- Siempre actualizar `PRD.md`, `architecture.md` y `data_model.md` después de cada issue para mantener la coherencia técnica.
- **Revisiones**: No hacer merge de Pull Requests sin revisión previa del propietario del repositorio (Enrichpg).
- **Base de datos**: Borrar el archivo `smart_store.db` al realizar cambios en el esquema de SQLAlchemy para forzar la regeneración de tablas limpias.
