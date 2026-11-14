# Frontend de OwnTempo

Aplicación React Native creada con Expo, Expo Router y TypeScript.

## Requisitos

- Node.js 22.
- Backend de OwnTempo iniciado en el puerto `8000`.

## Configuración

La aplicación usa `EXPO_PUBLIC_API_URL` para localizar el backend. Si no se define,
utiliza `http://localhost:8000` en web/iOS y `http://10.0.2.2:8000` en el emulador
Android.

Para un dispositivo físico, copia `.env.example` a `.env.local` y sustituye la URL
por la IP local del ordenador:

```env
EXPO_PUBLIC_API_URL=http://192.168.1.50:8000
```

## Desarrollo

```bash
npm install
npm start
```

También se puede iniciar una plataforma directamente:

```bash
npm run android
npm run ios
npm run web
```

## Comprobaciones

```bash
npm run typecheck
npm run lint
npx expo-doctor
```

