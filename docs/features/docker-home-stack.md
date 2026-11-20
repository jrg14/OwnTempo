# Entorno Docker para servidor doméstico

## Estado

Implementado con Docker Compose.

## Finalidad

Permite construir y ejecutar OwnTempo en un servidor doméstico con un único
comando. La composición incluye tres servicios:

- `db`: PostgreSQL 17 con datos persistentes en el volumen `postgres_data`.
- `backend`: Django REST Framework servido con Gunicorn.
- `frontend`: PWA compilada con Vite y servida por Nginx.

## Flujo de arranque

PostgreSQL debe superar primero su comprobación de estado. El backend espera a que
la base de datos acepte conexiones, aplica migraciones, ejecuta `collectstatic` y
arranca Gunicorn. La PWA comienza cuando el healthcheck de Django responde.

Nginx sirve la aplicación en `/`, redirige `/api/` y `/admin/` a Django, y entrega
las rutas del navegador mediante `index.html`. De este modo, el navegador utiliza
un solo origen y la configuración CORS queda limitada al servidor Vite de
desarrollo.

## Puertos

- `${FRONTEND_PORT:-8080}`: entrada principal para la PWA y la API.
- `${BACKEND_PORT:-8000}`: acceso directo al backend para desarrollo y diagnóstico.
- PostgreSQL no publica puertos en el host.

## Operación

```bash
docker compose up --build
docker compose run --rm backend python manage.py test
docker compose down
```

`docker compose down` conserva el volumen de PostgreSQL. La eliminación de
volúmenes no forma parte del flujo normal y debe hacerse únicamente con una copia
de seguridad verificada.

## Límites y seguridad

La composición proporciona el runtime de la aplicación, pero el responsable del
servidor debe añadir HTTPS para accesos fuera de `localhost`, credenciales reales,
copias de seguridad y un mecanismo privado de acceso remoto. Django y PostgreSQL
no deben exponerse directamente a Internet.
