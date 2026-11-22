# Plan de implementación: informes mensuales de entrenamiento y salud

## Objetivo

Añadir al módulo `training` un sistema que, para cada mes, reúna los datos de
entrenamiento, actividad y salud del usuario, construya un JSON normalizado y lo
envíe a un modelo local ejecutado con Docker. El modelo analizará ese contexto y
devolverá un informe mensual legible con:

- evolución del mes y comparación con el mes anterior;
- cumplimiento de objetivos y regularidad;
- puntos fuertes y aspectos a mejorar;
- observaciones sobre entrenamiento, pasos y tendencias de salud;
- recomendaciones prácticas y prudentes para el siguiente mes.

El sistema no debe diagnosticar enfermedades ni sustituir a un profesional
sanitario. La IA redacta y resume; los cálculos, las comparaciones y las reglas
de seguridad pertenecen al backend.

## Alcance y decisiones

### Datos incluidos

El contexto mensual se construirá con los modelos ya existentes:

- `TrainingProfile`: estatura y fecha de nacimiento.
- `StrengthWorkout`, `StrengthExercise` y `StrengthSet`: sesiones, duración,
  ejercicios, series, repeticiones, peso y volumen.
- `DailySteps`: pasos diarios y objetivos.
- `HealthMeasurement`: peso, IMC, composición corporal y metabolismo.

El informe solo estará disponible para espacios personales y para su propietario,
igual que el resto del módulo de entrenamiento. No se enviarán datos de otros
usuarios ni de espacios compartidos.

### Generación bajo demanda y regeneración

La primera versión generará el informe desde un botón o endpoint para un mes
concreto. El mismo mes podrá regenerarse si cambian los datos o el prompt. Cada
generación conservará el modelo, la versión del prompt, la fecha y el JSON de
entrada utilizado, de forma que el informe sea auditable.

Más adelante se podrá añadir una tarea programada el primer día de cada mes,
pero no es necesaria para el MVP.

### Modelo local

Se recomienda empezar con Ollama como servicio Docker y un modelo instruct de
aproximadamente 3B parámetros. Un modelo de 1B puede servir para una primera
instalación con pocos recursos, pero normalmente redactará análisis menos
consistentes. El backend hablará con la API HTTP interna de Ollama; el texto no
saldrá de la red local.

La configuración debe permitir cambiar el modelo sin modificar código:

```env
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://ollama:11434
LOCAL_LLM_MODEL=qwen2.5:3b-instruct
LOCAL_LLM_TIMEOUT_SECONDS=180
```

El nombre exacto del modelo será configurable porque dependerá del hardware y
de los modelos disponibles en la instalación.

## Arquitectura propuesta

```text
PWA
  │ POST /monthly-reports/
  ▼
Django training API
  ├─ valida espacio, usuario y mes
  ├─ consulta datos del mes y del mes anterior
  ├─ calcula métricas deterministas
  ├─ crea MonthlyReport(status=pending)
  └─ encola la generación
          │
          ▼
Worker / tarea asíncrona
  ├─ construye el JSON de contexto
  ├─ envía prompt + JSON al LLM local
  ├─ valida la respuesta estructurada
  └─ guarda el informe o el error
          │
          ▼
PostgreSQL: contexto, estado, respuesta y metadatos
```

Para el MVP puede ejecutarse la tarea mediante una cola sencilla compatible con
el despliegue actual. Si todavía no existe Redis o Celery en el proyecto, se
puede implementar inicialmente un comando de gestión que procese informes
pendientes y dejar la interfaz preparada para una cola real. No se recomienda
bloquear una petición HTTP esperando al modelo.

## Modelo de datos

Crear `MonthlyTrainingReport` en `backend/apps/training/models.py`:

```text
space                 ForeignKey(Space)
user                  ForeignKey(User)
month                 DateField      # siempre el primer día del mes
status                choices        # pending, processing, completed, failed
input_payload         JSONField      # snapshot normalizado enviado al modelo
result_payload        JSONField      # respuesta estructurada validada
model_name            CharField
prompt_version        CharField
error_message         TextField      # opcional
created_at            DateTimeField
updated_at            DateTimeField
completed_at          DateTimeField  # opcional
```

Restricciones e índices:

- único por `space + user + month + prompt_version` si se quieren conservar
  varias versiones, o único por `space + user + month` si se reemplaza la
  generación anterior;
- índice por `space`, `user` y `month`;
- `month` debe normalizarse al primer día del mes;
- el `input_payload` queda congelado para poder reproducir el informe;
- no guardar secretos ni datos de autenticación dentro del payload.

## JSON de entrada al modelo

El backend debe generar un contrato estable y pequeño. Los valores calculados
deben incluir unidad, periodo y cantidad de datos disponibles para que el modelo
no confunda ausencia de registros con valor cero.

Ejemplo simplificado:

```json
{
  "schema_version": "1.0",
  "period": {
    "month": "2026-11",
    "from": "2026-11-01",
    "to": "2026-11-30",
    "days_in_period": 30,
    "days_elapsed": 22
  },
  "profile": {
    "height_cm": 178,
    "age_years": 36
  },
  "goals": {
    "steps_daily_default": 8000,
    "notes": "Mejorar regularidad y fuerza"
  },
  "training": {
    "workout_count": 9,
    "total_duration_minutes": 405,
    "average_duration_minutes": 45,
    "active_days": 9,
    "total_volume_kg": 18420.5,
    "exercises": [
      {
        "name": "Sentadilla",
        "sessions": 4,
        "sets": 16,
        "repetitions": 96,
        "volume_kg": 6240,
        "max_weight_kg": 90
      }
    ]
  },
  "steps": {
    "recorded_days": 20,
    "average_steps": 7340,
    "total_steps": 146800,
    "goal_days": 12,
    "goal_completion_rate": 0.60,
    "best_day": {"date": "2026-11-08", "steps": 12140}
  },
  "health": {
    "measurements_count": 4,
    "first": {"date": "2026-11-01", "weight_kg": 82.4},
    "last": {"date": "2026-11-21", "weight_kg": 81.7},
    "changes": {
      "weight_kg": -0.7,
      "body_fat_percentage": -0.4,
      "muscle_mass_kg": 0.2
    }
  },
  "comparison_previous_month": {
    "workout_count_change": 2,
    "average_steps_change": 410,
    "weight_kg_change": -0.3
  },
  "data_quality": {
    "missing_steps_days": 2,
    "health_measurements_are_sparse": true,
    "warnings": ["Solo hay cuatro mediciones de salud"]
  }
}
```

No se deben enviar al modelo las series completas si no aportan valor. Se
conservarán agregados por ejercicio y las primeras/últimas mediciones. Si se
necesita explicar una sesión concreta, podrá incluirse un pequeño resumen de las
últimas sesiones.

## Contrato de salida del modelo

Solicitar exclusivamente JSON y validarlo con un serializer de Django o un
esquema equivalente antes de guardarlo:

```json
{
  "title": "Noviembre 2026: constancia en fuerza",
  "summary": "Texto breve de 2-4 frases.",
  "overall_status": "on_track",
  "scores": {
    "training": 7,
    "activity": 6,
    "health_tracking": 5,
    "consistency": 7
  },
  "highlights": ["..."],
  "improvements": ["..."],
  "next_month_actions": ["..."],
  "cautions": ["Las mediciones son escasas; la tendencia es provisional."]
}
```

Reglas de validación:

- campos obligatorios presentes;
- listas con un máximo de elementos;
- puntuaciones enteras entre 0 y 10;
- `overall_status` limitado a `on_track`, `needs_attention` o
  `insufficient_data`;
- rechazo de texto que presente diagnósticos o instrucciones médicas tajantes;
- si el modelo devuelve texto adicional, intentar extraer un bloque JSON y, si
  no es válido, marcar el informe como `failed` sin reemplazar un informe previo.

## Servicio backend

Crear `backend/apps/training/monthly_reports.py` con responsabilidades
separadas:

1. `normalize_month(value)` valida `AAAA-MM` y devuelve el primer día del mes.
2. `build_monthly_context(space, user, month)` consulta ambos meses y calcula
   agregados con `Decimal` y fechas del servidor.
3. `build_prompt(context)` añade instrucciones fijas, el contrato de salida y
   el JSON, evitando concatenar datos como instrucciones.
4. `request_local_analysis(prompt)` llama al servicio local con timeout,
   reintentos limitados y logs sin datos sensibles.
5. `validate_result(payload)` aplica el serializer de salida.
6. `generate_monthly_report(report_id)` controla la transición de estados y
   guarda resultado, error y metadatos de reproducibilidad.

Los agregados deben calcularse en Python/SQL, no pedir al modelo que sume series.
Hay que distinguir siempre entre `0`, `null` y “sin datos”.

## API

Añadir rutas bajo el namespace existente:

```http
GET  /api/v1/spaces/{space_id}/training/monthly-reports/
POST /api/v1/spaces/{space_id}/training/monthly-reports/
GET  /api/v1/spaces/{space_id}/training/monthly-reports/{id}/
POST /api/v1/spaces/{space_id}/training/monthly-reports/{id}/regenerate/
```

Petición de generación:

```json
{ "month": "2026-11" }
```

La respuesta inicial debe ser `202 Accepted` con `id`, `status` y `month`. El
frontend consultará el detalle hasta recibir `completed` o `failed`, o podrá
actualizarlo mediante polling moderado. La API nunca debe exponer el prompt
interno completo ni el payload a usuarios que no sean el propietario.

## Interfaz

Añadir una sección **Informes mensuales** dentro de la pestaña Salud o como una
cuarta pestaña del módulo. Debe incluir:

- selector de mes;
- botón “Generar informe” y estado de progreso;
- resumen destacado y estado general;
- tarjetas de entrenamiento, actividad y seguimiento de salud;
- comparación con el mes anterior;
- acciones del mes siguiente;
- aviso de datos insuficientes o mediciones escasas;
- fecha, modelo y versión del informe.

Los datos numéricos exactos deben seguir visibles junto al texto generado. El
usuario debe poder regenerar el informe y ver cuándo fue creado.

## Docker y operación local

Ampliar `compose.yml` con un servicio opcional `ollama` y un volumen para los
modelos. El backend debe depender de la disponibilidad de la API, no de que el
modelo ya esté descargado. El primer arranque puede requerir una acción
explícita para descargar el modelo, por ejemplo `ollama pull`.

Requisitos operativos:

- documentar RAM, CPU/GPU y espacio aproximado;
- healthcheck de `/api/tags`;
- timeout para evitar workers bloqueados;
- limitar concurrencia a una generación por usuario/mes;
- conservar el modelo fuera de la imagen del backend;
- permitir `LOCAL_LLM_ENABLED=false` para instalaciones sin IA;
- mostrar un error claro si el servicio local no está disponible.

## Privacidad y seguridad

- No enviar datos fuera de Docker ni registrar el prompt completo en logs.
- Aplicar los permisos del módulo antes de consultar o encolar el informe.
- Tratar `input_payload` y `result_payload` como datos personales sensibles.
- Añadir una opción para eliminar los informes y sus snapshots.
- No incluir nombre, correo u otros identificadores que el modelo no necesite.
- Añadir en la interfaz un aviso: “Análisis orientativo, no diagnóstico médico”.
- Si hay síntomas, lesiones, dolor o señales de riesgo introducidas en notas, el
  resultado debe recomendar consultar a un profesional, sin diagnosticar.

## Plan por fases

### Fase 1: contrato y cálculos

- Crear el modelo, migración y serializers.
- Implementar normalización del mes y agregados deterministas.
- Añadir tests de meses incompletos, datos vacíos, `null`, cambios negativos y
  comparación con el mes anterior.

### Fase 2: integración local

- Añadir cliente HTTP del LLM y configuración por entorno.
- Añadir servicio Ollama al compose de desarrollo.
- Implementar validación estricta del JSON de salida y manejo de errores.
- Crear comando para procesar informes pendientes si aún no hay worker.

### Fase 3: API y frontend

- Exponer listado, creación, detalle y regeneración.
- Añadir la sección de informes con estados de carga, vacío, error y éxito.
- Mostrar métricas calculadas junto con la interpretación de la IA.

### Fase 4: robustez

- Incorporar cola asíncrona real y reintentos con backoff.
- Añadir límites de concurrencia y limpieza de informes antiguos.
- Probar con respuestas inválidas, timeouts y servicio apagado.
- Verificar permisos de espacio personal y ausencia de filtraciones entre usuarios.

## Criterios de aceptación

- Un usuario puede generar un informe para un mes sin bloquear la petición HTTP.
- El JSON enviado contiene solo sus datos y distingue ausencia de datos de cero.
- Los totales y cambios mostrados por la aplicación coinciden con los cálculos del
  backend, independientemente de lo que diga la IA.
- Un modelo local disponible genera una respuesta JSON validada y persistida.
- Un modelo caído, lento o con respuesta inválida produce un estado `failed`
  recuperable y un mensaje útil.
- El usuario puede consultar informes anteriores y regenerar uno.
- Un usuario no puede acceder a informes de otro usuario ni de espacios
  compartidos.
- La suite cubre modelos, permisos, API, agregados, cliente LLM y estados de
  error.

## Archivos previstos

```text
backend/apps/training/
├── models.py                  # MonthlyTrainingReport
├── monthly_reports.py         # agregados, prompt y generación
├── serializers.py             # entrada y salida del informe
├── views.py                   # endpoints
├── urls.py                    # rutas
├── tasks.py                   # worker o adaptador de cola
├── migrations/                # nueva migración
└── tests.py                   # pruebas unitarias y de integración

compose.yml                    # servicio Ollama opcional
docs/features/training.md      # actualización de funcionalidad
docs/plans/training.md         # enlace a este plan
frontend/...                   # sección de informes mensuales
```

