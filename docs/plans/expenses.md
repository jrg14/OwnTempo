# Plan de implementación: gastos comunes y ajuste de pareja

## Estado

Implementado. El comportamiento real está documentado en
[`../features/expenses.md`](../features/expenses.md). Este documento conserva
las decisiones y el orden seguido para el módulo `expenses`.

## Objetivo

Sustituir la hoja de cálculo mensual de una pareja por un espacio compartido en
el que se puedan registrar los gastos comunes, indicar quién los ha pagado,
introducir los ingresos de ambos y obtener automáticamente:

- cuánto corresponde aportar a cada persona;
- cuánto ha aportado realmente cada una;
- quién debe compensar a quién y por cuánto;
- cuánto ahorro le queda a cada persona después de su aporte común;
- cuánto gasta cada persona de ese ahorro en gastos personales;
- cuánto ahorro personal conserva finalmente cada una.

La primera entrega estará centrada en gastos comunes y personales de dos
personas. Los gastos personales se calcularán por separado para cada una,
partiendo del ahorro restante después del reparto común.

## Alcance de esta entrega

- Trabajar por periodos mensuales identificados por año y mes.
- Crear, editar y eliminar categorías de gasto del espacio.
- Registrar gastos comunes con fecha, categoría, descripción, importe y persona
  que los ha pagado.
- Introducir los ingresos de cada participante del periodo.
- Elegir una regla de reparto: 50/50, proporcional a ingresos o porcentajes
  personalizados.
- Mostrar el total gastado, el desglose por categoría y los totales pagados por
  persona.
- Calcular el aporte teórico, el aporte real y el ajuste final.
- Mostrar el saldo de cada persona y una transferencia de compensación sencilla.
- Calcular como referencia el dinero restante después del aporte común.
- Permitir que cada persona introduzca manualmente el saldo inicial desde el que
  quiere controlar sus gastos personales.
- Registrar gastos personales separados para cada participante.
- Calcular el ahorro personal restante después de esos gastos.
- Mantener el aislamiento por espacio y conservar los datos aunque el módulo se
  desactive.

Queda fuera de esta primera versión:

- presupuestos previstos por categoría;
- recurrencia automática de gastos;
- importación desde Excel, CSV o bancos;
- múltiples monedas dentro del mismo periodo;
- liquidaciones entre más de dos personas;
- notificaciones y pagos reales.

## Decisiones de producto

- En un espacio compartido cada periodo tendrá exactamente dos participantes.
  En un espacio personal tendrá un único participante y solo habilitará gastos
  personales, saldo inicial y categorías.
- Se guardarán los participantes en el propio periodo para que el resultado no
  cambie si después se modifica la pertenencia al espacio.
- Todos los importes se almacenarán como `Decimal` con dos decimales, nunca como
  `float`. La moneda inicial será EUR y se mostrará como configuración del
  espacio o del periodo para poder ampliarla más adelante.
- El importe de un gasto debe ser positivo. Los reembolsos o correcciones se
  harán editando el gasto o registrando otro gasto positivo, no mediante
  importes negativos en esta versión.
- El gasto se atribuye a una sola persona pagadora. Si una compra la pagan
  ambos, se registrarán dos líneas.
- Los participantes y sus ingresos quedan congelados dentro del periodo al
  crearlo o configurarlo; cambiar miembros del espacio no reescribe periodos
  históricos.
- Cualquier miembro del espacio podrá consultar y gestionar categorías, gastos
  comunes e ingresos del periodo. Cada participante gestionará sus propios
  gastos personales; el otro podrá ver el total personal del resumen, pero no
  el detalle de cada gasto.
- El periodo podrá estar `open` o `closed`. En esta entrega el cierre será una
  protección contra cambios accidentales y no un proceso contable irreversible;
  el propietario podrá reabrirlo.
- Los gastos personales pertenecen exclusivamente a una persona. No participan
  en el ajuste entre miembros y no se mezclan con el total común.
- Un gasto personal no puede superar el saldo personal inicial introducido por
  su propietario. La API rechazará cualquier operación que deje el saldo
  personal negativo.

## Reglas de cálculo

Sea `T` el total de gastos del periodo, `I_i` el ingreso de una persona y `P_i`
lo que ha pagado realmente.

### Aporte teórico

- **50/50:** `aporte_i = T / 2`.
- **Proporcional a ingresos:** `aporte_i = T * I_i / (I_1 + I_2)`. Requiere
  ingresos no negativos y al menos un ingreso positivo.
- **Porcentaje personalizado:** `aporte_i = T * porcentaje_i / 100`. Los dos
  porcentajes deben estar entre 0 y 100 y sumar exactamente 100.

Todos los resultados se redondearán a céntimos usando `Decimal`. El céntimo
residual se asignará de forma determinista a la persona con mayor resto
fraccional, con el identificador de participante como desempate, para que la
suma de aportes coincida siempre exactamente con `T`.

### Aporte real y ajuste

- `diferencia_i = aporte_i - P_i`.
- Una diferencia positiva significa que esa persona debe poner dinero.
- Una diferencia negativa significa que esa persona ha adelantado dinero y debe
  recibirlo.
- Para dos personas se mostrará una única transferencia por el mínimo entre la
  deuda positiva y el crédito positivo. Si el resultado es cero, se mostrará
  “No hay nada que ajustar”.

Ejemplo: si una persona debe aportar 10 EUR y ha pagado 8 EUR, su diferencia es
`+2 EUR` y deberá transferir 2 EUR a la otra persona, salvo que el cálculo
global del periodo produzca un crédito/deuda diferente.

### Restante tras gastos comunes

`ahorro_disponible_i = ingreso_i - aporte_i`

Es la cantidad del ingreso que no se destina a gastos comunes y se muestra como
referencia. No condiciona los gastos personales.

### Gastos personales y saldo final

Sea `S_i` el saldo personal inicial introducido manualmente y `R_i` la suma de
gastos personales de la persona `i`:

`ahorro_final_i = S_i - R_i`

Los gastos personales utilizarán categorías y una interfaz parecidas a las de
los gastos comunes, pero tendrán una única persona propietaria y no tendrán
campo `paid_by` ni cálculo de reparto.

La UI diferenciará claramente: ingreso, aporte común, restante tras gastos
comunes, saldo personal inicial, gasto personal acumulado y saldo personal
final.

## Modelo de datos

Se añadirá una app Django independiente `apps.expenses`.

### `ExpenseCategory`

- `space`: espacio propietario.
- `name`: nombre único dentro del espacio, máximo 80 caracteres.
- `color`: clave visual opcional.
- `is_active`.
- `created_at`, `updated_at`.

Se crearán categorías iniciales de forma idempotente solo si el espacio no tiene
ninguna: vivienda, alimentación, suministros, transporte, ocio y otros. El
usuario podrá renombrarlas, desactivarlas o crear nuevas; desactivar una
categoría no elimina gastos históricos.

### `ExpensePeriod`

- `space`.
- `year`, `month`, con unicidad por espacio.
- `split_mode`: `equal`, `income` o `custom`.
- `status`: `open` o `closed`.
- `created_by`, `created_at`, `updated_at`.

La base de datos impedirá meses inválidos y dos periodos para el mismo espacio.

### `ExpenseParticipant`

- `period`.
- `user`, protegido frente a borrado.
- `income`: importe no negativo, obligatorio cuando el modo es proporcional.
- `personal_starting_savings`: saldo inicial no negativo introducido manualmente
  para controlar los gastos personales.
- `custom_percentage`: porcentaje entre 0 y 100 cuando el modo es personalizado.
- `position`, para un orden estable en la interfaz.

Habrá exactamente dos participantes en espacios compartidos y uno en espacios
personales. No se permitirá repetir usuario y la validación comprobará que
pertenecen al espacio al configurarlo.

### `CommonExpense`

- `period`.
- `category`.
- `description`: texto obligatorio, máximo 200 caracteres.
- `amount`: importe positivo con dos decimales.
- `spent_on`: fecha del gasto.
- `paid_by`: `ExpenseParticipant`.
- `created_by`, `created_at`, `updated_at`.

La categoría y la persona pagadora deberán pertenecer al mismo espacio y
periodo. Un gasto de un periodo cerrado no podrá modificarse salvo que el
periodo se reabra.

### `PersonalExpense`

- `period`.
- `owner`: participante propietario del gasto dentro del periodo.
- `category`.
- `description`: texto obligatorio, máximo 200 caracteres.
- `amount`: importe positivo con dos decimales.
- `spent_on`: fecha del gasto.
- `created_by`, `created_at`, `updated_at`.

La categoría debe pertenecer al espacio y el propietario al periodo. El importe
acumulado de los gastos personales de una persona no podrá superar su saldo
personal inicial. Esta comprobación se hará dentro de una transacción y se volverá
a validar al editar o eliminar gastos.

Los totales y saldos no se persistirán como valores derivados: se calcularán en
un servicio transaccional para evitar que queden obsoletos al editar un gasto.

## API

Todas las rutas exigirán autenticación, pertenencia al espacio y módulo
`expenses` activo.

### Periodos

```http
GET    /api/v1/spaces/{space_id}/expenses/periods/
POST   /api/v1/spaces/{space_id}/expenses/periods/
GET    /api/v1/spaces/{space_id}/expenses/periods/{period_id}/
PATCH  /api/v1/spaces/{space_id}/expenses/periods/{period_id}/
```

La respuesta de detalle incluirá configuración, participantes e ingresos, pero
el resumen financiero se consultará mediante un endpoint específico:

```http
GET /api/v1/spaces/{space_id}/expenses/periods/{period_id}/summary/
```

El resumen devolverá el total, totales por categoría, totales pagados,
aportaciones teóricas, restante tras gastos comunes, saldo personal inicial,
gastos personales, saldo final y transferencias de ajuste. El servidor será la única fuente de
verdad del cálculo; el cliente no reimplementará la fórmula para tomar
decisiones.

### Categorías y gastos

```http
GET    /api/v1/spaces/{space_id}/expenses/categories/
POST   /api/v1/spaces/{space_id}/expenses/categories/
PATCH  /api/v1/spaces/{space_id}/expenses/categories/{category_id}/

GET    /api/v1/spaces/{space_id}/expenses/periods/{period_id}/expenses/
POST   /api/v1/spaces/{space_id}/expenses/periods/{period_id}/expenses/
PATCH  /api/v1/spaces/{space_id}/expenses/periods/{period_id}/expenses/{expense_id}/
DELETE /api/v1/spaces/{space_id}/expenses/periods/{period_id}/expenses/{expense_id}/

GET    /api/v1/spaces/{space_id}/expenses/periods/{period_id}/personal-expenses/
POST   /api/v1/spaces/{space_id}/expenses/periods/{period_id}/personal-expenses/
PATCH  /api/v1/spaces/{space_id}/expenses/periods/{period_id}/personal-expenses/{expense_id}/
DELETE /api/v1/spaces/{space_id}/expenses/periods/{period_id}/personal-expenses/{expense_id}/
```

Los serializers rechazarán campos calculados, participantes externos, importes
negativos, porcentajes inválidos, gastos personales que excedan el ahorro
inicial y cambios en periodos cerrados.

## Servicios y permisos

Se crearán servicios de dominio separados de las vistas:

- `create_period` y `update_period_configuration`;
- `create_category` y `update_category`;
- `create_expense`, `update_expense` y `delete_expense`;
- `create_personal_expense`, `update_personal_expense` y
  `delete_personal_expense`;
- `calculate_period_summary`;
- `build_settlement`.

El resumen leerá los gastos con agregaciones por participante y categoría, y
usará una función única de redondeo para que API y pruebas compartan exactamente
la misma regla.

La autorización seguirá el contrato de la plataforma:

```text
sesión -> miembro del espacio -> expenses activo -> periodo del espacio
```

Un ID de otro espacio debe comportarse como no encontrado dentro del queryset
autorizado. Al desactivar el módulo se bloquean las rutas, pero no se borran
periodos, categorías ni gastos.

## PWA

La ruta será `/spaces/{space_id}/expenses/` y tendrá una experiencia mensual,
priorizando móvil:

1. Selector de mes y estado del periodo.
2. Tarjeta de resumen con total gastado y desglose por categoría.
3. Panel de configuración con participantes, ingresos y regla de reparto.
4. Lista de gastos con filtros por categoría y persona pagadora.
5. Formulario de alta/edición con fecha, categoría, descripción, importe y
   pagador.
6. Bloque “Quién debe a quién” con la transferencia final.
7. Sección individual de gastos personales para cada participante.
8. Bloque de restante común, saldo personal inicial, gasto personal acumulado y
   saldo personal final.

El flujo de configuración debe permitir elegir visualmente entre 50/50,
proporcional a ingresos y porcentajes personalizados. Al cambiar la regla o un
ingreso se refrescará el resumen y se explicará cómo ha cambiado el aporte.

Los gastos personales se mostrarán agrupados bajo cada participante y nunca se
mezclarán con el total común ni con la transferencia de ajuste.

Estados obligatorios: carga inicial, periodo inexistente, periodo vacío, error
de API, validación de importe, ingresos o porcentajes, guardado correcto,
periodo cerrado y módulo no disponible.

## Orden de implementación

1. Cerrar con el producto la política de periodo cerrado.
2. Crear `apps.expenses`, modelos, restricciones y migración.
3. Añadir categorías iniciales idempotentes y administración Django.
4. Implementar servicios de periodos, gastos, redondeo y resumen.
5. Añadir serializers, vistas, URLs y permisos con aislamiento por espacio.
6. Escribir pruebas de reglas de reparto, céntimos, errores y autorizaciones.
7. Marcar `expenses` como disponible en el catálogo después de superar backend.
8. Crear tipos y cliente de API en la PWA.
9. Implementar la vista mensual, configuración, formulario y resumen.
10. Implementar el saldo inicial manual y el listado y formulario de gastos
    personales con validación contra ese saldo.
11. Verificar responsive, accesibilidad, estados vacíos y build de producción.
12. Documentar el comportamiento final en `docs/features/expenses.md` y
    actualizar roadmap y README.

## Pruebas mínimas

### Modelo y cálculo

- No se puede crear un periodo duplicado para el mismo espacio y mes.
- Un periodo exige dos participantes en espacios compartidos y uno en el
  espacio personal.
- Los gastos exigen importe positivo, categoría válida y pagador del periodo.
- 50/50 suma exactamente el total incluso con importes impares en céntimos.
- El reparto proporcional rechaza ingresos con suma cero y suma exactamente el
  total tras el redondeo.
- Los porcentajes personalizados deben sumar 100%.
- La suma de aportes teóricos coincide siempre con el total gastado.
- La suma de pagos reales coincide con la suma de gastos.
- El ajuste produce la transferencia correcta para los casos de deuda, crédito
  y saldo cero.
- El restante común coincide con ingreso menos aporte teórico.
- Los gastos personales se descuentan del saldo personal inicial introducido.
- Los gastos personales no modifican el total común ni el ajuste entre personas.
- No se puede crear ni editar un gasto personal que deje saldo negativo.
- El saldo final coincide con saldo personal inicial menos gasto acumulado.
- Un periodo cerrado bloquea altas, cambios y borrados.

### API y aislamiento

- Un miembro puede consultar y gestionar el módulo de su espacio.
- Un usuario ajeno no puede descubrir categorías, periodos ni gastos.
- Un ID de otro espacio no permite leer, editar ni borrar datos.
- El módulo desactivado bloquea todos los endpoints sin eliminar datos.
- Los campos de auditoría y los valores calculados no pueden modificarse desde
  el cliente.

### PWA

- Se puede cambiar de mes sin mezclar gastos entre periodos.
- El resumen se actualiza después de crear, editar o eliminar un gasto.
- Cambiar el modo de reparto muestra los nuevos aportes y el nuevo ajuste.
- El resumen distingue restante común, saldo personal inicial, gastos personales
  y saldo final.
- Cada persona puede gestionar sus gastos personales sin atribuirlos a la otra.
- Los errores de porcentajes, ingresos e importes se muestran junto al campo.
- La vista es usable con teclado y en móvil.
