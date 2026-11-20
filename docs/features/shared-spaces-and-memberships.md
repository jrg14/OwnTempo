# Espacios compartidos, invitaciones y miembros

## Estado

Implementado y verificado mediante pruebas automatizadas de backend y las
comprobaciones de calidad de la PWA.

## Finalidad

Los usuarios pueden crear espacios compartidos para separar los datos comunes de
los datos privados. Un usuario solo puede consultar un espacio cuando dispone de
una pertenencia activa.

Las invitaciones se dirigen a usuarios existentes mediante su `username`. No se
utiliza email ni se permite registro público.

## Modelo de datos

Se reutilizan `Space` y `Membership` y se añade `Invitation`:

- Un espacio compartido tiene `kind=shared`.
- Su creador recibe una pertenencia con rol `owner`.
- Los usuarios invitados reciben el rol `member` al aceptar.
- Una invitación puede estar `pending`, `accepted`, `rejected` o `cancelled`.
- Solo puede existir una invitación pendiente por espacio y destinatario.

La aceptación crea la pertenencia y actualiza la invitación dentro de una única
transacción.

## Roles

### Propietario

- Renombrar el espacio.
- Invitar usuarios.
- Consultar y cancelar invitaciones.
- Consultar miembros.
- Retirar miembros.

El propietario no puede abandonar el espacio porque todavía no existe
transferencia de propiedad.

### Miembro

- Consultar el espacio y sus miembros.
- Cambiar al espacio desde la PWA.
- Abandonar el espacio.

No puede renombrar el espacio, invitar usuarios ni retirar miembros.

## API

### Espacios

```http
GET  /api/v1/spaces/
POST /api/v1/spaces/
GET  /api/v1/spaces/{space_id}/
PATCH /api/v1/spaces/{space_id}/
```

La creación fuerza el tipo `shared`; el cliente no puede crear espacios
personales mediante esta ruta.

### Miembros

```http
GET    /api/v1/spaces/{space_id}/members/
DELETE /api/v1/spaces/{space_id}/members/{user_id}/
POST   /api/v1/spaces/{space_id}/leave/
```

### Invitaciones enviadas

```http
GET    /api/v1/spaces/{space_id}/invitations/
POST   /api/v1/spaces/{space_id}/invitations/
DELETE /api/v1/spaces/{space_id}/invitations/{invitation_id}/
```

### Invitaciones recibidas

```http
GET  /api/v1/invitations/
POST /api/v1/invitations/{invitation_id}/accept/
POST /api/v1/invitations/{invitation_id}/reject/
```

Las operaciones mutables requieren sesión y protección CSRF.

## PWA

La pantalla autenticada incorpora:

- Selector entre el espacio personal y los espacios compartidos.
- Creación de espacios compartidos.
- Bandeja de invitaciones recibidas con aceptación y rechazo.
- Edición del nombre para propietarios.
- Listado de miembros y roles.
- Invitación por nombre de usuario.
- Cancelación de invitaciones pendientes.
- Retirada de miembros con confirmación.
- Salida voluntaria de miembros con confirmación.

Las acciones administrativas solo se muestran al propietario.

## Seguridad y aislamiento

- Los listados filtran por las pertenencias del usuario autenticado.
- Los invitados no acceden al espacio antes de aceptar.
- Un usuario no puede responder invitaciones dirigidas a otra persona.
- Los miembros no pueden realizar acciones de propietario.
- Un usuario retirado o que abandona pierde el acceso inmediatamente.
- El espacio personal no admite invitaciones.

## Verificación realizada

- Creación del espacio y pertenencia del propietario.
- Ciclos de aceptación, rechazo y cancelación de invitaciones.
- Prevención de invitaciones pendientes duplicadas.
- Permisos de propietario, miembro, invitado y usuario ajeno.
- Retirada y salida de miembros.
- Pérdida inmediata de acceso tras retirar la pertenencia.
- Suite completa de Django.
- Sincronización entre modelos y migraciones.
- TypeScript, ESLint y compilación de producción de la PWA.

## Fuera de alcance

- Eliminación de espacios.
- Transferencia de propiedad o varios propietarios.
- Rol de administrador.
- Invitaciones por email o enlace público.
- Notificaciones push.
- Permisos por módulo.
- Tareas, compras, calendario y gastos.
