# Plan de implementación: PWA y despliegue doméstico

## Objetivo

Ofrecer OwnTempo desde un servidor doméstico como una aplicación web progresiva
instalable, accesible desde navegadores móviles y de escritorio sin mantener una
aplicación nativa.

## Decisiones adoptadas

- React, TypeScript y Vite como frontend web-first.
- Manifiesto y service worker generados con `vite-plugin-pwa`.
- Django REST Framework como API independiente del cliente.
- Docker Compose como mecanismo de construcción y ejecución.
- Nginx como servidor de archivos estáticos y proxy de `/api/` hacia Django.
- Gunicorn como servidor WSGI; `runserver` queda reservado para desarrollo.
- PWA y API bajo el mismo origen en el despliegue normal.
- Sin React Native, Expo ni proyectos nativos Android/iOS.

## Autenticación prevista

La PWA utilizará preferentemente sesiones de Django con cookies `HttpOnly`,
`Secure` y una política `SameSite` adecuada. Las operaciones mutables deberán
aplicar la protección CSRF de Django. No se guardarán credenciales ni tokens de
renovación en `localStorage`.

Si se incorpora un cliente nativo o una integración externa, se diseñará entonces
un mecanismo de tokens separado sin cambiar el modelo de usuarios y espacios.

## Alcance offline

El service worker guarda los recursos estáticos necesarios para abrir la interfaz,
pero las respuestas de la API no se cachean. La creación y sincronización de datos
sin conexión queda fuera del alcance inicial: requeriría almacenamiento local,
colas de operaciones y una política explícita de resolución de conflictos.

## Despliegue y seguridad

1. Servir `/` y `/api/` desde un único origen.
2. Utilizar HTTPS cuando se acceda mediante un nombre o dirección de red.
3. Mantener PostgreSQL dentro de la red de Docker.
4. Sustituir todos los secretos y contraseñas de ejemplo.
5. Mantener `DEBUG` desactivado y configurar `ALLOWED_HOSTS`.
6. Automatizar copias de seguridad de PostgreSQL y probar su restauración.
7. Favorecer una VPN o túnel privado para acceso remoto.

## Evolución futura

La API REST seguirá evitando dependencias con la PWA. Si más adelante se necesita
una aplicación nativa, podrá crearse un cliente nuevo contra la misma API; no se
mantiene por adelantado una abstracción multiplataforma que complique la PWA.
