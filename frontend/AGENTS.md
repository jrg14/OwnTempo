This is a web-first progressive web application. Prioritize semantic HTML,
accessibility, responsive layouts, browser performance, and installability. Do not
introduce Expo, React Native, Android, or iOS projects unless the product decision
is explicitly reversed.

## Commands

```bash
npm run dev
npm run typecheck
npm run lint
npm run build
npm run preview
```

Run type checking, linting, and a production build before declaring frontend work
complete.

## PWA rules

- Keep the manifest and icons in `vite.config.ts` valid and installable.
- Cache the application shell, not authenticated API responses, unless an offline
  data and conflict-resolution design has been approved.
- Treat `VITE_*` variables as public build-time values; never put secrets in them.
- Preserve the same-origin production model: Nginx serves the PWA and proxies
  `/api/` to Django.
- Use semantic web elements and keyboard-visible focus styles.
- Respect `prefers-reduced-motion` for non-essential animation.

## Structure

- `src/App.tsx`: current application composition.
- `src/components`: reusable UI components.
- `src/hooks`: state and effects.
- `src/api`: typed calls to Django.
- `src/styles.css`: global responsive styles.
- `vite.config.ts`: Vite and PWA configuration.
