# Plan de implementación: lista de deseos

## Estado

Implementado. El comportamiento real está documentado en
[`../features/wishlist.md`](../features/wishlist.md). Este documento conserva las
decisiones y el orden seguido para la primera versión del módulo `wishlist` sobre
la plataforma modular por espacio.

## Objetivo

Permitir que una persona guarde productos, experiencias e ideas que quiere
recordar para más adelante, tanto en su espacio personal como en un espacio
compartido. La feature debe servir como una colección ligera y consultable, sin
convertirse todavía en un catálogo de compras ni en un sistema de seguimiento
de precios.

## Alcance de esta entrega

- Crear, consultar, editar y eliminar deseos.
- Guardar título obligatorio y descripción opcional.
- Clasificar un deseo como `product`, `experience` o `idea`.
- Añadir una URL opcional y una imagen remota opcional como referencia.
- Añadir precio y moneda opcionales, sin cálculos ni conversión.
- Definir prioridad `low`, `normal` o `high`.
- Marcar un deseo como pendiente, conseguido o descartado.
- Filtrar por estado, tipo y prioridad.
- Ordenar por estado, prioridad y fecha de creación.
- Utilizar el mismo módulo en espacios personales y compartidos.
- Conservar los datos cuando el módulo se desactive.

## Decisiones de producto

- Un deseo pertenece a un único espacio y nunca se comparte entre espacios.
- Todos los miembros activos de un espacio pueden consultar, crear, editar,
  completar y eliminar deseos.
- Una entrada nueva empieza con estado `pending` y prioridad `normal`.
- `obtained` representa algo conseguido o realizado; `dismissed` representa una
  idea que ya no interesa. Ambos estados se conservan para mantener contexto.
- Marcar un deseo como conseguido o descartado no elimina sus datos ni su URL.
- El título es obligatorio y se guarda sin espacios exteriores.
- La URL se validará como enlace HTTP o HTTPS; no se descargarán ni procesarán
  contenidos externos desde el backend.
- El precio será un decimal positivo opcional y la moneda será un código de tres
  letras, por defecto `EUR` cuando se indique precio.
- El orden por defecto mostrará primero deseos pendientes, después prioridad alta
  y finalmente los más recientes.
- No habrá reservas, compras, notificaciones ni seguimiento automático del precio.

## Modelo de dominio

Se añadirá una app Django independiente llamada `apps.wishlist`.

### `WishItem`

- `space`: espacio propietario del deseo.
- `title`: título obligatorio, máximo 200 caracteres.
- `description`: descripción opcional, máximo 2.000 caracteres.
- `kind`: `product`, `experience` o `idea`.
- `status`: `pending`, `obtained` o `dismissed`.
- `priority`: `low`, `normal` o `high`.
- `url`: enlace HTTP o HTTPS opcional.
- `image_url`: enlace HTTP o HTTPS opcional a una imagen de referencia.
- `price`: importe decimal positivo opcional, con dos decimales.
- `currency`: código ISO de tres letras, por defecto `EUR`.
- `created_by`: usuario miembro que creó el deseo.
- `obtained_at`: fecha y hora en que se marcó como conseguido.
- `created_at` y `updated_at`.

Restricciones:

- El creador debe pertenecer al espacio.
- `title` no puede quedar vacío después de recortarlo.
- `price` no puede ser negativo.
- `currency` se normalizará a mayúsculas.
- `obtained_at` debe ser nulo mientras el estado no sea `obtained` y tener valor
  cuando el estado sea `obtained`.
- Los deseos descartados no tendrán una fecha especial de eliminación.

No se creará una tabla de categorías personalizables en esta primera versión.
El tipo fijo permite filtros útiles sin introducir configuración adicional por
espacio.

## Catálogo y disponibilidad

La plataforma modular ya contiene la entrada estable `wishlist`. Al completar
la implementación se añadirá `app_label="wishlist"` y se marcará
`available=true` en el catálogo.

Los endpoints exigirán pertenencia al espacio y módulo activo y disponible. Al
desactivarlo se bloqueará el acceso, pero los deseos permanecerán almacenados.

## API

Todas las rutas requerirán sesión autenticada, pertenencia activa al espacio y
el módulo `wishlist` activo.

### Listado y detalle

```http
GET    /api/v1/spaces/{space_id}/wishlist/
POST   /api/v1/spaces/{space_id}/wishlist/
GET    /api/v1/spaces/{space_id}/wishlist/{wish_id}/
PATCH  /api/v1/spaces/{space_id}/wishlist/{wish_id}/
DELETE /api/v1/spaces/{space_id}/wishlist/{wish_id}/
```

El listado admitirá:

```text
status=pending|obtained|dismissed|all
kind=product|experience|idea
priority=low|normal|high
```

La respuesta incluirá contadores del conjunto completo del espacio para que la
PWA pueda mostrar un resumen sin hacer una petición adicional:

```json
{
  "id": 12,
  "title": "Curso de cerámica",
  "kind": "experience",
  "status": "pending",
  "priority": "high",
  "description": "Buscar una opción de fin de semana.",
  "url": null,
  "image_url": null,
  "price": null,
  "currency": "EUR",
  "obtained_at": null,
  "created_by": 4,
  "created_at": "2026-11-21T10:30:00Z",
  "updated_at": "2026-11-21T10:30:00Z"
}
```

### Operaciones de estado

El estado se actualizará mediante `PATCH` para mantener una API pequeña:

```json
{
  "status": "obtained"
}
```

El backend asignará `obtained_at` automáticamente al conseguir un deseo y lo
limpiará al devolverlo a `pending` o `dismissed`. No se aceptará directamente
`obtained_at` desde el cliente.

## Servicios y transacciones

La creación y actualización se implementarán mediante servicios de dominio:

- `create_wish(user, space, validated_data)`.
- `update_wish(wish, validated_data)`.
- `set_wish_status(wish, status)`.

El cambio de estado será atómico y conservará la coherencia entre `status` y
`obtained_at`. Las consultas partirán siempre del espacio solicitado y usarán
ordenación e índices adecuados para los filtros de estado, tipo y prioridad.

Los enlaces se validarán sintácticamente. La aplicación no hará peticiones a
dominios remotos durante la creación, listado o renderizado de un deseo.

## Permisos y aislamiento

- Un usuario anónimo no puede acceder a las rutas.
- Un usuario que no sea miembro activo no puede descubrir deseos.
- Todos los miembros activos pueden operar sobre los deseos de su espacio.
- El módulo desactivado bloquea lectura y escritura.
- Un identificador de otro espacio debe responder como no encontrado dentro del
  queryset autorizado.
- La eliminación del creador no debe borrar los deseos que creó; se conservará
  la política de protección de datos del proyecto.

No habrá privacidad individual por deseo en esta primera versión: en un espacio
compartido todos los deseos serán visibles para sus miembros.

## PWA

### Navegación

El módulo se abrirá desde el espacio activo mediante la ruta estable
`/spaces/{space_id}/wishlist/`.

La pantalla tendrá:

1. Resumen con deseos pendientes, conseguidos y descartados.
2. Filtros por estado, tipo y prioridad.
3. Listado de tarjetas de deseos.
4. Acción visible para crear un deseo.
5. Formulario de edición y acción para cambiar el estado.

### Tarjeta de deseo

Cada tarjeta podrá mostrar:

- título y tipo;
- prioridad;
- descripción;
- precio y moneda, si existen;
- enlace externo, abriendo una pestaña nueva con relación segura;
- estado y fecha de consecución cuando corresponda;
- acciones accesibles para editar, cambiar estado y eliminar.

Estados de interfaz obligatorios:

- carga inicial;
- error de carga y reintento;
- estado vacío sin deseos;
- ausencia de resultados para un filtro;
- formulario con errores de validación;
- guardado correcto;
- módulo desactivado o no disponible.

La imagen remota será opcional y decorativa; si falla no podrá romper la tarjeta
ni ocultar el título o las acciones.

## Orden de implementación

1. Crear `apps.wishlist`, modelos, migración y administración Django.
2. Añadir servicios de dominio para CRUD y cambios de estado.
3. Añadir serializers, validaciones, vistas, URLs y permisos del módulo.
4. Añadir índices, filtros y ordenación estable de la API.
5. Implementar pruebas de modelo, servicios, API y aislamiento entre espacios.
6. Activar `wishlist` como módulo disponible tras superar las pruebas backend.
7. Crear tipos y clientes de API en la PWA.
8. Implementar listado, filtros, tarjetas y formulario de deseos.
9. Implementar estados, enlaces externos y estados de carga/error.
10. Actualizar documentación de feature, roadmap y verificación final.

## Pruebas mínimas

### Modelo y servicios

- El título se recorta y no admite valores vacíos.
- Los tipos, estados y prioridades solo aceptan valores del catálogo.
- La URL y la imagen aceptan HTTP/HTTPS y rechazan esquemas inseguros.
- El precio no puede ser negativo y la moneda se normaliza.
- El estado inicial es `pending` y la prioridad inicial `normal`.
- Marcar como conseguido asigna `obtained_at`.
- Volver a pendiente o descartar limpia `obtained_at`.
- Un creador que no pertenezca al espacio no puede crear deseos.

### API y autorización

- Un miembro puede crear, listar, editar, cambiar de estado y eliminar deseos.
- Los filtros por estado, tipo y prioridad funcionan de forma combinada.
- Un usuario ajeno recibe una respuesta de autorización sin descubrir datos.
- No se puede leer o modificar un deseo de otro espacio manipulando el ID.
- El módulo desactivado bloquea todos sus endpoints sin borrar datos.
- El listado mantiene contadores completos aunque se aplique un filtro.

### PWA

- El usuario puede crear un deseo con los campos obligatorios y opcionales.
- Los filtros actualizan el listado y el resumen correctamente.
- El cambio de estado actualiza la tarjeta sin perder los metadatos.
- Los enlaces externos son accesibles y seguros.
- Una imagen rota mantiene la tarjeta operativa.
- Se muestran correctamente carga, vacío, error y módulo no disponible.

## Criterios de aceptación

El módulo se considerará completado cuando:

1. Un miembro pueda guardar y gestionar productos, experiencias e ideas.
2. Los deseos puedan clasificarse, priorizarse y filtrarse.
3. Los estados pendiente, conseguido y descartado conserven sus datos.
4. `obtained_at` sea coherente y gestionado por el backend.
5. Los enlaces y precios opcionales se validen sin dependencias externas.
6. Todos los endpoints estén aislados por espacio y módulo activo.
7. La PWA cubra los estados de carga, vacío, error y guardado.
8. La suite backend, el typecheck, el lint y el build frontend pasen.
9. El comportamiento real quede documentado en `docs/features/` y el roadmap
   refleje la feature como completada.

## Fuera de alcance

- Compras, reservas o pagos.
- Seguimiento automático de precios o disponibilidad.
- Scraping o importación automática desde tiendas.
- Catálogos compartidos y categorías configurables.
- Recomendaciones personalizadas.
- Comentarios, votaciones o asignación individual de deseos.
- Notificaciones, recordatorios y funcionamiento offline completo.
