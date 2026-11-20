# Usuarios y autenticación doméstica

## Estado

Implementada sin tests automatizados, por decisión de alcance.

## Finalidad

Permite que usuarios creados por el administrador accedan a OwnTempo mediante una
sesión de Django, consulten o actualicen sus datos básicos y cierren la sesión. No
existe registro público ni gestión de contraseñas desde la PWA.

## Modelo de usuario

La app `apps.accounts` define `User`, basado en `AbstractUser`, y se configura como
`AUTH_USER_MODEL`. El campo heredado `email` se elimina: OwnTempo identifica a cada
persona únicamente mediante un `username` único.

Los datos disponibles son:

- `username`: identificador de acceso y dato editable por el usuario.
- `first_name`: nombre opcional.
- `last_name`: apellidos opcionales.
- Los campos administrativos estándar de Django, gestionados solo desde Admin.

No se crea un perfil separado ni un espacio personal.

## Administración

Django Admin permite al administrador:

- Crear usuarios y establecer su contraseña.
- Editar username, nombre y apellidos.
- Activar o desactivar cuentas mediante `is_active`.
- Establecer o restablecer contraseñas.
- Gestionar permisos administrativos cuando sea necesario.

La PWA no muestra registro, cambio de contraseña ni recuperación de acceso. Los
usuarios deben contactar con el administrador doméstico.

## API

### Obtener CSRF

```http
GET /api/v1/auth/csrf/
```

Es público, establece la cookie CSRF y devuelve un token que la PWA envía en las
operaciones mutables.

### Iniciar sesión

```http
POST /api/v1/auth/login/
```

Acepta `username` y `password`, valida CSRF y crea una sesión Django. Devuelve la
cuenta actual cuando las credenciales son correctas. Los errores distinguen datos
ausentes, credenciales incorrectas y cuentas desactivadas sin mostrar información
interna del servidor.

### Cuenta actual

```http
GET /api/v1/account/me/
PATCH /api/v1/account/me/
```

Requiere una sesión válida. `GET` devuelve `id`, `username`, `first_name` y
`last_name`. `PATCH` permite editar únicamente username, nombre y apellidos. La
cuenta se obtiene siempre desde `request.user`; no se acepta un identificador de
otro usuario.

### Cerrar sesión

```http
POST /api/v1/auth/logout/
```

Valida CSRF, invalida la sesión actual y devuelve HTTP `204`. Es idempotente.

## PWA

Al arrancar, la PWA consulta la cuenta actual:

- Sin sesión válida muestra el formulario de login.
- Con sesión válida muestra la pantalla principal y la cuenta del usuario.
- La cuenta permite editar username, nombre y apellidos.
- La cabecera identifica al usuario y ofrece el cierre de sesión.
- Los errores de conexión, autenticación y validación se muestran de forma
  descriptiva.

Las peticiones usan `credentials: include`. Antes de cada operación mutable, la
PWA solicita un token CSRF y lo envía mediante `X-CSRFToken`. No guarda sesiones,
contraseñas ni tokens en almacenamiento web.

## Configuración de seguridad

- Django REST Framework usa `SessionAuthentication`.
- Las APIs son privadas por defecto; healthcheck y CSRF son públicos.
- CORS admite credenciales únicamente desde los orígenes configurados.
- `DJANGO_CSRF_TRUSTED_ORIGINS` define los orígenes de desarrollo autorizados.
- `DJANGO_SECURE_COOKIES=true` activa cookies `Secure` para despliegues HTTPS.
- Las cookies de sesión son `HttpOnly` y usan `SameSite=Lax`.

## Migración inicial

El modelo de usuario propio aparece en `accounts.0001_initial`. Como
`AUTH_USER_MODEL` cambia la identidad base de Django, debe aplicarse sobre una base
de datos nueva. Si un volumen de desarrollo anterior ya tiene las migraciones de
Django aplicadas, debe respaldarse cualquier dato necesario y recrearse el volumen
antes de arrancar esta versión. OwnTempo todavía no tiene migraciones de negocio
que conservar.

## Verificación realizada

- Django detecta la migración como completa y coherente con el modelo.
- `manage.py check` no informa problemas.
- TypeScript y ESLint finalizan correctamente.
- La compilación de producción de la PWA finaliza correctamente.
- El formulario de login se revisó visualmente en escritorio y móvil.

No se añadieron ni ejecutaron tests automatizados.

## Fuera de alcance

- Registro público.
- Email de usuario.
- Cambio o recuperación de contraseña desde la PWA.
- Tokens JWT.
- Segundo factor de autenticación.
- Espacios personales o compartidos.
