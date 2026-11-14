# Inicio de la aplicación móvil

## Estado

Implementado con React Native, Expo Router y TypeScript.

## Finalidad

Ofrece la primera pantalla de OwnTempo. Explica de forma breve la propuesta de la
aplicación, presenta sus módulos principales y muestra el estado real del backend.

## Comportamiento

- Presenta tareas, calendario, compra y gastos como próximos módulos.
- Explica la separación entre espacios personales y compartidos.
- Consulta `GET /api/v1/health/` al abrir la pantalla.
- Muestra estados de carga, conexión correcta y error.
- Permite repetir manualmente la comprobación.
- Adapta la distribución a móvil y web.

## Configuración

La variable pública `EXPO_PUBLIC_API_URL` determina la dirección del backend. Si no
se define, se utiliza `localhost` en web/iOS y `10.0.2.2` en el emulador Android.

## Estructura

- `src/app`: rutas y layout de Expo Router.
- `src/screens`: composición de pantallas.
- `src/components`: componentes reutilizables.
- `src/hooks`: estado y efectos de interfaz.
- `src/api`: acceso tipado al backend.
- `src/constants`: tema visual compartido.
