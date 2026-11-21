# Tareas personales y compartidas

## Estado

Implementada y verificada. Es el primer módulo de negocio disponible en la
plataforma modular de OwnTempo.

## Comportamiento

Cada tarea pertenece a un único espacio. Puede utilizarse en el espacio personal
o en un espacio compartido, sin mezclar datos entre contextos.

Una tarea incluye:

- título obligatorio;
- descripción opcional;
- estado `pending` o `completed`;
- prioridad `low`, `normal` o `high`;
- fecha límite opcional;
- cero, uno o varios responsables;
- creador y fechas de auditoría;
- fecha de finalización, gestionada automáticamente con el estado.

Todos los miembros del espacio pueden crear, editar, completar, reabrir y
eliminar tareas. Una tarea sin responsables representa trabajo común. Los
responsables deben ser miembros activos del mismo espacio.

Al retirar o abandonar un miembro, sus asignaciones se eliminan. Las tareas se
conservan. Desactivar el módulo también conserva todos sus datos y solo bloquea
temporalmente el acceso.

## Modelo de datos

La app `apps.tasks` define:

### `Task`

- relación directa con `Space`;
- título, descripción, estado, prioridad y fecha límite;
- relación con el usuario creador;
- `completed_at`, `created_at` y `updated_at`;
- índices por espacio y estado, y por espacio y fecha límite;
- restricción que mantiene `status` y `completed_at` sincronizados.

### `TaskAssignment`

- relación con `Task` y usuario;
- combinación tarea y usuario única;
- validación de pertenencia al espacio;
- limpieza automática cuando desaparece la pertenencia.

## API

```http
GET    /api/v1/spaces/{space_id}/tasks/
POST   /api/v1/spaces/{space_id}/tasks/
GET    /api/v1/spaces/{space_id}/tasks/{task_id}/
PATCH  /api/v1/spaces/{space_id}/tasks/{task_id}/
DELETE /api/v1/spaces/{space_id}/tasks/{task_id}/
```

El listado admite filtros por:

- `status=pending|completed`;
- `assigned_to={user_id}`;
- `due=overdue|today|upcoming|none`.

Las mutaciones de tarea y asignaciones son atómicas. El espacio se obtiene de
la ruta; no se acepta como autoridad un identificador enviado en el cuerpo.

## Permisos y aislamiento

Todas las rutas requieren:

1. sesión autenticada;
2. pertenencia al espacio;
3. módulo `tasks` activo y disponible;
4. tarea perteneciente al espacio de la ruta.

Los querysets se filtran por espacio. Un identificador de tarea perteneciente a
otro espacio responde como recurso no encontrado y no expone sus datos.

## PWA

La entrada `Tareas` se muestra entre los módulos activos del espacio. La vista
incluye:

- contador de tareas pendientes;
- creación y edición inline;
- filtros de estado, fecha y responsable;
- prioridad, vencimiento y responsables en cada fila;
- acciones rápidas para completar, reabrir, editar y eliminar;
- confirmación antes del borrado;
- carga con esqueletos, errores recuperables y estados vacíos;
- adaptación móvil y escritorio, foco visible y etiquetas accesibles.

El espacio personal omite la selección de responsables innecesaria. En espacios
compartidos se muestran todos los miembros como opciones de asignación.

## Verificación realizada

- Valores por defecto y consistencia de finalización.
- Asignaciones múltiples, únicas y restringidas a miembros.
- Limpieza de asignaciones al retirar miembros.
- CRUD completo en espacios personales y compartidos.
- Filtros por estado, responsable y vencimiento.
- Aislamiento frente a usuarios y espacios ajenos.
- Bloqueo del módulo desactivado sin pérdida de datos.
- Suite completa de Django.
- TypeScript, ESLint y build de producción de la PWA.

## Fuera de alcance

- Recurrencias, recordatorios y notificaciones.
- Subtareas, etiquetas y dependencias.
- Comentarios, adjuntos e historial.
- Sincronización offline.
- Permisos individuales por tarea.
- Resumen de tareas en un panel inicial configurable.
