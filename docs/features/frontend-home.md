# Inicio de la PWA

## Estado

Implementado como aplicación web progresiva con React, Vite y TypeScript.

## Finalidad

Ofrece la primera pantalla de OwnTempo. Explica de forma breve la propuesta de la
aplicación, presenta sus módulos principales y muestra el estado real del backend.
Solo se muestra después de comprobar que existe una sesión válida; en caso
contrario, la PWA presenta la pantalla de acceso.

## Comportamiento

- Presenta y permite abrir tareas, compras, deseos, calendario y gastos desde el
  espacio activo cuando están habilitados.
- Explica la separación entre espacios personales y compartidos.
- Consulta `GET /api/v1/health/` al abrir la pantalla.
- Muestra estados de carga, conexión correcta y error.
- Permite repetir manualmente la comprobación.
- Adapta la distribución a móvil, tableta y escritorio.
- Incluye manifiesto web, iconos instalables y service worker con actualización
  automática de los recursos estáticos.
- No almacena en caché las respuestas de la API ni promete funcionamiento offline
  de los datos de negocio.

## Configuración

La variable de compilación `VITE_API_URL` determina la dirección del backend. En
desarrollo se utiliza `http://localhost:8000` si no se define. En la imagen Docker
de producción se omite para consumir `/api/` desde el mismo origen que la PWA.

## Estructura

- `src/App.tsx`: composición de la pantalla actual.
- `src/main.tsx`: punto de entrada de React.
- `src/components`: componentes reutilizables.
- `src/hooks`: estado y efectos de interfaz.
- `src/api`: acceso tipado al backend.
- `src/styles.css`: estilos responsivos y accesibles.
- `vite.config.ts`: compilación, manifiesto y service worker de la PWA.

## Decisión de plataforma

OwnTempo es web-first y no mantiene clientes nativos Android o iOS. La API REST
permanece separada para que un cliente nativo pueda añadirse en el futuro sin
condicionar la implementación actual.
