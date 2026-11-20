# OwnTempo — plan de reorganización móvil

## Objetivo

Convertir la pantalla principal en una superficie operativa centrada en el espacio activo y en la siguiente acción útil. El hero de presentación, la cuenta y el diagnóstico dejan de competir con el trabajo cotidiano.

## Arquitectura propuesta

1. **App bar**: marca, avatar y menú.
2. **Contexto activo**: nombre del espacio, tipo y selector.
3. **Acciones rápidas**: dos acciones principales disponibles en ese espacio.
4. **Invitaciones**: solo aparece cuando hay pendientes.
5. **Módulos activos**: lista compacta con estado y acción “Abrir”.
6. **Gestión secundaria**: miembros, configuración de módulos, cuenta y diagnóstico.
7. **Navegación inferior**: Inicio, Espacios y Actividad.

## Plan de implementación

### Fase 1 — Reorganizar composición

- Crear `MobileHome` o convertir `SpacesWorkspace` en el contenido principal.
- Mover el espacio activo al primer viewport.
- Eliminar el hero de la vista autenticada o reservarlo para onboarding.
- Mostrar solo módulos activos; dejar el catálogo en “Configurar módulos”.
- Mover `AccountCard` y `HealthCard` a una pantalla secundaria o acordeón.

### Fase 2 — Añadir acciones móviles

- Definir una lista de acciones rápidas por módulo.
- Hacer que “Abrir” lleve a la ruta real del módulo.
- Añadir navegación inferior con estado activo.
- Mantener el selector de espacio accesible sin ocupar demasiado espacio.

### Fase 3 — Estados y errores

- Mantener los errores junto a la acción que falla.
- Separar errores de autenticación, espacios, invitaciones y módulos.
- Añadir estados vacíos útiles: “Aún no hay tareas”, con CTA directo.
- Sustituir detalles de infraestructura por estado humano; dejar Django/PostgreSQL en diagnóstico.

### Fase 4 — Responsive y accesibilidad

- Diseñar primero a 360–390 px y escalar después a tablet/escritorio.
- Objetivo mínimo táctil: 44 × 44 px.
- Revisar orden de foco y navegación por teclado.
- Verificar contraste, zoom al 200 %, reduced motion y textos largos.

### Fase 5 — Validación

- Probar login, cambio de espacio, aceptación de invitación y apertura de módulo.
- Revisar estados de carga, error y vacío.
- Validar en 360 px, 390 px, 430 px y escritorio.
- Ejecutar `npm run typecheck`, `npm run lint` y `npm run build`.

## Fuera de alcance inicial

- Rediseño completo de módulos internos.
- Cambios en el modelo de permisos del backend.
- Nueva identidad visual completa.
