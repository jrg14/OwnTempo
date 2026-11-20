# Plan de implementación: espacios y pertenencia

## Estado

Primera entrega implementada. El comportamiento real está documentado en
[`../features/personal-space.md`](../features/personal-space.md). Los espacios
compartidos y las invitaciones se implementarán sobre la misma base.

## Objetivo

Proporcionar el contexto de privacidad y colaboración de OwnTempo. Cada dato de
negocio pertenecerá a un espacio y solo será visible para los miembros de ese
espacio.

Este modelo permite que una persona mantenga información privada y, al mismo
tiempo, comparta otros datos con una pareja, familia, compañeros de piso u otro
grupo.

## Decisión principal de producto

Los espacios representan contextos independientes de organización:

- El espacio personal de Ana contiene sus gastos, tareas y eventos privados.
- Un espacio compartido como `Casa` contiene gastos, tareas y listas comunes.
- Un espacio compartido como `Viaje a Lisboa` puede agrupar información de un
  contexto temporal.

La visibilidad se determina por la pertenencia al espacio, no por permisos
individuales en cada elemento.

Por tanto:

```text
Gasto personal de Ana   -> Espacio personal de Ana
Gasto común de la casa  -> Espacio Casa
Gasto de un viaje       -> Espacio Viaje
```

Inicialmente no habrá elementos privados dentro de un espacio compartido. Si un
dato debe ser privado, pertenecerá al espacio personal del usuario.

## Modelo de dominio

Se creará una app Django independiente llamada `apps.spaces`.

### `Space`

- `id`: identificador del espacio.
- `name`: nombre visible del espacio.
- `kind`: `personal` o `shared`.
- `created_at` y `updated_at`.
- `created_by`: usuario que creó el espacio.

El modelo tendrá una restricción para permitir como máximo un espacio personal
por usuario creador.

### `Membership`

- `user`.
- `space`.
- `role`: inicialmente `owner` o `member`.
- `created_at`.

La relación entre usuario y espacio será única. Aunque en la primera entrega el
espacio personal solo tendrá un miembro, se utilizará `Membership` desde el
principio para que los módulos futuros puedan consultar la pertenencia de forma
uniforme.

## Reglas de negocio

- Cada usuario debe tener exactamente un espacio personal.
- Un espacio personal solo puede tener un miembro.
- El usuario propietario no puede perder el acceso a su espacio personal.
- Un espacio personal no admite invitaciones ni miembros adicionales.
- Solo los miembros pueden consultar un espacio.
- Solo el propietario puede editar el nombre del espacio personal.
- Los recursos futuros deberán guardar una referencia a `Space`; nunca se
  autorizarán únicamente por un `user_id` independiente.
- Las consultas de negocio deberán filtrar por los espacios accesibles al usuario
  autenticado.

## Creación del espacio personal

El espacio personal se creará automáticamente al crear un usuario, también si el
usuario se crea desde Django Admin.

La operación será idempotente para evitar duplicados en reintentos o procesos de
mantenimiento.

Se añadirá además un comando de mantenimiento que permita detectar y crear
espacios personales faltantes para usuarios existentes.

## API prevista

Todas las rutas requerirán una sesión autenticada.

### Listar espacios accesibles

```http
GET /api/v1/spaces/
```

Devuelve los espacios de los que el usuario es miembro, incluyendo su rol.

### Obtener el espacio personal

```http
GET /api/v1/spaces/personal/
```

Devuelve el espacio personal del usuario actual.

### Editar el espacio personal

```http
PATCH /api/v1/spaces/personal/
```

En la primera entrega solo permitirá cambiar `name`.

Ejemplo de respuesta:

```json
{
  "id": 1,
  "name": "Mi espacio",
  "kind": "personal",
  "role": "owner"
}
```

No se aceptará un identificador de usuario para resolver el espacio. La API
siempre usará `request.user` y la pertenencia registrada.

## PWA

Después de validar la sesión, la PWA consultará el espacio personal y mostrará:

- El nombre del espacio.
- Un formulario para cambiarlo.
- Estados de carga, guardado correcto y error.

La interfaz no incluirá todavía creación de espacios compartidos, invitaciones ni
selector de espacios. Se dejará preparado un componente de navegación para que
esas funciones puedan añadirse posteriormente sin rehacer la pantalla principal.

## Fases de implementación

1. Crear `apps.spaces`, modelos, migración y restricciones de base de datos.
2. Crear automáticamente el espacio personal al crear un usuario.
3. Añadir el comando de mantenimiento para usuarios sin espacio.
4. Implementar permisos y consultas filtradas por pertenencia.
5. Implementar `GET /spaces/` y `GET/PATCH /spaces/personal/`.
6. Añadir pruebas de modelo, API, aislamiento y permisos.
7. Integrar el espacio personal en la PWA.
8. Actualizar la documentación de la feature implementada y el roadmap.

## Pruebas mínimas

### Backend

- Un usuario nuevo recibe un único espacio personal.
- Repetir la creación no genera espacios duplicados.
- Dos usuarios tienen espacios personales distintos.
- Un usuario no puede consultar el espacio personal de otro.
- Un usuario no puede editar el espacio personal de otro.
- Un espacio personal no admite un segundo miembro.
- La lista de espacios no filtra datos de usuarios ajenos.
- Las rutas requieren autenticación.

### Frontend

- El espacio personal aparece tras iniciar sesión.
- El nombre se puede editar y conservar tras recargar.
- Se muestran correctamente los estados de carga, éxito y error.
- El flujo de cierre de sesión sigue funcionando.

## Criterios de aceptación

La feature se considerará completada cuando:

1. Cada usuario disponga automáticamente de un espacio personal.
2. Los recursos futuros puedan referenciar un espacio sin crear una excepción
   para datos personales.
3. Un usuario pueda consultar y renombrar su espacio desde la PWA.
4. Sea imposible acceder al espacio personal de otro usuario mediante la API.
5. La base permita añadir espacios compartidos, invitaciones y roles sin cambiar
   el modelo de pertenencia.

## Fuera de alcance

- Creación y edición de espacios compartidos.
- Invitaciones por usuario, enlace o correo.
- Aceptación y rechazo de invitaciones.
- Transferencia de propiedad.
- Eliminación de espacios.
- Roles avanzados y permisos por módulo.
- Privacidad por elemento dentro de un espacio compartido.
- Activación y desactivación de módulos.
