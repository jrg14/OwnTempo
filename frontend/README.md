# PWA de OwnTempo

Aplicación web progresiva construida con React, TypeScript y Vite. Está diseñada
para instalarse desde el navegador y adaptarse a móvil, tableta y escritorio.

## Requisitos

- Node.js 22.
- Backend de OwnTempo iniciado en el puerto `8000` para desarrollo local.

## Configuración

En desarrollo, la aplicación consulta `http://localhost:8000` por defecto. Si el
backend utiliza otra dirección, copia `.env.example` a
`.env.development.local`:

```env
VITE_API_URL=http://192.168.1.50:8000
```

Las variables `VITE_*` se incorporan al bundle durante la compilación y nunca
deben contener secretos. En Docker no se define `VITE_API_URL`: la PWA consulta el
mismo origen y Nginx redirige `/api/` al backend.

## Desarrollo

```bash
npm install
npm run dev
```

Vite sirve la aplicación en `http://localhost:5173` y Django permite este origen
mediante CORS solo para desarrollo.

## Compilación y comprobaciones

```bash
npm run typecheck
npm run lint
npm run build
npm run preview
```

La compilación genera `dist/`, incluido el manifiesto web, los iconos y el service
worker. El service worker precachea recursos estáticos, pero no las respuestas de
la API ni los datos del usuario.

## Docker

El `Dockerfile` utiliza una fase Node para compilar la PWA y una imagen Nginx para
servirla. Desde la raíz del repositorio:

```bash
docker compose up --build
```

La aplicación completa queda disponible en `http://localhost:8080`.
