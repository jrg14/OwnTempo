# Lista de deseos personal y compartida

## Estado

Implementada y verificada. Es el tercer módulo de negocio disponible en la
plataforma modular de OwnTempo.

## Comportamiento

Cada deseo pertenece a un único espacio personal o compartido. Todos los
miembros activos del espacio pueden verlo, crearlo, editarlo, cambiar su estado
y eliminarlo.

Un deseo contiene:

- título obligatorio y descripción opcional;
- tipo `product`, `experience` o `idea`;
- estado `pending`, `obtained` o `dismissed`;
- prioridad `low`, `normal` o `high`;
- enlace HTTP/HTTPS e imagen remota opcionales;
- precio decimal no negativo y moneda de tres letras opcionales;
- creador y fechas de auditoría;
- fecha de consecución gestionada automáticamente.

Los deseos pendientes aparecen primero, ordenados por prioridad alta, normal y
baja, y después por fecha de creación. Marcar un deseo como conseguido asigna
`obtained_at`; restaurarlo o descartarlo elimina esa fecha sin perder el resto de
los datos.

## Modelo y validación

La app `apps.wishlist` define `WishItem`, vinculado directamente con `Space` y
con su creador. La base de datos comprueba que el precio no sea negativo y que la
fecha de consecución concuerde con el estado.

El modelo y la API normalizan títulos, descripciones y monedas. Los enlaces solo
aceptan los esquemas HTTP y HTTPS. El backend valida su sintaxis, pero no visita,
descarga ni analiza el contenido remoto.

## API

```http
GET    /api/v1/spaces/{space_id}/wishlist/
POST   /api/v1/spaces/{space_id}/wishlist/
GET    /api/v1/spaces/{space_id}/wishlist/{wish_id}/
PATCH  /api/v1/spaces/{space_id}/wishlist/{wish_id}/
DELETE /api/v1/spaces/{space_id}/wishlist/{wish_id}/
```

El listado admite filtros combinables por `status`, `kind` y `priority`. Su
respuesta incluye los resultados filtrados y contadores globales de pendientes,
conseguidos, descartados y total del espacio.

Todas las rutas requieren sesión, pertenencia activa y el módulo `wishlist`
activo. Los querysets siempre parten del espacio de la URL, por lo que un
identificador de otro espacio no permite descubrir ni modificar datos ajenos.

## PWA

La ruta `/spaces/{space_id}/wishlist/` ofrece:

- resumen por estado;
- filtros por estado, tipo y prioridad;
- tarjetas responsive con metadatos y precio;
- creación y edición mediante formulario validado;
- enlaces externos seguros en una pestaña nueva;
- imágenes opcionales que se ocultan si no pueden cargarse;
- acciones para conseguir, descartar, restaurar y eliminar;
- estados de carga, error, vacío y ausencia de coincidencias.

La PWA vuelve a comprobar la disponibilidad del módulo al recuperar el foco. Al
desactivarlo, se bloquea el acceso sin eliminar los deseos existentes.

## Verificación realizada

- Valores iniciales y normalización de campos.
- Coherencia entre estado y fecha de consecución.
- Rechazo de precios negativos y esquemas de URL inseguros.
- CRUD completo por miembros activos.
- Filtros combinados y contadores globales.
- Aislamiento entre espacios y bloqueo por módulo desactivado.
- Migración sincronizada con los modelos.
- Suite completa de Django.
- TypeScript, ESLint y build de producción de la PWA.

## Fuera de alcance

- Compras, pagos y reservas.
- Seguimiento de precios o disponibilidad.
- Importación automática desde tiendas.
- Categorías configurables, comentarios o votaciones.
- Recomendaciones, recordatorios y sincronización offline de datos.
