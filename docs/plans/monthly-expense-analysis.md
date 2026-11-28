# Plan de implementación: análisis mensual de gastos

## Objetivo

Añadir al módulo `expenses` informes mensuales con IA local para estudiar gastos
personales y gastos comunes. El informe debe identificar gasto evitable, explicar
la evolución histórica y proyectar gasto y ahorro hasta final de año.

La IA no realizará operaciones contables. Django calcula importes, medias,
comparaciones, tendencias y escenarios; Ollama recibe un JSON agregado y redacta
una interpretación estructurada.

## Alcance personal y común

El alcance depende del tipo de espacio:

- En un espacio `personal`, el informe analiza exclusivamente los
  `PersonalExpense` del propietario.
- En un espacio `shared`, el informe analiza exclusivamente los
  `CommonExpense` del espacio.
- Los gastos personales nunca se incorporan al informe común.
- El informe personal solo es visible para el propietario.
- El informe común es visible para los miembros del espacio compartido.

Se conservará un informe por espacio y mes. En un espacio compartido todos los
miembros consultan el mismo snapshot y cualquiera con acceso al módulo puede
regenerarlo.

## Decisiones de producto

### Categorías evitables

La aplicación no decidirá por sí sola que una categoría es prescindible. Al
generar el informe, el usuario seleccionará las categorías que considera
evitables, por ejemplo ocio, restaurantes o compras.

El backend calculará:

- gasto del mes en categorías evitables;
- porcentaje respecto al gasto total;
- exceso frente a la media histórica de esas categorías;
- ahorro simulado al reducir ese gasto un 10 % o un 20 %.

“Ahorro potencial” se mostrará como simulación, no como dinero que
necesariamente podría haberse ahorrado.

### Presupuesto mensual

El formulario permitirá indicar un presupuesto total opcional para el mes. Se
guardará junto al snapshot del informe, sin modificar los periodos existentes.
El informe comparará el gasto con:

1. el presupuesto, cuando exista;
2. la media histórica, siempre que haya meses suficientes.

Los presupuestos por categoría quedan fuera del MVP. Las categorías se comparan
con su propia media histórica.

### Ingreso y ahorro personal

`ExpenseParticipant.income` ya existe, pero en los espacios personales la
interfaz lo guarda actualmente a cero. Se ampliará la configuración personal para
registrar ingreso mensual y saldo inicial por separado.

- El ingreso se utiliza para proyectar ahorro anual.
- El saldo inicial sigue siendo el límite disponible para registrar gastos
  personales en ese periodo.
- Los meses antiguos sin ingreso producirán una proyección de ahorro
  `null` y una advertencia de datos insuficientes.

Para gastos comunes, la proyección usa la suma de ingresos de los participantes
y se describe como “disponible del hogar después de gastos comunes”; no pretende
representar el ahorro real tras gastos personales.

## Cálculos deterministas

### Referencia histórica

Para el mes analizado se usarán como máximo los 12 meses anteriores con periodo
registrado en el mismo espacio y alcance.

Por cada categoría:

- total actual;
- media histórica;
- diferencia absoluta;
- diferencia porcentual, cuando la media sea mayor que cero;
- exceso: `max(total_actual - media_histórica, 0)`.

Si no hay al menos dos meses históricos, la comparación se marcará como
provisional.

### Evolución

El JSON incluirá una serie mensual con:

- gasto total;
- gasto por categoría;
- ingresos registrados;
- número de movimientos.

También incluirá:

- cambio frente al mes anterior;
- cambio frente al mismo mes del año anterior;
- pendiente lineal de los últimos seis meses;
- dirección `increasing`, `decreasing` o `stable`;
- meses extraordinarios.

Un mes se considera extraordinario si supera la media histórica más el mayor
valor entre un 20 % de esa media y una desviación estándar.

### Gastos puntuales y recurrentes

- Puntuales: los movimientos de mayor importe del mes, limitados a cinco.
- Recurrentes: descripciones normalizadas que aparecen en al menos dos meses
  distintos del histórico.
- Solo se enviarán al modelo descripciones necesarias y se tratarán como datos no
  confiables, nunca como instrucciones.

### Predicción anual

Para cada mes restante del año:

1. usar el gasto del mismo mes de años anteriores cuando exista;
2. en caso contrario, usar la media reciente ajustada por la tendencia;
3. no permitir predicciones negativas.

El total anual será:

`gasto real hasta el mes analizado + gasto previsto de los meses restantes`.

La misma fórmula se aplicará por categoría. Si el mes actual está incompleto, su
gasto se anualizará según los días transcurridos y se añadirá una advertencia.

### Escenarios

El backend calculará:

- proyección sin cambios;
- proyección reduciendo un 10 % el gasto evitable previsto;
- proyección reduciendo un 20 % el gasto evitable previsto;
- ahorro anual estimado para cada escenario cuando haya ingresos suficientes.

## Modelo de datos

Crear `MonthlyExpenseReport`:

```text
space                    ForeignKey(Space)
requested_by             ForeignKey(User)
month                    DateField
scope                    choices: personal | common
goal                     TextField
monthly_budget           DecimalField, opcional
avoidable_category_ids   JSONField
status                   pending | processing | completed | failed
input_payload            JSONField
result_payload           JSONField
model_name               CharField
prompt_version           CharField
error_message            TextField
created_at                DateTimeField
updated_at                DateTimeField
completed_at              DateTimeField, opcional
```

Restricción única: `space + month`. El alcance se deriva de `Space.kind` y no
se acepta desde el cliente.

El snapshot conserva las decisiones y datos agregados utilizados. Al regenerar
se reemplaza el snapshot anterior del mismo espacio y mes.

## JSON de entrada

Ejemplo resumido:

```json
{
  "schema_version": "1.0",
  "scope": "personal",
  "period": {"month": "2026-11", "is_partial": true},
  "goal": "Ahorrar 500 euros al mes",
  "budget": {
    "monthly": 1800,
    "actual": 1940,
    "difference": 140
  },
  "current_month": {
    "total": 1940,
    "income": 2600,
    "movement_count": 28,
    "categories": [
      {
        "id": 5,
        "name": "Ocio",
        "total": 310,
        "historical_average": 190,
        "excess": 120,
        "avoidable": true
      }
    ]
  },
  "evolution": {
    "monthly": [],
    "previous_month_change": 85,
    "previous_year_same_month_change": -40,
    "trend": "increasing",
    "extraordinary_months": []
  },
  "avoidable_spending": {
    "current_total": 520,
    "historical_excess": 170,
    "reduction_10": 52,
    "reduction_20": 104
  },
  "annual_forecast": {
    "projected_expenses": 22100,
    "projected_income": 31200,
    "projected_savings": 9100,
    "by_category": [],
    "scenarios": {
      "baseline": {},
      "reduce_avoidable_10": {},
      "reduce_avoidable_20": {}
    }
  },
  "recurring_expenses": [],
  "largest_expenses": [],
  "data_quality": {"historical_months": 8, "warnings": []}
}
```

## Contrato de salida de la IA

```json
{
  "title": "Noviembre: el ocio explica el exceso",
  "summary": "Resumen de dos a cuatro frases.",
  "overall_status": "needs_attention",
  "scores": {
    "spending_control": 6,
    "trend": 5,
    "savings_outlook": 7
  },
  "avoidable_findings": ["..."],
  "trend_findings": ["..."],
  "forecast_findings": ["..."],
  "recommended_actions": ["..."],
  "cautions": ["..."]
}
```

Todas las listas tendrán un máximo de cinco elementos y las puntuaciones estarán
entre 0 y 10. La respuesta se validará antes de guardarse.

## API

```http
GET  /api/v1/spaces/{space_id}/expenses/monthly-reports/
POST /api/v1/spaces/{space_id}/expenses/monthly-reports/
GET/DELETE /api/v1/spaces/{space_id}/expenses/monthly-reports/{id}/
POST /api/v1/spaces/{space_id}/expenses/monthly-reports/{id}/regenerate/
```

Petición:

```json
{
  "month": "2026-11",
  "goal": "Reducir ocio sin eliminarlo",
  "monthly_budget": "1800.00",
  "avoidable_category_ids": [5, 8]
}
```

La creación y regeneración devolverán `202 Accepted`.

## Worker e IA local

El worker existente `process_monthly_reports` procesará las colas de
entrenamiento y gastos. Ambas integraciones compartirán un cliente local de
Ollama para evitar duplicar timeouts, extracción de JSON y manejo de errores.

El worker:

1. recupera trabajos interrumpidos;
2. reclama un informe con bloqueo y `skip_locked`;
3. construye el snapshot;
4. llama a Ollama;
5. valida y persiste el resultado;
6. marca errores recuperables como `failed`.

## Interfaz

El módulo de gastos añadirá una vista **Informes** accesible aunque el mes
seleccionado todavía no tenga un periodo, porque el histórico puede existir.

La vista incluirá:

- selector de mes;
- presupuesto opcional;
- objetivo en texto;
- categorías evitables seleccionables;
- estado de generación;
- total, referencia y diferencia;
- evolución y comparación;
- proyección anual y ahorro;
- escenarios 10 % y 20 %;
- interpretación de la IA;
- historial de informes;
- regeneración y borrado.

En espacios personales la copia hablará de “tus gastos”. En espacios compartidos
hablará de “gastos comunes” y “disponible del hogar”.

## Privacidad y límites

- Los informes personales solo consultan movimientos del usuario.
- Los informes comunes no incluyen gastos personales de ningún miembro.
- Ollama permanece en la red privada de Docker.
- No se envían nombres de usuario, correos ni credenciales al modelo.
- Una predicción no es una garantía financiera.
- La aplicación no ofrecerá asesoramiento de inversión, crédito o fiscalidad.
- Las descripciones de movimientos se tratan como datos no confiables.
- Los importes exactos mostrados proceden del backend, no del texto generado.

## Fases de implementación

1. Modelo, migración, ingreso personal y contrato de serializers.
2. Agregados históricos, tendencias, extraordinarios y proyección.
3. Cola compartida, cliente Ollama y endpoints.
4. Pestaña de informes y estados responsive.
5. Pruebas de privacidad, fórmulas, API, worker y errores.
6. Actualización de documentación y README.

## Criterios de aceptación

- Un informe personal no contiene gastos comunes ni de otros usuarios.
- Un informe común no contiene gastos personales.
- Las categorías evitables proceden de la selección del usuario.
- Los excesos, comparaciones y escenarios se calculan sin usar la IA.
- La proyección indica datos insuficientes cuando faltan ingresos o histórico.
- Dos miembros del mismo espacio ven el mismo informe común.
- El endpoint responde sin esperar a Ollama.
- Un fallo del modelo conserva los gastos y permite regenerar.
- La interfaz funciona entre 320 px y escritorio.
- Migraciones, pruebas de Django, typecheck, lint y build quedan correctos.

