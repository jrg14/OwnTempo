# Plan de implementación: espacios compartidos y pertenencia

## Estado

Implementado. El comportamiento real está documentado en
[`../features/shared-spaces-and-memberships.md`](../features/shared-spaces-and-memberships.md).
La base del espacio personal se documenta por separado en
[`personal-space.md`](personal-space.md).

## Objetivo

Permitir que una persona cree contextos compartidos como `Casa`, `Familia` o
`Viaje a Lisboa`, invite a otros usuarios de OwnTempo y controle quién puede
acceder a los datos de ese espacio.

El espacio personal seguirá siendo el lugar para la información privada. Los
datos comunes pertenecerán a un espacio compartido y serán visibles para sus
miembros.

```text
Gasto privado de Ana   -> Espacio personal de Ana
Gasto común de la casa -> Espacio compartido Casa
```

## Alcance de esta entrega

- Crear espacios compartidos.
- Consultar y editar los espacios accesibles.
- Invitar a usuarios existentes mediante su nombre de usuario.
- Consultar invitaciones pendientes.
- Aceptar o rechazar invitaciones.
- Consultar los miembros de un espacio.
- El propietario puede retirar miembros.
- Un miembro puede abandonar un espacio compartido.
- Cambiar de espacio desde la PWA.
- Aplicar permisos y aislamiento por espacio en todas las APIs de espacios.

No habrá invitaciones por correo porque OwnTempo no gestiona email de usuario en
esta fase. Las invitaciones estarán disponibles dentro de la PWA para el usuario
destinatario.

## Modelo de dominio

### `Space`

Se reutiliza el modelo existente:

- `name`: nombre visible, obligatorio y limitado a 120 caracteres.
- `kind`: `personal` o `shared`.
- `created_by`: usuario creador.
- `created_at` y `updated_at`.

Un espacio compartido tendrá uno o más miembros. El creador recibirá la primera
pertenencia con rol `owner` dentro de la misma operación de creación.

### `Membership`

Se reutiliza la relación existente:

- `user`.
- `space`.
- `role`: `owner` o `member`.
- `created_at`.

La relación `user + space` seguirá siendo única. La primera versión solo tendrá
dos roles; no se añadirá todavía un rol de administrador intermedio.

### `Invitation`

Nueva entidad para una invitación dirigida a un usuario existente:

- `space`.
- `invited_user`: usuario destinatario.
- `invited_by`: usuario que envía la invitación.
- `status`: `pending`, `accepted`, `rejected` o `cancelled`.
- `created_at`.
- `responded_at`, opcional.

Restricciones y reglas:

- Solo puede existir una invitación `pending` para la misma pareja espacio y
  destinatario.
- El destinatario no puede ser invitado a su propio espacio personal.
- Un miembro actual no puede recibir otra invitación al mismo espacio.
- El invitador debe ser propietario del espacio.
- Aceptar una invitación crea la pertenencia y la marca como `accepted` en una
  única transacción.
- Rechazarla no crea pertenencia y la marca como `rejected`.
- Las invitaciones pendientes podrán cancelarse por el propietario.

## Reglas de negocio y permisos

### Propietario

- Editar el nombre del espacio compartido.
- Invitar usuarios.
- Consultar miembros e invitaciones del espacio.
- Retirar miembros que no sean propietarios.
- Cancelar invitaciones pendientes.

### Miembro

- Consultar el espacio y sus miembros.
- Consultar los datos de los módulos del espacio.
- Abandonar el espacio.
- No puede editar la configuración ni invitar o retirar miembros.

### Invitado

- Solo puede consultar su propia invitación pendiente.
- Puede aceptarla o rechazarla.
- No obtiene acceso al espacio antes de aceptarla.

### Reglas de seguridad

- Ninguna consulta devolverá espacios donde el usuario no tenga `Membership`.
- Las rutas no confiarán en un `user_id` enviado por el cliente para autorizar el
  acceso.
- El usuario no podrá modificar membresías de otro espacio.
- Las operaciones que cambian invitaciones o membresías serán atómicas.
- Los recursos futuros deberán filtrar siempre por `space_id` accesible.
- Un espacio personal no podrá convertirse en compartido ni aceptar miembros.
- Un miembro no podrá eliminar al propietario.

## Propiedad y salida

Para evitar que un espacio quede sin responsable:

- El propietario no podrá abandonarlo mientras sea el único propietario.
- La primera versión no permitirá tener varios propietarios.
- La eliminación del espacio no formará parte de esta entrega.
- La transferencia de propiedad queda fuera de esta entrega. Antes de necesitar
  varios propietarios habrá que diseñar explícitamente esa operación.

## API prevista

Todas las rutas requieren autenticación y protección CSRF en operaciones mutables.

### Espacios

```http
GET /api/v1/spaces/
POST /api/v1/spaces/
GET /api/v1/spaces/{space_id}/
PATCH /api/v1/spaces/{space_id}/
```

`POST /spaces/` acepta:

```json
{
  "name": "Casa"
}
```

El backend fuerza `kind=shared` y crea la pertenencia del propietario. El
cliente no podrá crear espacios personales mediante esta ruta.

### Miembros

```http
GET /api/v1/spaces/{space_id}/members/
DELETE /api/v1/spaces/{space_id}/members/{user_id}/
POST /api/v1/spaces/{space_id}/leave/
```

El listado devuelve solo información necesaria para la colaboración: `id`,
`username`, nombre visible y `role`.

### Invitaciones enviadas

```http
GET /api/v1/spaces/{space_id}/invitations/
POST /api/v1/spaces/{space_id}/invitations/
DELETE /api/v1/spaces/{space_id}/invitations/{invitation_id}/
```

El `POST` recibe el nombre de usuario del destinatario. Solo el propietario
puede usar estas rutas.

### Invitaciones recibidas

```http
GET /api/v1/invitations/
POST /api/v1/invitations/{invitation_id}/accept/
POST /api/v1/invitations/{invitation_id}/reject/
```

El usuario solo podrá operar sobre invitaciones cuyo destinatario sea él mismo.

## PWA

La experiencia se incorporará progresivamente:

1. Añadir un selector de espacios con el espacio personal y los compartidos.
2. Añadir una pantalla o diálogo para crear un espacio compartido.
3. Mostrar invitaciones pendientes al usuario destinatario.
4. Permitir aceptar o rechazar invitaciones.
5. Mostrar la lista de miembros y sus roles.
6. Permitir al propietario invitar y retirar miembros.
7. Permitir a un miembro abandonar un espacio con confirmación.
8. Mantener visible el espacio activo para que los módulos futuros sepan dónde
   leer y guardar sus datos.

La navegación no debe mostrar acciones de propietario a los miembros. Los
errores de permisos, duplicados e invitaciones inválidas se mostrarán con
mensajes comprensibles.

## Fases de implementación

1. Añadir `Invitation`, estados, restricciones y migración.
2. Crear servicios transaccionales para crear espacios, invitar, aceptar,
   rechazar, cancelar y abandonar.
3. Crear permisos reutilizables para miembro y propietario.
4. Implementar endpoints de espacios compartidos y detalle.
5. Implementar miembros e invitaciones enviadas y recibidas.
6. Añadir pruebas de aislamiento, transacciones y permisos.
7. Integrar selector de espacios en la PWA.
8. Integrar creación, invitaciones y gestión de miembros.
9. Documentar el comportamiento implementado y actualizar el roadmap.

## Pruebas mínimas

### Modelo y servicios

- Crear un espacio compartido crea al propietario como miembro `owner`.
- Un usuario puede pertenecer a varios espacios.
- Un usuario no puede crear una segunda invitación pendiente igual.
- No se puede invitar a un miembro existente.
- No se puede invitar al propietario del espacio.
- Aceptar una invitación crea una única pertenencia.
- Reintentar aceptar una invitación no duplica la pertenencia.
- Rechazar o cancelar una invitación impide aceptarla después.
- Abandonar elimina solo la pertenencia del usuario actual.
- Un propietario no puede dejar el espacio si no existe otro propietario.

### API y autorización

- Un usuario anónimo no puede consultar espacios ni invitaciones.
- Un usuario solo ve sus propios espacios.
- Un miembro no puede invitar, retirar miembros ni editar el espacio.
- Un propietario no puede operar sobre otro espacio.
- Un invitado no ve el contenido antes de aceptar.
- Un usuario ajeno no puede aceptar una invitación.
- Los miembros retirados dejan de acceder inmediatamente.
- El espacio personal no aparece como destino de invitaciones.

### PWA

- El selector muestra solo espacios accesibles.
- Crear un espacio actualiza la lista sin recargar la aplicación.
- Las invitaciones pendientes se pueden aceptar o rechazar.
- Las acciones de propietario no aparecen a miembros.
- Cambiar de espacio actualiza el contexto activo.
- Los estados de carga, error y éxito son comprensibles y accesibles.

## Criterios de aceptación

La feature se considerará completada cuando:

1. Ana pueda crear un espacio `Casa`.
2. Ana pueda invitar a Luis usando su username.
3. Luis vea la invitación sin ver todavía los datos de `Casa`.
4. Luis pueda aceptar la invitación y pase a ser miembro.
5. Ana y Luis puedan consultar el espacio y sus miembros.
6. Ana pueda retirar a Luis y Luis pierda el acceso.
7. Luis pueda abandonar un espacio sin afectar su espacio personal.
8. Un tercero no pueda descubrir ni consultar el espacio.
9. Los datos futuros puedan asociarse a `Casa` y aplicar este aislamiento sin
   lógica especial por usuario.

## Fuera de alcance

- Invitaciones por email o enlaces públicos.
- Registro público de usuarios.
- Varios propietarios y transferencia de propiedad.
- Eliminación de espacios.
- Rol de administrador.
- Permisos distintos por módulo.
- Privacidad de elementos individuales dentro de un espacio compartido.
- Notificaciones push o recordatorios de invitaciones.
- Activación y desactivación de módulos por espacio.
- Datos de tareas, compras, deseos, calendario o gastos.
