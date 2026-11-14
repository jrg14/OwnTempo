# Comprobación del estado del servicio

## Estado

Implementada y cubierta por pruebas automatizadas.

## Finalidad

Permite comprobar que la API de OwnTempo está ejecutándose y que puede comunicarse
con PostgreSQL. También se utiliza como healthcheck del contenedor del backend.

## API

```http
GET /api/v1/health/
```

El endpoint es público y no requiere autenticación.

Cuando Django y PostgreSQL están disponibles devuelve HTTP `200`:

```json
{
  "status": "ok",
  "service": "owntempo-api",
  "checks": {
    "django": "ok",
    "database": "ok"
  },
  "timestamp": "2026-11-14T10:50:13.468476Z"
}
```

Si la consulta a PostgreSQL falla devuelve HTTP `503`, estado `degraded` y marca
la base de datos como `unavailable`. La respuesta no revela detalles internos del
error.

## Implementación

La app `apps.health` contiene una vista de Django REST Framework con permiso
`AllowAny`. La vista ejecuta `SELECT 1` mediante la conexión configurada de Django.

El `compose.yml` consulta este endpoint periódicamente para evaluar el estado del
contenedor del backend. Antes de aplicar migraciones, el script `wait_for_db.py`
espera de forma limitada a que PostgreSQL acepte conexiones.

## Pruebas

La suite comprueba tanto la respuesta saludable como el código `503` producido al
simular que la conexión con PostgreSQL no está disponible.
