# Plan de implementación: módulo de tareas

## Estado

Implementado. El comportamiento real está documentado en
[`../features/tasks.md`](../features/tasks.md). Este documento conserva las
decisiones y el orden de implementación de la primera feature de negocio sobre
la plataforma modular por espacio.

## Objetivo

Permitir que una persona organice tareas en su espacio personal y que los
miembros de un espacio compartido puedan crear, consultar y completar tareas
comunes, asignándolas a uno o varios miembros.

La primera versión debe ser útil sin introducir todavía automatizaciones,
recordatorios ni recurrencias. Una tarea siempre pertenece a un espacio y nunca
se comparte entre espacios.

## Alcance de esta entrega

- Crear, consultar, editar y eliminar tareas.
- Marcar una tarea como pendiente o completada.
- Añadir descripción opcional.
- Añadir fecha límite opcional.
- Definir prioridad: baja, normal o alta.
- Asignar una tarea a cero, uno o varios miembros del espacio.
- Filtrar tareas por estado, responsable y vencimiento.
- Ordenar por estado, fecha límite y fecha de creación.
- Usar el mismo módulo en espacios personales y compartidos.
- Mostrar la lista de tareas dentro del espacio activo de la PWA.
- Mantener el acceso bloqueado si el módulo está desactivado.

Quedan fuera de esta entrega las tareas recurrentes, subtareas, etiquetas,
comentarios, adjuntos, notificaciones y sincronización offline.

## Decisiones de producto

- La tarea pertenece al `Space`, no al usuario que la creó.
- Todos los miembros activos del espacio pueden consultar las tareas del
  espacio.
- Todos los miembros activos pueden crear y editar tareas del espacio.
- Todos los miembros activos pueden completar o eliminar tareas.
- El creador se conservará como dato de auditoría, pero no tendrá privilegios
  especiales sobre la tarea.
- En un espacio personal solo su propietario podrá crear asignaciones, aunque
  normalmente las tareas no necesitarán responsable explícito.
- Una tarea sin responsables será válida y representará una tarea común.
- Un responsable debe ser miembro activo del mismo espacio.
- Eliminar una tarea será una eliminación definitiva en esta primera versión.
- Desactivar el módulo no eliminará las tareas ni sus asignaciones.
- Reactivar el módulo hará que los datos vuelvan a estar disponibles.
- Las fechas límite serán fechas de calendario, no instantes horarios; se
  serializarán como `YYYY-MM-DD`.

## Modelo de dominio

Se añadirá una app Django independiente llamada `apps.tasks`.

### `Task`

- `space`: `ForeignKey` a `Space` con borrado en cascada.
- `title`: texto obligatorio, máximo 200 caracteres.
- `description`: texto opcional.
- `status`: `pending` o `completed`, con `pending` por defecto.
- `priority`: `low`, `normal` o `high`, con `normal` por defecto.
- `due_date`: fecha opcional.
- `created_by`: usuario que creó la tarea.
- `created_at` y `updated_at`.
- `completed_at`: instante opcional; se rellena al pasar a `completed` y se
  limpia al volver a `pending`.

Restricciones y reglas:

- `title` no puede quedar vacío después de eliminar espacios.
- `created_by` debe ser miembro del espacio en el momento de crear la tarea.
- El modelo no confiará en `space_id` enviado en el cuerpo para autorizar el
  acceso; el espacio vendrá de la ruta y del queryset autorizado.
- El orden por defecto será primero tareas pendientes, después `due_date` más
  cercana y finalmente `created_at` más reciente.

### `TaskAssignment`

Relación explícita entre una tarea y los usuarios responsables:

- `task`: `ForeignKey` a `Task`.
- `user`: `ForeignKey` al usuario de OwnTempo.
- `created_at`.

La combinación `task + user` será única. La aplicación validará que el usuario
asignado tenga una pertenencia activa al mismo espacio que la tarea. Si se
elimina una pertenencia, sus asignaciones se eliminarán o se limpiarán según
la decisión final de implementación; la primera opción es la preferida para
evitar mostrar responsables sin acceso al espacio.

No se usará una relación directa a `Membership` porque la pertenencia es una
relación de acceso y la tarea debe conservar una referencia estable al usuario.

## Catálogo y disponibilidad

La entrada existente `tasks` del catálogo se actualizará con:

- `app_label: "tasks"`.
- `available: true`.
- La ruta estable del módulo: `/spaces/{space_id}/tasks/`.

El resto de módulos seguirá marcado como no disponible. El módulo utilizará el
permiso común `HasActiveModule`, por lo que requerirá que `tasks` esté activo en
el espacio además de que el usuario sea miembro.

## API

Todas las rutas requerirán sesión autenticada, pertenencia al espacio y módulo
`tasks` activo. Las operaciones mutables usarán la protección CSRF ya existente.

### Listado y creación

```http
GET  /api/v1/spaces/{space_id}/tasks/
POST /api/v1/spaces/{space_id}/tasks/
```

Parámetros de consulta previstos para el listado:

```text
?status=pending|completed
?assigned_to={user_id}
?due=overdue|today|upcoming|none
```

El `POST` aceptará:

```json
{
  "title": "Comprar detergente",
  "description": "Comprobar si queda en el armario",
  "priority": "normal",
  "due_date": "2026-11-25",
  "assignee_ids": [12, 18]
}
```

`title` será obligatorio. El resto de campos será opcional. El backend
ignorará o rechazará campos desconocidos según la convención establecida para
los serializers del proyecto; se recomienda rechazarlos para detectar errores
del cliente pronto.

### Detalle y operaciones

```http
GET    /api/v1/spaces/{space_id}/tasks/{task_id}/
PATCH  /api/v1/spaces/{space_id}/tasks/{task_id}/
DELETE /api/v1/spaces/{space_id}/tasks/{task_id}/
```

El `PATCH` podrá modificar `title`, `description`, `priority`, `due_date`,
`status` y `assignee_ids`. Al cambiar `status`, el servicio actualizará
`completed_at` de forma consistente.

Respuesta mínima:

```json
{
  "id": 42,
  "space_id": 7,
  "title": "Comprar detergente",
  "description": "Comprobar si queda en el armario",
  "status": "pending",
  "priority": "normal",
  "due_date": "2026-11-25",
  "created_by": {
    "id": 4,
    "username": "ana"
  },
  "assignees": [
    {
      "id": 12,
      "username": "luis",
      "display_name": "Luis"
    }
  ],
  "completed_at": null,
  "created_at": "2026-11-21T10:00:00Z",
  "updated_at": "2026-11-21T10:00:00Z"
}
```

No se añadirá un endpoint específico para completar tareas: `PATCH` con
`status` cubre esa operación y evita duplicar reglas de negocio.

## Servicios y transacciones

La creación y actualización se implementarán mediante servicios de dominio,
no con lógica compleja dentro de las vistas:

- `create_task(user, space, validated_data)`.
- `update_task(user, task, validated_data)`.
- `delete_task(user, task)`.
- `set_task_assignees(task, user_ids)`.

Las operaciones que actualicen la tarea y sus asignaciones se ejecutarán dentro
de una transacción. Antes de guardar se comprobará que todos los usuarios
indicados pertenecen al mismo espacio; si uno no es válido, no se modificará
ninguna asignación.

Los querysets se filtrarán siempre por `space_id` y por la pertenencia del
usuario. Un `task_id` existente en otro espacio deberá producir `404`, sin
revelar que la tarea existe.

## Permisos

El orden de autorización será:

```text
sesión válida
    -> miembro del espacio
        -> módulo tasks activo y disponible
            -> operación sobre una tarea del mismo espacio
```

La vista combinará `IsAuthenticated`, `IsSpaceMember` y `HasActiveModule`.
Para el detalle, el queryset autorizado será la primera barrera de aislamiento;
no se permitirá recuperar una tarea de otro espacio mediante un identificador
conocido.

La primera versión no diferenciará permisos entre creador y resto de miembros.
La posibilidad de restringir eliminación o edición al creador queda para una
futura decisión de producto.

## PWA

### Navegación

- El enlace de `Tareas` aparecerá en el espacio activo cuando el módulo esté
  activo y disponible.
- La ruta incluirá el identificador del espacio para permitir enlaces directos
  sin perder el contexto.
- Si el módulo se desactiva mientras está abierto, la pantalla mostrará un
  aviso y volverá a la vista del espacio.
- El selector de espacio seguirá siendo la fuente del contexto actual.

### Vista de tareas

La primera pantalla incluirá:

1. Encabezado con nombre del espacio y botón para volver.
2. Acción principal para crear una tarea.
3. Filtros visibles para `Pendientes`, `Completadas` y `Todas`.
4. Lista de tarjetas con título, prioridad, fecha límite y responsables.
5. Acción rápida para completar o reabrir.
6. Menú de edición y eliminación.
7. Estado vacío específico para cada filtro.

El formulario de creación y edición tendrá título, descripción, prioridad,
fecha límite y selección múltiple de miembros. En el espacio personal no se
mostrará una selección de responsables innecesaria.

Estados de interfaz obligatorios:

- carga inicial;
- error de lectura;
- error de guardado;
- envío en curso;
- lista vacía;
- tarea sin fecha;
- tarea vencida;
- confirmación antes de eliminar.

La interfaz deberá ser usable con teclado, anunciar cambios de estado y
mantener el foco después de cerrar el formulario o completar una tarea.

## Orden de implementación

1. Crear `apps.tasks`, registrarla en `INSTALLED_APPS` y añadir la entrada de
   URL raíz.
2. Implementar `Task` y `TaskAssignment`, restricciones, índices y migración.
3. Actualizar el catálogo `tasks` como disponible.
4. Implementar serializers con validación de pertenencia de responsables.
5. Implementar servicios transaccionales de creación, actualización y borrado.
6. Implementar listados, detalle, filtros y endpoints protegidos.
7. Añadir pruebas de modelos, servicios, API, aislamiento y módulo desactivado.
8. Crear la API TypeScript para listar, crear, actualizar y eliminar tareas.
9. Añadir la ruta y la vista de tareas a la PWA.
10. Añadir formulario, filtros, estados vacíos y acciones rápidas.
11. Ejecutar typecheck, lint, build y la suite de Django.
12. Documentar el comportamiento real en `docs/features/tasks.md` y actualizar
    el roadmap cuando la feature esté verificada.

## Pruebas mínimas

### Modelo y servicios

- No se puede crear una tarea con título vacío.
- Se aplican los valores por defecto de estado y prioridad.
- `completed_at` se rellena al completar una tarea.
- `completed_at` se limpia al reabrirla.
- Una tarea puede tener cero, uno o varios responsables.
- No se puede asignar un usuario que no pertenezca al espacio.
- No se pueden duplicar asignaciones.
- Actualizar asignaciones reemplaza el conjunto de forma atómica.
- Eliminar una tarea elimina sus asignaciones.
- Las tareas de un espacio no aparecen en otro.

### API y autorización

- Un usuario anónimo no puede listar ni modificar tareas.
- Un miembro puede listar y operar sobre tareas de su espacio.
- Un usuario ajeno recibe `404` al consultar una tarea de otro espacio.
- Un miembro no puede crear una tarea indicando otro `space_id` en el cuerpo.
- Un usuario no puede asignar personas de otro espacio.
- Un módulo desactivado bloquea listado, detalle y mutaciones.
- Un módulo no disponible no puede abrirse aunque esté activado en la base de
  datos.
- `PATCH` valida transiciones de estado y fechas correctamente.
- `DELETE` requiere pertenencia y módulo activo.

### PWA

- Tareas aparece solo en el espacio correcto y cuando está disponible.
- Cambiar de espacio recarga las tareas sin mezclar datos.
- Crear y editar una tarea actualiza la lista sin recargar la página.
- Completar y reabrir una tarea mantiene el foco y el filtro actual.
- Los errores de API se muestran con mensajes comprensibles.
- El formulario funciona en móvil, escritorio y con teclado.
- El estado vacío diferencia entre no tener tareas y no tener resultados para
  un filtro.

## Criterios de aceptación

La feature se considerará completada cuando:

1. Una persona pueda crear una tarea en su espacio personal y verla después.
2. Un miembro pueda crear una tarea en un espacio compartido y asignarla a uno
   o varios miembros.
3. Los miembros puedan completar, reabrir, editar y eliminar tareas del espacio.
4. Las tareas puedan filtrarse por estado, responsable y vencimiento.
5. Ningún usuario pueda descubrir ni modificar tareas de otro espacio.
6. Desactivar `tasks` bloquee la API y la navegación sin borrar los datos.
7. Reactivar `tasks` restaure el acceso a las tareas existentes.
8. La suite backend y las comprobaciones frontend pasen sin errores.
9. El comportamiento implementado quede documentado como feature verificada.

## Fuera de alcance

- Tareas recurrentes.
- Recordatorios, notificaciones push o correo.
- Subtareas y dependencias entre tareas.
- Etiquetas y categorías personalizadas.
- Comentarios, actividad y menciones.
- Archivos adjuntos.
- Historial de cambios.
- Sincronización offline y resolución de conflictos.
- Panel inicial configurable y resúmenes agregados de tareas.
- Permisos distintos por tarea dentro del mismo espacio.
