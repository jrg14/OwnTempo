# Calendario personal y compartido

## Estado

Implementado y verificado. Es el cuarto módulo de negocio disponible en la
plataforma modular de OwnTempo.

## Comportamiento

Cada evento pertenece a un único espacio personal o compartido. Todos los
miembros activos del espacio pueden consultarlo, crearlo, editarlo y eliminarlo.

Hay dos modalidades excluyentes:

- Los eventos horarios guardan `start_at` y `end_at` con zona horaria, y exigen
  que el final sea posterior al inicio.
- Los eventos de día completo guardan una fecha local en `date` y no contienen
  horas artificiales.

Los eventos pueden incluir título, descripción, ubicación o enlace y una clave
de color semántica. El creador y las fechas de auditoría son de solo lectura.

## Fechas y consultas

Django almacena los eventos horarios de forma consciente de zona y la PWA los
presenta en la zona del navegador. Los eventos de día completo conservan la
fecha local sin conversiones a UTC.

El listado exige los parámetros `from` y `to` como fechas ISO. Devuelve eventos
que se solapan con el rango, aunque hayan comenzado antes, y limita cada consulta
a un máximo de 93 días inclusivos.

## Modelo de datos

La app `apps.calendar` define `CalendarEvent`, vinculado directamente con
`Space` y su creador. La base de datos comprueba que cada fila represente un
evento horario válido o un evento de día completo válido, sin mezclar ambos
modos.

Se mantienen índices por espacio y fecha, inicio y final para las consultas de
rango.

## API

```http
GET    /api/v1/spaces/{space_id}/calendar/events/?from=AAAA-MM-DD&to=AAAA-MM-DD
POST   /api/v1/spaces/{space_id}/calendar/events/
GET    /api/v1/spaces/{space_id}/calendar/events/{event_id}/
PATCH  /api/v1/spaces/{space_id}/calendar/events/{event_id}/
DELETE /api/v1/spaces/{space_id}/calendar/events/{event_id}/
```

Todas las rutas requieren sesión, pertenencia activa y el módulo `calendar`
activo. Los querysets parten siempre del espacio de la URL, por lo que un
identificador externo no permite descubrir datos de otro espacio.

## PWA

La ruta `/spaces/{space_id}/calendar/` ofrece:

- navegación mensual y acción para volver a hoy;
- cuadrícula de seis semanas con número de eventos por día;
- agenda del día seleccionado;
- creación y edición de eventos horarios y de día completo;
- colores semánticos y ubicación como texto o enlace seguro;
- acciones accesibles para editar y eliminar;
- estados de carga, error, día vacío y módulo no disponible;
- diseño adaptable a móvil y escritorio.

La PWA vuelve a comprobar la activación del módulo al recuperar el foco. Si se
desactiva, regresa al inicio sin eliminar los eventos existentes.

## Verificación realizada

- Validación de título, modo, intervalos y zona horaria.
- Cambio seguro entre evento horario y día completo.
- Consultas de solapamiento y límites de rango.
- CRUD completo por miembros activos.
- Aislamiento entre espacios y bloqueo por módulo desactivado.
- Migración sincronizada con los modelos.
- Suite completa de Django.
- TypeScript, ESLint y build de producción de la PWA.

## Fuera de alcance

- Recurrencias y sus excepciones.
- Invitaciones, asistentes y eventos privados.
- Recordatorios, notificaciones y alarmas.
- Integraciones iCal, Google Calendar u otros servicios.
- Reservas de recursos y sincronización offline de datos.
