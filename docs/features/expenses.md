# Gastos comunes y personales

## Estado

Implementado y verificado. Es el quinto módulo de negocio disponible en la
plataforma modular de OwnTempo.

## Comportamiento

El módulo trabaja por meses. Un espacio compartido utiliza exactamente dos
participantes y guarda sus ingresos y la regla de reparto:

- 50/50;
- proporcional a ingresos;
- porcentajes personalizados que suman 100%.

Los gastos comunes registran categoría, concepto, importe, fecha y persona que
pagó. El servidor calcula el total, el aporte que corresponde a cada persona,
lo pagado realmente y una única transferencia de ajuste. Los cálculos utilizan
decimales y asignan cualquier céntimo residual de forma determinista.

Un espacio personal utiliza un único participante y ofrece ingreso mensual,
saldo inicial, gastos personales, categorías y saldo final. No muestra ni
admite gastos comunes, reparto o transferencias de ajuste. El ingreso se usa
para previsiones; el saldo inicial continúa siendo el límite operativo del mes.

## Ahorro y gastos personales

El módulo muestra como referencia cuánto queda tras los gastos comunes:

```text
ingreso - aporte común = restante tras gastos comunes
```

Los gastos personales no dependen de ese resultado. Cada persona introduce
manualmente su saldo personal inicial y el cálculo personal es:

```text
saldo personal inicial - gastos personales = saldo personal final
```

Cada persona solo puede consultar y modificar el detalle de sus gastos
personales. El resumen compartido muestra el saldo inicial y el total personal
de ambos, pero no revela las líneas individuales del otro. Una operación que
deje el saldo personal en negativo se rechaza.

## Modelo de datos

La app `apps.expenses` define:

- `ExpenseCategory`, vinculada al espacio;
- `ExpensePeriod`, único por espacio, año y mes;
- `ExpenseParticipant`, con ingreso, porcentaje y saldo personal inicial;
- `CommonExpense`, con categoría y pagador;
- `PersonalExpense`, con categoría y propietario.
- `MonthlyExpenseReport`, con el snapshot calculado y la interpretación local.

Al crear el primer periodo se generan de forma idempotente las categorías
Vivienda, Alimentación, Suministros, Transporte, Ocio y Otros. Las categorías
adicionales se comparten dentro del espacio.

## API

La API ofrece periodos, resumen calculado, categorías, gastos comunes y gastos
personales bajo `/api/v1/spaces/{space_id}/expenses/`. Todas las rutas requieren
sesión, pertenencia al espacio y el módulo activo. Los querysets aíslan los
identificadores de otros espacios y los gastos personales se filtran por el
usuario actual.

Los periodos pueden cerrarse para bloquear cambios. Cualquier participante
puede cerrarlos y solo el propietario del espacio puede reabrirlos.

Los informes mensuales se sirven bajo `monthly-reports/`. La creación devuelve
`202 Accepted`; el worker común de informes procesa la cola sin bloquear la API.
En un espacio personal solo se agregan los gastos personales del propietario.
En uno compartido solo se agregan los gastos comunes y nunca los detalles
personales de los miembros.

## Informes mensuales

La pestaña **Informes** permite elegir mes, presupuesto opcional, objetivo y
categorías consideradas evitables. Django calcula medias históricas, excesos,
tendencia, meses extraordinarios, recurrencias, proyección anual y escenarios
de reducción del 10 % y 20 %. Ollama recibe ese JSON agregado y devuelve una
interpretación estructurada en español; no realiza los cálculos financieros.

Los meses en curso se identifican como parciales y su gasto se escala según los
días transcurridos únicamente para la previsión anual. La interfaz mantiene el
importe real registrado como dato del mes y presenta todas las predicciones
como estimaciones.

## PWA

La ruta `/spaces/{space_id}/expenses/` incluye:

- selector mensual y creación guiada del periodo;
- configuración de participantes, ingresos y reparto;
- resumen común y por persona;
- transferencia final de ajuste;
- formularios y listados editables de gastos comunes;
- formulario y listado privado de gastos personales;
- restante tras gastos comunes, saldo personal inicial, gasto personal acumulado
  y saldo personal final;
- creación de categorías;
- estados de carga, error, periodo vacío, cerrado y módulo no disponible.
- pestaña de informes con generación asíncrona, escenarios e histórico.

Los espacios personales permiten crear su propio periodo mensual introduciendo
el ingreso mensual y el saldo personal inicial.

## Verificación realizada

- Reparto igual, proporcional y personalizado.
- Redondeo exacto a céntimos.
- Cálculo de pagos, deudas, transferencias y ahorros.
- Rechazo de gastos personales por encima del ahorro.
- Privacidad del detalle personal y aislamiento entre espacios.
- Bloqueo por periodo cerrado y módulo desactivado.
- Migración sincronizada con los modelos.
- Suite completa de Django.
- TypeScript, ESLint y build de producción de la PWA.
