# Listas de la compra personales y compartidas

## Estado

Implementada y verificada. Es el segundo módulo de negocio disponible en la
plataforma modular de OwnTempo.

## Comportamiento

Cada lista pertenece a un único espacio personal o compartido. Un espacio puede
tener varias listas, incluso con el mismo nombre, y sus datos nunca se mezclan
con los de otro espacio.

Una lista incluye nombre, creador, fechas de auditoría y contadores de productos
pendientes, comprados y totales. Cada producto incluye:

- nombre obligatorio;
- cantidad y unidad opcionales como texto libre;
- nota opcional;
- estado `pending` o `purchased`;
- posición manual dentro de la lista;
- creador y fechas de auditoría;
- fecha de compra, gestionada automáticamente con el estado.

Los productos pendientes aparecen antes que los comprados. Dentro de cada grupo
se conserva el orden manual. Marcar un producto como comprado asigna su fecha de
compra; restaurarlo la elimina sin perder cantidad, unidad ni nota.

Todos los miembros activos del espacio pueden crear, editar y eliminar listas y
productos, cambiar estados y reordenar. Desactivar el módulo bloquea sus rutas y
su interfaz, pero conserva todos los datos.

## Modelo de datos

La app `apps.shopping` define:

- `ShoppingList`, vinculada directamente con `Space` y su creador.
- `ShoppingItem`, vinculada con una lista y su creador.

La base de datos garantiza una posición única por lista y que `purchased_at`
concuerde con el estado. La creación bloquea la lista mientras calcula la
siguiente posición y la reordenación se ejecuta dentro de una transacción.

## API

```http
GET    /api/v1/spaces/{space_id}/shopping/lists/
POST   /api/v1/spaces/{space_id}/shopping/lists/
GET    /api/v1/spaces/{space_id}/shopping/lists/{list_id}/
PATCH  /api/v1/spaces/{space_id}/shopping/lists/{list_id}/
DELETE /api/v1/spaces/{space_id}/shopping/lists/{list_id}/

POST   /api/v1/spaces/{space_id}/shopping/lists/{list_id}/items/
PATCH  /api/v1/spaces/{space_id}/shopping/lists/{list_id}/items/{item_id}/
DELETE /api/v1/spaces/{space_id}/shopping/lists/{list_id}/items/{item_id}/
POST   /api/v1/spaces/{space_id}/shopping/lists/{list_id}/items/reorder/
```

El detalle admite `status=pending`, `status=purchased` y `status=all`. Los
contadores siempre describen la lista completa aunque los productos estén
filtrados.

Todas las rutas requieren sesión, pertenencia activa y el módulo `shopping`
activo. Las consultas acotan lista y producto por el espacio de la URL para que
un identificador externo responda como no encontrado.

## PWA

La ruta `/spaces/{space_id}/shopping/` ofrece:

- selección y creación de listas;
- contadores de pendientes por lista;
- renombrado y eliminación con confirmación;
- formulario rápido para productos, cantidad, unidad y nota;
- edición, eliminación y marcado con una interacción;
- filtros de pendientes, comprados y todos;
- controles accesibles para reordenar dentro de cada estado;
- estados de carga, error, lista vacía y compra completada;
- diseño adaptable a móvil y escritorio.

La PWA vuelve a comprobar la activación del módulo al recuperar el foco. Si se
desactiva desde otra sesión, regresa al inicio sin exponer operaciones obsoletas.

## Verificación realizada

- Validación y normalización de listas y productos.
- Coherencia entre estado y fecha de compra.
- Posiciones únicas y reordenación completa y atómica.
- Resúmenes y filtros de estado.
- CRUD por miembros y aislamiento entre espacios.
- Bloqueo completo al desactivar el módulo sin pérdida de datos.
- Cascada controlada de productos al eliminar una lista.
- Suite completa de Django.
- TypeScript, ESLint y build de producción de la PWA.

## Fuera de alcance

- Precios, presupuestos e inventario.
- Catálogo de productos o códigos de barras.
- Tiendas, categorías y pasillos.
- Generación desde recetas.
- Compartición entre espacios.
- Historial, papelera, recordatorios y sincronización offline de datos.
