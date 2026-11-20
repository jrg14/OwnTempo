# Espacio personal del usuario

## Estado

Implementado y verificado mediante pruebas automatizadas de backend y las
comprobaciones de calidad de la PWA.

## Finalidad

Cada usuario dispone de un contexto privado al que podrán pertenecer sus gastos,
tareas, eventos y demás datos personales. Solo el propietario puede acceder a
este espacio.

Los espacios compartidos utilizarán posteriormente el mismo modelo. De este modo,
la visibilidad de un recurso se determinará por el espacio al que pertenece y por
sus miembros, sin añadir reglas de privacidad diferentes a cada módulo.

## Modelo de datos

La app `apps.spaces` define:

- `Space`: contexto de organización con nombre, tipo y usuario creador.
- `Membership`: pertenencia de un usuario a un espacio y su rol.

Los tipos de espacio disponibles son `personal` y `shared`. Los roles iniciales
son `owner` y `member`.

La base de datos impide que un usuario cree más de un espacio personal y que una
misma pertenencia se registre dos veces. La validación del modelo exige además que
el único miembro de un espacio personal sea su creador y tenga el rol `owner`.

## Creación automática

Al crear un usuario, una señal crea de forma idempotente:

1. Su espacio con el nombre inicial `Mi espacio`.
2. Su pertenencia como propietario.

La migración de datos crea esta estructura para usuarios anteriores. El comando
siguiente permite reparar usuarios que no tengan espacio personal:

```bash
python manage.py ensure_personal_spaces
```

## API

### Espacios accesibles

```http
GET /api/v1/spaces/
```

Devuelve únicamente los espacios de los que el usuario autenticado es miembro.

### Espacio personal

```http
GET /api/v1/spaces/personal/
PATCH /api/v1/spaces/personal/
```

`GET` devuelve el espacio personal del usuario actual. `PATCH` permite modificar
solo su nombre. La respuesta incluye `id`, `name`, `kind` y `role`.

La API obtiene el usuario desde la sesión; no acepta un identificador de usuario
ni una ruta con la que se pueda seleccionar el espacio personal de otra persona.

## PWA

La pantalla autenticada carga el espacio personal y muestra:

- Su nombre editable.
- Una explicación de que el contexto es privado.
- Estados de carga, guardado correcto y error.
- Una acción para reintentar si la carga inicial falla.

Las llamadas mutables usan la misma protección CSRF que la gestión de cuenta.

## Verificación realizada

- Creación automática e idempotente del espacio personal.
- Restricción de un espacio personal por usuario.
- Rechazo de miembros ajenos en espacios personales.
- Reparación mediante comando de mantenimiento.
- Autenticación, edición y aislamiento de la API.
- Sincronización entre modelos y migraciones.
- TypeScript, ESLint y compilación de producción de la PWA.

## Evolución posterior

Los espacios compartidos, invitaciones y miembros están documentados en
[`shared-spaces-and-memberships.md`](shared-spaces-and-memberships.md).

## Fuera de alcance de esta feature

- Roles avanzados.
- Activación de módulos por espacio.
- Recursos de tareas, compras, deseos, calendario o gastos.
