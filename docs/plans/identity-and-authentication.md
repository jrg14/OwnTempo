# Plan de implementación: usuarios y autenticación doméstica

## Estado

Implementada. El comportamiento real está documentado en
[`../features/users-authentication.md`](../features/users-authentication.md).

## Objetivo

Permitir que los usuarios creados por el administrador accedan a OwnTempo desde
la PWA, cierren su sesión y consulten o actualicen los datos básicos de su propia
cuenta.

El alcance está adaptado a un uso doméstico en un servidor privado. No se busca
crear por ahora un sistema público de registro ni un flujo completo de gestión de
contraseñas desde la aplicación.

## Decisiones de producto

### Alta de usuarios

- No habrá registro público desde la PWA.
- El administrador creará los usuarios desde Django Admin.
- El administrador asignará inicialmente el nombre de usuario, nombre, apellidos
  opcionales y contraseña.
- El administrador podrá activar o desactivar una cuenta mediante `is_active`.
- Una cuenta desactivada no podrá iniciar sesión.
- El administrador será responsable de crear nuevas cuentas y resolver problemas
  de acceso.

### Contraseñas

- No se implementará cambio de contraseña desde la PWA en esta fase.
- No se implementará recuperación de contraseña por correo.
- El administrador podrá establecer o restablecer la contraseña desde Django
  Admin.
- Django seguirá almacenando las contraseñas mediante sus mecanismos seguros y
  validadores configurados.

Esta decisión reduce la complejidad y evita depender inicialmente de un proveedor
de correo electrónico. Podrá revisarse si OwnTempo deja de ser exclusivamente
doméstico.

### Sesiones

- La PWA y la API se servirán bajo el mismo origen en el despliegue normal.
- La autenticación utilizará sesiones de Django mediante cookies.
- La cookie de sesión deberá ser `HttpOnly` y `Secure` cuando se use HTTPS.
- Las operaciones mutables estarán protegidas mediante CSRF.
- No se guardarán contraseñas, sesiones ni tokens en `localStorage`.
- Los tokens de acceso y renovación quedan fuera del alcance actual y solo se
  valorarían para un futuro cliente nativo o una integración externa.

## Modelo de usuario

Se creará una app Django `accounts` con un modelo `User` propio basado en
`AbstractUser`. Debe configurarse `AUTH_USER_MODEL` antes de añadir modelos de
negocio que referencien usuarios.

El modelo conservará inicialmente los campos estándar de Django:

- `username`: identificador de acceso, asignado inicialmente por el administrador
  y editable posteriormente por el propio usuario.
- `first_name`: nombre visible.
- `last_name`: apellidos visibles.
- `is_active`: permite bloquear el acceso sin borrar la cuenta.
- `is_staff` e `is_superuser`: reservados para la administración y nunca editables
  desde la API de cuenta propia.

No se creará todavía un modelo `Profile` ni se añadirá una relación con `Space`.

## API prevista

Las rutas son una propuesta para la implementación y pueden ajustarse al estilo
final de la API.

### Inicio de sesión

```http
POST /api/v1/auth/login/
Content-Type: application/json
X-CSRFToken: <token>

{
  "username": "ana",
  "password": "..."
}
```

Comportamiento esperado:

- Credenciales correctas: HTTP `200` y creación de la sesión de Django.
- Usuario inexistente, contraseña incorrecta o cuenta inactiva: respuesta de
  error descriptiva con HTTP `400` o `401`.
- No se devolverá la contraseña ni información de permisos administrativos.

### Cuenta actual

```http
GET /api/v1/account/me/
PATCH /api/v1/account/me/
```

`GET` devolverá únicamente la cuenta autenticada. `PATCH` permitirá modificar
solo los datos personales editables:

- `username`, sujeto a las reglas de unicidad de Django.
- `first_name`.
- `last_name`.

La contraseña, `is_active`, `is_staff`, `is_superuser`, los grupos y los permisos
no podrán modificarse desde esta API.

### Cierre de sesión

```http
POST /api/v1/auth/logout/
```

La ruta invalidará la sesión actual y devolverá una respuesta idempotente. Debe
estar protegida frente a CSRF porque modifica el estado de la sesión.

### CSRF

La PWA necesitará una forma de obtener el token CSRF antes del primer `POST`, por
ejemplo una ruta pública `GET /api/v1/auth/csrf/` que establezca la cookie sin
crear una sesión autenticada. La solución definitiva se elegirá al implementar la
integración frontend.

## Comportamiento de la PWA

- Mostrar un formulario de login con nombre de usuario y contraseña.
- Mostrar errores descriptivos de autenticación y conexión.
- Mantener la sesión mientras la cookie siga siendo válida.
- Consultar la cuenta actual al entrar en una zona autenticada.
- Permitir editar username, nombre y apellidos.
- Ofrecer cierre de sesión.
- No mostrar enlaces de registro, cambio de contraseña ni recuperación por correo.
- Informar al usuario de que las altas y gestiones de contraseña las realiza el
  administrador.

La pantalla de login y la pantalla de cuenta serán features de la PWA cuando se
implementen; no forman parte de la pantalla inicial actualmente documentada.

## Permisos y seguridad

- El endpoint de healthcheck seguirá siendo público.
- Todas las demás APIs privadas requerirán autenticación por defecto.
- Un usuario solo podrá consultar y modificar su propia cuenta.
- Nunca se aceptará un identificador de usuario arbitrario para decidir la cuenta
  editable.
- Los campos administrativos se excluirán explícitamente de serializers y vistas.
- Los errores de login serán descriptivos para el usuario, pero nunca incluirán
  trazas, consultas ni detalles internos del servidor.
- En producción se exigirá HTTPS para proteger la cookie de sesión.

## Fases de implementación

1. Crear `apps.accounts` y el modelo `User` basado en `AbstractUser`.
2. Configurar `AUTH_USER_MODEL`, migraciones y registro en Django Admin.
3. Añadir la obtención del token CSRF.
4. Implementar login mediante sesión.
5. Implementar `GET/PATCH /api/v1/account/me/`.
6. Implementar logout.
7. Añadir la pantalla de login de la PWA.
8. Añadir la pantalla de cuenta actual.
9. Aplicar autenticación por defecto al resto de APIs privadas.
10. Documentar el procedimiento doméstico para crear y desactivar usuarios desde
    Django Admin.

## Pruebas automatizadas pospuestas

Por decisión de alcance, esta implementación no incorpora ni ejecuta tests
automatizados. Si se decide añadirlos posteriormente, deberán cubrir al menos los
casos siguientes.

### Backend

- El modelo de usuario se crea correctamente mediante migraciones.
- El administrador puede crear, editar, activar y desactivar usuarios.
- Login correcto crea una sesión.
- Login con credenciales incorrectas es rechazado.
- Login de una cuenta inactiva es rechazado.
- Usuario anónimo no puede consultar `account/me`.
- Un usuario autenticado obtiene únicamente sus propios datos.
- `PATCH` permite cambiar username, nombre y apellidos.
- `PATCH` rechaza o ignora campos administrativos y contraseña.
- Logout invalida la sesión.
- Las operaciones mutables sin CSRF son rechazadas.
- No se filtran contraseñas ni permisos administrativos en las respuestas.

### PWA

- El formulario envía las credenciales al endpoint correcto.
- La PWA muestra un error descriptivo ante un login fallido.
- Una sesión válida permite cargar la cuenta actual.
- Los cambios editables se guardan y se reflejan al volver a consultar.
- El cierre de sesión devuelve al usuario a la pantalla de login.
- No aparecen opciones de registro o recuperación de contraseña.

## Criterio de finalización

El administrador puede crear y gestionar usuarios desde Django Admin, y cada
usuario creado puede iniciar sesión en la PWA, consultar y actualizar sus datos
personales permitidos y cerrar sesión. No existe registro público ni gestión de
contraseñas desde la aplicación.

## Fuera de alcance

- Creación pública de cuentas.
- Verificación de correo electrónico.
- Cambio de contraseña desde la PWA.
- Recuperación de contraseña por correo.
- Segundo factor de autenticación.
- Tokens JWT o refresh tokens.
- Espacio personal automático.
- Espacios compartidos, invitaciones, membresías y roles de negocio.
