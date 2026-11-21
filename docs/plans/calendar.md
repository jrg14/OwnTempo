# Plan de implementación: calendario personal y compartido

## Estado

Implementado. El comportamiento real está documentado en
[`../features/calendar.md`](../features/calendar.md). Este documento conserva las
decisiones y el orden seguido para la primera versión del módulo `calendar` sobre
la plataforma modular por espacio.

## Objetivo

Permitir que una persona consulte y gestione sus eventos en el espacio personal
y que los miembros de un espacio compartido mantengan una agenda común. La
primera versión priorizará una vista fiable por fecha y una edición sencilla,
sin introducir todavía un sistema completo de invitaciones o recurrencias.

## Alcance de esta entrega

- Crear, consultar, editar y eliminar eventos.
- Definir título obligatorio y descripción opcional.
- Definir inicio y fin con fecha y hora.
- Crear eventos de día completo.
- Añadir ubicación o enlace opcional.
- Elegir un color semántico opcional para la presentación.
- Filtrar y consultar eventos por un rango de fechas.
- Mostrar vistas de agenda, mes y próximos eventos en la PWA.
- Utilizar el mismo módulo en espacios personales y compartidos.
- Conservar eventos cuando el módulo se desactive.

## Decisiones de producto

- Un evento pertenece a un único espacio y nunca se comparte entre espacios.
- Todos los miembros activos pueden consultar, crear, editar y eliminar eventos
  del espacio.
- Un evento nuevo es visible para todos los miembros del espacio desde el
  momento de su creación.
- Un evento con `all_day=true` representa un día completo y no requiere horas.
- Un evento con hora debe tener `end_at` posterior a `start_at`.
- La hora se almacenará en UTC en el backend y la API utilizará fechas ISO 8601
  con zona horaria explícita.
- La PWA mostrará las horas en la zona horaria del usuario; inicialmente se
  usará la zona del navegador y se conservará `Europe/Madrid` como fallback del
  proyecto.
- Los eventos se ordenarán por inicio ascendente y, a igualdad de inicio, por
  duración y fecha de creación.
- Los eventos de día completo aparecerán antes que los eventos horarios del
  mismo día.
- No se enviarán notificaciones ni recordatorios en esta versión.

## Modelo de dominio

Se añadirá una app Django independiente llamada `apps.calendar`.

### `CalendarEvent`

- `space`: espacio propietario del evento.
- `title`: título obligatorio, máximo 200 caracteres.
- `description`: descripción opcional, máximo 4.000 caracteres.
- `start_at`: inicio del evento como fecha y hora consciente de zona.
- `end_at`: fin del evento como fecha y hora consciente de zona, nulo para día
  completo.
- `all_day`: indica si ocupa el día completo.
- `date`: fecha local del evento para eventos de día completo y consultas rápidas.
- `location`: ubicación o enlace opcional, máximo 300 caracteres.
- `color`: clave semántica opcional, limitada al catálogo de colores de la PWA.
- `created_by`: usuario miembro que lo creó.
- `created_at` y `updated_at`.

Restricciones:

- El creador debe pertenecer al espacio.
- `title` no puede quedar vacío después de recortarlo.
- Un evento de día completo debe tener `date`, no necesita `start_at` ni
  `end_at` y no aceptará horas parciales.
- Un evento horario debe tener `start_at` y `end_at`, ambos en la misma
  interpretación temporal, y el final debe ser posterior al inicio.
- No se guardarán fechas ingenuas sin zona horaria.
- `color` solo aceptará claves presentes en el catálogo estable.

La representación de eventos de día completo se cerrará antes de codificar la
migración. La opción preferida es conservar una fecha local explícita y permitir
que los campos horarios sean nulos, evitando conversiones artificiales a
medianoche UTC.

## Catálogo y disponibilidad

La plataforma modular ya contiene la entrada estable `calendar`. Al completar
la implementación se añadirá `app_label="calendar"` y se marcará
`available=true` en el catálogo.

Los endpoints exigirán pertenencia al espacio y módulo activo y disponible. Al
desactivarlo se bloqueará el acceso, pero los eventos seguirán almacenados.

## API

Todas las rutas requerirán sesión autenticada, pertenencia activa al espacio y
el módulo `calendar` activo.

### Eventos

```http
GET    /api/v1/spaces/{space_id}/calendar/events/
POST   /api/v1/spaces/{space_id}/calendar/events/
GET    /api/v1/spaces/{space_id}/calendar/events/{event_id}/
PATCH  /api/v1/spaces/{space_id}/calendar/events/{event_id}/
DELETE /api/v1/spaces/{space_id}/calendar/events/{event_id}/
```

El listado requerirá un rango explícito para evitar descargar una agenda
ilimitada:

```text
GET /api/v1/spaces/{space_id}/calendar/events/?from=2026-11-01&to=2026-11-30
```

El rango será inclusivo y devolverá eventos que se solapen con él, incluidos los
eventos de día completo. Se validará que `from` no sea posterior a `to` y que el
rango máximo no supere 93 días en una sola consulta.

La respuesta estará ordenada y devolverá las fechas en ISO 8601. Para crear un
evento horario:

```json
{
  "title": "Revisión del proyecto",
  "description": "Preparar las decisiones pendientes.",
  "start_at": "2026-11-24T17:00:00+01:00",
  "end_at": "2026-11-24T18:00:00+01:00",
  "all_day": false,
  "location": "https://meet.example.com/reunion",
  "color": "teal"
}
```

Para un evento de día completo:

```json
{
  "title": "Día festivo",
  "date": "2026-12-06",
  "all_day": true,
  "color": "amber"
}
```

El cliente no podrá modificar `created_by`, `created_at`, `updated_at` ni un
campo calculado de zona horaria.

## Servicios y transacciones

La creación y actualización se implementarán mediante servicios de dominio:

- `create_event(user, space, validated_data)`.
- `update_event(event, validated_data)`.
- `delete_event(event)`.
- `events_for_range(space, start, end)`.

Los servicios normalizarán fechas, comprobarán el modo de día completo y
mantendrán las validaciones de intervalos en una única capa. La consulta por
rango incluirá eventos que comiencen antes del final solicitado pero terminen
después del inicio, además de los eventos de día completo que caigan dentro del
rango.

No se calcularán recurrencias en tiempo real ni se crearán copias derivadas de
un evento.

## Permisos y aislamiento

- Un usuario anónimo no puede acceder a las rutas.
- Un usuario que no sea miembro activo no puede descubrir eventos.
- Todos los miembros activos pueden operar sobre eventos del espacio.
- El módulo desactivado bloquea lectura y escritura.
- Un identificador de otro espacio debe responder como no encontrado dentro del
  queryset autorizado.
- Eliminar al creador no debe eliminar eventos; se conservará la política de
  protección de datos del proyecto.

No habrá asistentes individuales, eventos privados ni permisos por evento en
esta primera versión: el espacio es la unidad de privacidad.

## PWA

### Navegación

El módulo se abrirá desde el espacio activo mediante la ruta estable
`/spaces/{space_id}/calendar/`.

La pantalla tendrá:

1. Selector de fecha y navegación al día actual.
2. Vista mensual para localizar días con eventos.
3. Agenda diaria o semanal con eventos ordenados.
4. Vista de próximos eventos como alternativa compacta.
5. Acción visible para crear un evento.

### Formulario y tarjeta

El formulario permitirá cambiar entre evento horario y día completo. Mostrará
errores si falta el final, el intervalo no es válido o una fecha no puede
interpretarse. Las tarjetas mostrarán título, horas o etiqueta de día completo,
ubicación, color y descripción.

Estados de interfaz obligatorios:

- carga inicial y cambio de rango;
- error de carga y reintento;
- rango sin eventos;
- formulario con error de validación;
- guardado correcto;
- módulo desactivado o no disponible.

La interfaz deberá mantener accesibles las acciones de editar y eliminar en
móvil y teclado. Los eventos con enlace de ubicación abrirán una pestaña nueva
con relación segura.

## Orden de implementación

1. Resolver la representación definitiva de eventos de día completo y zona
   horaria antes de crear la migración.
2. Crear `apps.calendar`, modelo, migración y administración Django.
3. Añadir servicios de dominio para validación, CRUD y consultas por rango.
4. Añadir serializers, filtros, vistas, URLs y permisos del módulo.
5. Implementar pruebas de fechas, solapamientos, zona horaria y aislamiento.
6. Activar `calendar` como módulo disponible tras superar las pruebas backend.
7. Crear tipos y cliente de API en la PWA.
8. Implementar agenda, calendario mensual y formulario de eventos.
9. Implementar navegación de rangos, estados vacíos y errores.
10. Actualizar documentación de feature, roadmap y verificación final.

## Pruebas mínimas

### Modelo y servicios

- El título se recorta y no admite valores vacíos.
- Un evento horario exige inicio y fin.
- El final debe ser posterior al inicio.
- Un evento de día completo exige fecha y rechaza horas.
- Las fechas ingenuas se rechazan o se normalizan explícitamente antes de guardar.
- Los eventos se almacenan y devuelven con zona horaria coherente.
- Un rango incluye eventos que se solapan con sus límites.
- Un rango superior a 93 días se rechaza.
- El creador debe pertenecer al espacio.
- Los colores desconocidos se rechazan.

### API y autorización

- Un miembro puede crear, listar, editar y eliminar eventos.
- Los filtros de rango devuelven solo eventos del espacio solicitado.
- Los eventos de día completo aparecen en el día correcto.
- Un usuario ajeno no puede descubrir eventos.
- No se puede leer o modificar un evento de otro espacio manipulando el ID.
- El módulo desactivado bloquea todos sus endpoints sin borrar datos.
- Los campos de auditoría no pueden ser modificados desde el cliente.

### PWA

- Se puede cambiar de mes, día y rango sin mezclar eventos.
- Se diferencian visualmente eventos de día completo y eventos horarios.
- Se puede crear y editar ambos tipos de evento.
- Se muestran correctamente los solapamientos en la agenda.
- Las ubicaciones o enlaces son accesibles y seguros.
- Se muestran carga, rango vacío, error y módulo no disponible.

## Criterios de aceptación

El módulo se considerará completado cuando:

1. Un miembro pueda gestionar eventos personales o compartidos.
2. Los eventos horarios y de día completo se comporten correctamente.
3. Las consultas por rango incluyan solapamientos sin descargar una agenda
   ilimitada.
4. Las fechas se almacenen y presenten con zona horaria coherente.
5. La API esté aislada por espacio y módulo activo.
6. La PWA ofrezca agenda, calendario mensual, creación y edición.
7. La suite backend, el typecheck, el lint y el build frontend pasen.
8. El comportamiento real quede documentado en `docs/features/` y el roadmap
   refleje la feature como completada.

## Fuera de alcance

- Recurrencias y excepciones de recurrencia.
- Invitaciones, asistentes y aceptación de eventos.
- Recordatorios, notificaciones y alarmas.
- Sincronización con Google Calendar, iCal o servicios externos.
- Reservas de recursos o disponibilidad de salas.
- Calendarios privados dentro de un espacio compartido.
- Integración automática con tareas, gastos o listas de la compra.
- Funcionamiento offline completo y resolución de conflictos.
