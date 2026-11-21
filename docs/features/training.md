# Entrenamiento personal

## Estado

Implementada y cubierta por pruebas automatizadas. El mockup se conserva como
referencia visual de la jerarquía y los flujos principales.

El plan técnico está documentado en
[`../plans/training.md`](../plans/training.md).

## Mockup

Abrir el mockup en un navegador:

- [`frontend/mockups/training.html`](../../frontend/mockups/training.html)

La pantalla incluye tres vistas navegables:

- **Resumen**: estado del día, pasos, última medición de salud, sesión y registro rápido.
- **Fuerza**: sesiones, ejercicios, series, peso, repeticiones y volumen.
- **Salud**: evolución seleccionable de los parámetros de la báscula inteligente.

El HTML independiente no persiste datos; la PWA implementada utiliza los mismos
flujos contra la API real.

## Comportamiento implementado

El módulo solo aparece en espacios personales. Permite:

- Configurar estatura y fecha de nacimiento; la edad se calcula dinámicamente.
- Registrar pasos y objetivo diario, con un único registro por fecha.
- Registrar una medición diaria de báscula inteligente con peso, IMC, grasa
  corporal, grasa subcutánea, grasa visceral, agua corporal, masa muscular,
  masa ósea, tasa metabólica basal y edad metabólica.
- Crear y eliminar sesiones de fuerza con varios ejercicios y series.
- Guardar peso, repeticiones, duración y notas de una sesión.
- Consultar resumen diario, métricas semanales y una gráfica histórica para cada
  parámetro de salud.

La PWA ofrece las pestañas **Resumen**, **Fuerza** y **Salud**, formularios
adaptados a móvil, estados vacíos y mensajes accesibles de error y confirmación.

## API

```http
GET /api/v1/spaces/{space_id}/training/profile/
PUT /api/v1/spaces/{space_id}/training/profile/

GET  /api/v1/spaces/{space_id}/training/workouts/
POST /api/v1/spaces/{space_id}/training/workouts/
GET/PATCH/DELETE /api/v1/spaces/{space_id}/training/workouts/{id}/

GET/POST  /api/v1/spaces/{space_id}/training/steps/
PATCH     /api/v1/spaces/{space_id}/training/steps/{id}/

GET/POST         /api/v1/spaces/{space_id}/training/health/
GET/PATCH/DELETE /api/v1/spaces/{space_id}/training/health/{id}/

GET /api/v1/spaces/{space_id}/training/summary/
```

Los listados históricos admiten los parámetros `from` y `to` en formato
`AAAA-MM-DD`.

## Modelo y permisos

La app `apps.training` contiene `TrainingProfile`, `StrengthWorkout`,
`StrengthExercise`, `StrengthSet`, `DailySteps` y `HealthMeasurement`.

Cada `HealthMeasurement` agrupa todos los parámetros de una lectura de báscula
y es única por espacio, usuario y fecha. La migración renombra los registros de
peso existentes y los conserva como mediciones históricas incompletas. Las
nuevas mediciones creadas desde la API requieren los diez parámetros.

Todas las rutas requieren:

1. Sesión autenticada.
2. Pertenencia al espacio.
3. Módulo `training` activo.
4. Espacio de tipo `personal` cuyo propietario sea el usuario actual.

Las configuraciones de entrenamiento se crean desactivadas para espacios
compartidos, no se muestran en su catálogo configurable y no se pueden activar
mediante la API.

## Dirección de experiencia

El módulo debe sentirse como un registro personal frecuente, no como un panel de
analítica complejo. La jerarquía propuesta es:

1. Qué ha ocurrido hoy.
2. Qué puede registrar el usuario ahora.
3. Qué ha cambiado durante la semana.
4. Qué tendencia existe a más largo plazo.

El resumen usa una superficie verde para el estado del día y deja los datos
históricos en superficies claras. El ámbar se reserva para acciones de registro,
objetivos y el dato actual en gráficos.

## Estructura de implementación sugerida

La implementación real puede partir de estos bloques:

```text
TrainingWorkspace
├── TrainingHeader
├── TrainingTabs
├── TodayOverview
├── QuickRecordActions
├── StrengthWorkoutList
├── StepsTrend
├── HealthMetricChart
└── TrainingEmptyState
```

En móvil, la navegación debe conservar las tres pestañas, convertir las columnas
en una sola columna y mantener los botones de registro con una altura mínima de
44px. Los ejercicios deben mostrarse como filas compactas o tarjetas colapsables
para que añadir series no desborde la pantalla.

## Estados que el mockup representa

- Día con entrenamiento completado.
- Pasos parcialmente completados.
- Última medición de salud.
- Historial de ejercicios con series y volumen.
- Gráficos con datos históricos.
- Formulario de alta de entrenamiento.
- Formulario de pasos.
- Formulario completo de báscula inteligente.

Durante la implementación también deben añadirse los estados que no se muestran
en el mockup:

- Perfil sin configurar.
- Módulo sin datos.
- Carga.
- Error de API.
- Guardado correcto.
- Espacio compartido sin acceso al módulo.

## Reglas de privacidad visibles en la UX

El módulo solo aparece dentro del espacio personal. En el lateral del mockup se
indica que los datos solo son visibles para el usuario propietario. La
restricción también debe estar protegida en backend, de modo que una ruta escrita
manualmente hacia un espacio compartido no permita consultar ni modificar datos.

## Criterios visuales para la implementación

- Mantener la paleta existente de OwnTempo: verde profundo, fondo claro, líneas
  suaves y acento ámbar.
- Priorizar títulos y valores tabulares legibles.
- Mantener estados de foco visibles para teclado.
- No usar gráficos como sustituto de los valores exactos.
- Mostrar siempre la fecha y la unidad de medida (`kg`, `%`, `kcal`, `años`,
  `pasos`, `min`).
- No presentar métricas médicas ni recomendaciones no calculadas por el producto.
- Mantener la vista usable entre 320px y escritorio.

## Relación con la implementación

La implementación sigue el modelo de datos, API y permisos definidos en el plan.
Los valores del mockup son ilustrativos; la PWA muestra los datos reales del
usuario y conserva su jerarquía, flujos principales y comportamiento responsive.

## Verificación

- Pruebas específicas de entrenamiento y módulos.
- Suite completa de Django.
- Migraciones sincronizadas mediante `makemigrations --check --dry-run`.
- Typecheck, lint y build de producción de la PWA.
