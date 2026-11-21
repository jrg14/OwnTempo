# Plan de implementación: listas de la compra

## Estado

Implementado. El comportamiento real está documentado en
[`../features/shopping-lists.md`](../features/shopping-lists.md). Este documento
conserva las decisiones y el orden seguido para la primera versión del módulo
`shopping` sobre la plataforma modular por espacio.

## Objetivo

Permitir que una persona gestione sus compras en el espacio personal y que los
miembros de un espacio compartido puedan mantener listas comunes, añadir
productos y marcarlos como comprados sin mezclar información entre espacios.

La primera versión debe ser rápida de utilizar desde el móvil. No incluirá
precios, cantidades calculadas, inventario ni sincronización con tiendas.

## Alcance de esta entrega

- Crear, consultar, editar y eliminar listas.
- Crear, editar, reordenar y eliminar productos de una lista.
- Marcar un producto como pendiente o comprado.
- Restaurar un producto comprado a pendiente.
- Definir cantidad y unidad opcionales como texto libre.
- Añadir una nota opcional a cada producto.
- Consultar el progreso de una lista y filtrar productos por estado.
- Utilizar el mismo módulo en espacios personales y compartidos.
- Conservar los datos cuando el módulo se desactive.

## Decisiones de producto

- Una lista pertenece a un único espacio.
- Un espacio puede tener varias listas, pero cada lista tiene un único nombre.
- Todos los miembros activos del espacio pueden consultar, crear, editar,
  completar y eliminar listas y productos.
- Una lista nueva empieza vacía y activa.
- Un producto comprado permanece en la lista hasta que se elimine o se vuelva a
  marcar como pendiente.
- La compra se registra por producto, no por lista completa.
- El orden manual de los productos será el orden principal de presentación.
- Los productos pendientes aparecerán antes que los comprados por defecto,
  conservando el orden manual dentro de cada grupo.
- El texto del producto es obligatorio y se guardará sin espacios exteriores.
- No se crearán catálogos globales de productos ni sugerencias automáticas.
- Las fechas de creación y modificación servirán para auditoría; no habrá
  historial de cambios en esta versión.

## Modelo de dominio

Se añadirá una app Django independiente llamada `apps.shopping`.

### `ShoppingList`

- `space`: espacio propietario de la lista.
- `name`: nombre obligatorio de la lista, con un máximo de 120 caracteres.
- `created_by`: usuario miembro que la creó.
- `created_at` y `updated_at`.

Restricciones:

- El espacio y el creador deben existir.
- El creador debe pertenecer al espacio en el momento de crear la lista.
- El nombre no puede quedar vacío después de recortarlo.
- No se exigirá unicidad del nombre: pueden existir, por ejemplo, dos listas
  llamadas `Supermercado` con finalidades distintas.

### `ShoppingItem`

- `shopping_list`: lista a la que pertenece.
- `name`: producto o artículo obligatorio, con un máximo de 200 caracteres.
- `quantity`: cantidad opcional como texto, por ejemplo `2` o `medio kilo`.
- `unit`: unidad opcional, por ejemplo `uds`, `kg` o `paquetes`.
- `note`: nota opcional, como marca o variedad.
- `status`: `pending` o `purchased`, con valor inicial `pending`.
- `position`: entero no negativo para el orden manual.
- `created_by`: usuario que añadió el producto.
- `purchased_at`: fecha y hora de compra, nula mientras esté pendiente.
- `created_at` y `updated_at`.

Restricciones:

- La lista y el creador deben pertenecer al mismo espacio.
- `position` será único dentro de la lista cuando sea posible; el servicio de
  reordenación será la fuente de verdad para evitar colisiones.
- Un producto pendiente tendrá `purchased_at` nulo y uno comprado tendrá valor.
- El cambio de estado se hará mediante servicio para mantener ambos campos
  sincronizados.

No se eliminarán automáticamente los productos comprados al cerrar una lista.
Una futura función de limpieza podrá archivarlos explícitamente.

## Catálogo y disponibilidad

La plataforma modular ya contiene la entrada estable `shopping`, con la ruta y
el estado de disponibilidad. Al completar esta implementación se actualizará
`available` para que los miembros puedan abrir el módulo.

Los endpoints deberán exigir pertenencia al espacio y módulo activo y
disponible. Si el módulo se desactiva, las listas y productos permanecerán en
la base de datos y el acceso funcional devolverá el error común de módulo no
disponible.

## API

Todas las rutas requerirán sesión autenticada, pertenencia activa al espacio y
el módulo `shopping` activo.

### Listas

```http
GET    /api/v1/spaces/{space_id}/shopping/lists/
POST   /api/v1/spaces/{space_id}/shopping/lists/
GET    /api/v1/spaces/{space_id}/shopping/lists/{list_id}/
PATCH  /api/v1/spaces/{space_id}/shopping/lists/{list_id}/
DELETE /api/v1/spaces/{space_id}/shopping/lists/{list_id}/
```

El listado devolverá las listas del espacio, ordenadas por `updated_at`
descendente, junto con un resumen mínimo:

```json
{
  "id": 12,
  "name": "Supermercado",
  "pending_count": 8,
  "purchased_count": 3,
  "item_count": 11,
  "created_by": 4,
  "updated_at": "2026-11-21T10:30:00Z"
}
```

### Productos

```http
POST   /api/v1/spaces/{space_id}/shopping/lists/{list_id}/items/
PATCH  /api/v1/spaces/{space_id}/shopping/lists/{list_id}/items/{item_id}/
DELETE /api/v1/spaces/{space_id}/shopping/lists/{list_id}/items/{item_id}/
POST   /api/v1/spaces/{space_id}/shopping/lists/{list_id}/items/reorder/
```

La respuesta de detalle incluirá los productos y el resumen de la lista. Se
admitirá un filtro `status=pending|purchased|all`; por defecto se devolverán
todos, con pendientes primero.

La operación de estado podrá utilizar el mismo `PATCH` del producto:

```json
{
  "status": "purchased"
}
```

La reordenación recibirá una lista completa de identificadores pertenecientes a
la lista:

```json
{
  "item_ids": [18, 12, 14, 19]
}
```

El backend rechazará identificadores duplicados, ausentes o pertenecientes a
otra lista. Las operaciones de eliminación serán idempotentes únicamente dentro
de la autorización del espacio; nunca se podrá borrar un objeto de otro
espacio.

## Servicios y transacciones

La creación y actualización se implementarán mediante servicios de dominio,
siguiendo el patrón utilizado por `apps.tasks`:

- `create_shopping_list(user, space, validated_data)`.
- `update_shopping_list(shopping_list, validated_data)`.
- `create_shopping_item(user, shopping_list, validated_data)`.
- `update_shopping_item(shopping_item, validated_data)`.
- `set_item_status(shopping_item, status)`.
- `reorder_shopping_items(shopping_list, item_ids)`.

Las operaciones de estado y reordenación serán atómicas. El servicio de estado
asignará `purchased_at` al marcar como comprado y lo limpiará al restaurar el
producto. El servicio de reordenación bloqueará la lista o sus productos cuando
sea necesario para evitar resultados parciales.

Las consultas siempre partirán del espacio solicitado y usarán `select_related`
o agregaciones para evitar mezclar listas y reducir consultas en los resúmenes.

## Permisos y aislamiento

- Un usuario anónimo no puede acceder a ninguna ruta.
- Un usuario que no sea miembro activo no puede descubrir listas ni productos.
- Todos los miembros activos pueden ejecutar las operaciones del alcance.
- El módulo desactivado bloquea catálogo de negocio, lectura y escritura.
- Los identificadores recibidos por URL se validarán dentro del espacio actual.
- La eliminación del usuario creador no eliminará listas ni productos; se
  aplicará la política de protección de datos ya utilizada por el proyecto.

No habrá permisos individuales por lista en esta primera versión. La unidad de
privacidad y autorización seguirá siendo el espacio.

## PWA

### Navegación

El módulo se abrirá desde el espacio activo mediante la ruta estable de
`shopping`. La pantalla tendrá:

1. Selector o listado de listas.
2. Vista de detalle de la lista seleccionada.
3. Acción visible para crear una lista.
4. Acción para añadir productos rápidamente.

### Vista de lista

La interfaz deberá:

- Mostrar nombre, progreso y contador de pendientes.
- Separar visualmente productos pendientes y comprados.
- Permitir marcar y desmarcar productos con una interacción de un toque.
- Mostrar cantidad, unidad y nota solo cuando existan.
- Permitir editar y eliminar mediante acciones accesibles.
- Permitir reordenar productos pendientes desde móvil.
- Mantener visibles los productos comprados, con menor énfasis visual.
- Confirmar las operaciones destructivas.

Estados de interfaz obligatorios:

- carga de listas;
- error de carga;
- espacio sin listas;
- lista vacía;
- lista con todos los productos comprados;
- guardado correcto;
- error de validación;
- módulo desactivado o no disponible.

La interfaz no deberá perder cambios locales al cambiar de lista durante una
petición. Los errores se mostrarán cerca de la operación afectada y no solo en
un aviso global.

## Orden de implementación

1. Crear `apps.shopping`, modelos, migración y registro en Django.
2. Añadir servicios de dominio para listas, productos, estados y orden.
3. Añadir serializers, vistas, URLs y permisos del módulo.
4. Añadir índices, agregaciones de resumen y filtros de estado.
5. Implementar pruebas de modelo, servicios, API y aislamiento entre espacios.
6. Activar `shopping` como módulo disponible tras superar las pruebas backend.
7. Crear hooks y tipos de API en la PWA.
8. Implementar listado, detalle, creación y edición de listas y productos.
9. Implementar marcado rápido, reordenación y estados de error.
10. Actualizar documentación de feature, roadmap y verificación final.

## Pruebas mínimas

### Modelo y servicios

- Una lista exige nombre no vacío y espacio válido.
- Un producto exige nombre no vacío y lista válida.
- La cantidad, unidad y nota son opcionales.
- El estado inicial de un producto es `pending`.
- Marcar como comprado asigna `purchased_at`.
- Restaurar un producto limpia `purchased_at`.
- La reordenación conserva exactamente todos los productos de la lista.
- La reordenación rechaza duplicados, ausentes y productos de otra lista.
- Los resúmenes cuentan correctamente pendientes, comprados y totales.

### API y autorización

- Un miembro puede listar y modificar datos de su espacio.
- Un usuario ajeno recibe `403` o `404` según el contrato común, sin filtrar
  existencia de datos.
- No se puede leer, editar o eliminar una lista de otro espacio manipulando el
  identificador.
- El módulo desactivado bloquea todos sus endpoints de negocio.
- Los filtros `pending`, `purchased` y `all` devuelven resultados correctos.
- La eliminación de una lista elimina sus productos de forma controlada.

### PWA

- Se muestran listas y resúmenes del espacio activo correcto.
- El marcado rápido actualiza el contador y la sección visual.
- Se puede crear y editar una lista y sus productos.
- El orden manual se conserva después de recargar.
- Se muestran correctamente carga, vacío, error y módulo no disponible.
- La vista funciona en móvil y escritorio sin acciones inaccesibles.

## Criterios de aceptación

El módulo se considerará completado cuando:

1. Un miembro pueda crear y gestionar varias listas en su espacio.
2. Los productos puedan añadirse con cantidad, unidad y nota opcionales.
3. Los productos puedan marcarse y restaurarse sin perder sus datos.
4. Las listas muestren progreso fiable entre pendientes y comprados.
5. El orden manual se mantenga en la API y en la PWA.
6. Todos los endpoints estén aislados por espacio y módulo activo.
7. La PWA cubra los estados de carga, vacío, error y guardado.
8. La suite backend, el typecheck, el lint y el build frontend pasen.
9. El comportamiento real quede documentado en `docs/features/` y el roadmap
   refleje la feature como completada.

## Fuera de alcance

- Precios, presupuestos y cálculo del coste total.
- Inventario doméstico y control de existencias.
- Catálogo de productos, códigos de barras o escáner.
- Categorías, tiendas o pasillos configurables.
- Recetas, cantidades derivadas y listas generadas automáticamente.
- Compartición de una lista entre espacios.
- Historial de cambios, papelera o archivado automático.
- Notificaciones, recordatorios y funcionamiento offline completo.
