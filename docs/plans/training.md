# Plan de implementación: módulo de entrenamiento

## Estado

Implementado. El comportamiento real y el mockup de referencia están
documentados en [`../features/training.md`](../features/training.md).

La ampliación de informes mensuales se documenta en
[`monthly-training-health-reports.md`](monthly-training-health-reports.md).

## Objetivo

Crear un módulo personal para registrar y consultar:

- Entrenamientos de fuerza.
- Ejercicios, peso utilizado y repeticiones.
- Pasos diarios.
- Evolución de los parámetros de una báscula inteligente.
- Estatura y fecha de nacimiento, a partir de la cual se calculará la edad.

El módulo se integrará en la arquitectura modular existente y utilizará rutas
bajo `/spaces/{space_id}/training/`.

## Decisión principal de producto

`training` solo estará disponible en espacios personales. No se podrá activar ni
utilizar en un espacio compartido, porque contiene datos personales de salud y
composición corporal.

La seguridad se implementará en dos niveles:

1. El espacio debe tener `kind=personal`.
2. El usuario autenticado debe ser el propietario del espacio personal.

Los modelos seguirán referenciando `Space`, como el resto de módulos, y además
guardarán el usuario cuando sea necesario para hacer explícita la propiedad del
registro. La aplicación no dependerá solo de un `user_id` para autorizar datos.

## Integración con el catálogo de módulos

Añadir en `backend/apps/modules/catalog.py`:

```python
ModuleDefinition(
    key="training",
    name="Entrenamiento",
    description="Registra fuerza, pasos diarios y evolución de tu salud.",
    icon="activity",
    route_segment="training",
    app_label="training",
    available=True,
)
```

La configuración deberá seguir estas reglas:

- En espacios personales, `training` podrá estar activo.
- En espacios compartidos, `training` permanecerá desactivado.
- La API rechazará cualquier intento de activarlo en un espacio compartido.
- La PWA no mostrará el módulo dentro de un espacio compartido.
- Los espacios compartidos existentes recibirán una configuración desactivada
  si el mantenimiento de módulos requiere crear todas las entradas del catálogo.
- El módulo no se podrá abrir aunque un cliente manipule manualmente la URL.

Será necesario adaptar `ensure_space_modules` para que aplique esta regla al
crear o reparar configuraciones.

## Aplicación backend

Crear:

```text
backend/apps/training/
```

La aplicación incluirá modelos, migraciones, serializers, vistas, servicios,
URLs, administración y pruebas.

### `TrainingProfile`

Datos personales del usuario:

- `space`.
- `user`.
- `height_cm`.
- `date_of_birth`.
- `created_at`.
- `updated_at`.

Se almacenará `date_of_birth` en lugar de una edad fija, ya que la edad cambia
con el tiempo.

Restricción recomendada:

```text
space + user único
```

El modelo validará que el espacio sea personal y que el usuario sea su
propietario.

### `StrengthWorkout`

Representa una sesión de fuerza:

- `space`.
- `user`.
- `workout_date`.
- `started_at`, opcional.
- `duration_minutes`, opcional.
- `notes`, opcional.
- `created_at`.
- `updated_at`.

Se permitirán varias sesiones en un mismo día.

### `StrengthExercise`

Ejercicio realizado dentro de una sesión:

- `workout`.
- `name`.
- `order`.
- `notes`, opcional.

Ejemplos: sentadilla, press banca, peso muerto o remo con barra.

### `StrengthSet`

Serie concreta de un ejercicio:

- `exercise`.
- `set_number`.
- `weight_kg`.
- `repetitions`.
- `rest_seconds`, opcional.

Validaciones:

- El peso no puede ser negativo.
- Las repeticiones deben ser mayores que cero.
- El número de serie debe ser positivo.

### `DailySteps`

Registro de pasos diarios:

- `space`.
- `user`.
- `date`.
- `steps`.
- `goal`, opcional.
- `notes`, opcional.

Restricción:

```text
space + user + date único
```

### `HealthMeasurement`

Medición diaria de una báscula inteligente:

- `space`.
- `user`.
- `date`.
- `weight_kg`.
- `bmi`.
- `body_fat_percentage`.
- `subcutaneous_fat_percentage`.
- `visceral_fat_level`.
- `body_water_percentage`.
- `muscle_mass_kg`.
- `bone_mass_kg`.
- `basal_metabolic_rate_kcal`.
- `metabolic_age`.
- `notes`, opcional.

Para el MVP se guardará un registro principal por día:

```text
space + user + date único
```

Más adelante se podrán admitir varias mediciones diarias si el uso real lo
justifica.

## API prevista

Todas las rutas requerirán sesión autenticada, pertenencia al espacio, módulo
activo y espacio personal del usuario actual.

### Perfil

```http
GET /api/v1/spaces/{space_id}/training/profile/
PUT /api/v1/spaces/{space_id}/training/profile/
```

### Entrenamientos

```http
GET    /api/v1/spaces/{space_id}/training/workouts/
POST   /api/v1/spaces/{space_id}/training/workouts/
GET    /api/v1/spaces/{space_id}/training/workouts/{id}/
PATCH  /api/v1/spaces/{space_id}/training/workouts/{id}/
DELETE /api/v1/spaces/{space_id}/training/workouts/{id}/
```

### Pasos

```http
GET   /api/v1/spaces/{space_id}/training/steps/
POST  /api/v1/spaces/{space_id}/training/steps/
PATCH /api/v1/spaces/{space_id}/training/steps/{id}/
```

### Salud

```http
GET    /api/v1/spaces/{space_id}/training/health/
POST   /api/v1/spaces/{space_id}/training/health/
PATCH  /api/v1/spaces/{space_id}/training/health/{id}/
DELETE /api/v1/spaces/{space_id}/training/health/{id}/
```

Las consultas históricas aceptarán filtros de fecha:

```text
?from=2026-11-01&to=2026-11-21
```

### Resumen

```http
GET /api/v1/spaces/{space_id}/training/summary/
```

El resumen podrá devolver pasos de hoy, entrenamiento realizado, última medición,
promedio de pasos, entrenamientos de la semana e historial de salud.

## Interfaz frontend

Crear:

```text
frontend/src/api/training.ts
frontend/src/components/training-workspace.tsx
```

Actualizar:

```text
frontend/src/App.tsx
frontend/src/components/icon.tsx
frontend/src/components/space-modules-panel.tsx
```

La ruta frontend será:

```text
/spaces/{space_id}/training/
```

### Vista principal

La pantalla se dividirá en cuatro áreas:

1. **Resumen de hoy**: pasos, entrenamiento y última medición de salud.
2. **Registro rápido**: añadir pasos, medición de salud o entrenamiento.
3. **Entrenamiento de fuerza**: sesiones, ejercicios y series editables.
4. **Salud**: gráfica seleccionable para los diez parámetros de la báscula.

### Formulario de fuerza

Debe permitir:

- Elegir la fecha.
- Añadir uno o varios ejercicios.
- Añadir y eliminar series dinámicamente.
- Introducir peso y repeticiones.
- Añadir notas.
- Guardar la sesión completa.

En móvil, cada ejercicio se mostrará como una tarjeta colapsable para mantener
el formulario manejable.

## Estados de interfaz

Se deberán diseñar y probar estos estados:

- Perfil sin configurar.
- Módulo sin datos.
- Día sin entrenamiento.
- Día sin pasos.
- Sin mediciones de salud.
- Carga en curso.
- Error de API.
- Registro guardado correctamente.
- Datos inválidos.
- Módulo desactivado.
- Acceso a espacio compartido no permitido.

El estado vacío debe ofrecer una acción clara, por ejemplo:

> Empieza configurando tus datos básicos o añade tu primer entrenamiento.

## Métricas del MVP

Incluir inicialmente:

- Promedio de pasos diarios.
- Total de pasos por semana.
- Número de entrenamientos por semana.
- Últimos valores de los diez parámetros de salud.
- Diferencia de peso respecto al primer registro y al anterior.
- Evolución gráfica por parámetro y unidad.
- Volumen aproximado por ejercicio:

```text
peso × repeticiones
```

No se incluirán todavía registros de ingesta o gasto calórico, recomendaciones
médicas ni integraciones con relojes o dispositivos externos. La tasa metabólica
basal se mostrará únicamente como el valor estimado por la báscula.

## Pruebas mínimas

### Backend

- Se puede crear y actualizar el perfil personal.
- La estatura y la fecha de nacimiento se validan correctamente.
- Se pueden crear entrenamientos, ejercicios y series.
- El peso y las repeticiones no aceptan valores inválidos.
- Solo existe un registro de pasos por día y usuario.
- Solo existe una medición de salud por día y usuario.
- Un usuario no puede consultar datos de otro usuario.
- Un usuario no puede utilizar el módulo en un espacio compartido.
- Un módulo desactivado bloquea sus endpoints.
- Los datos quedan aislados entre espacios.
- El resumen calcula correctamente las métricas.

### Frontend

- El módulo aparece en el espacio personal.
- El módulo no aparece en espacios compartidos.
- La ruta manual a un espacio compartido se rechaza.
- Los formularios muestran validaciones y errores.
- Los registros aparecen después de guardarse.
- Los gráficos funcionan con pocos datos y con datos vacíos.
- La vista es usable en móvil y escritorio.

## Orden de implementación

1. Añadir `training` al catálogo.
2. Definir la regla de módulo exclusivo para espacios personales.
3. Crear la aplicación Django y las migraciones.
4. Implementar modelos, restricciones y validaciones.
5. Implementar serializers, servicios, vistas y URLs.
6. Añadir permisos específicos y pruebas backend.
7. Crear la API frontend.
8. Añadir la ruta y `TrainingWorkspace`.
9. Implementar resumen y registros diarios.
10. Implementar el formulario de fuerza.
11. Añadir gráfica seleccionable de salud, pasos y actividad.
12. Integrar estados vacíos, errores y responsive.
13. Ejecutar pruebas backend, lint y build frontend.
14. Actualizar la documentación de la feature una vez implementada.

## Criterios de aceptación

El módulo se considerará completado cuando:

1. Solo esté disponible en el espacio personal del usuario.
2. Sea imposible activarlo o consultarlo desde un espacio compartido.
3. El usuario pueda registrar un entrenamiento con ejercicios, pesos y
   repeticiones.
4. El usuario pueda registrar pasos y los diez parámetros de salud por fecha.
5. El usuario pueda consultar la tendencia histórica de cada parámetro.
6. Los datos estén aislados por usuario y espacio.
7. Existan pruebas automatizadas para permisos, validaciones y cálculos.
8. La interfaz funcione correctamente en escritorio y móvil.

## Fuera de alcance

- Entrenamientos compartidos.
- Perfiles de entrenamiento para varios miembros.
- Integración con Apple Health, Google Fit, Garmin u otros dispositivos.
- Sincronización automática de pasos.
- Recomendaciones médicas o nutricionales.
- Planificación avanzada de rutinas.
- Gestión de objetivos complejos o periodización.
- Registro de calorías o comidas.
