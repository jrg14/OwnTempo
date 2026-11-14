# Plan de implementación: arquitectura modular

## Objetivo

Permitir que cada espacio active solo las funcionalidades que necesita y que los
módulos puedan evolucionar con independencia sin romper la base compartida.

## Enfoque propuesto

Cada módulo funcional será una app de Django independiente, por ejemplo `tasks`,
`shopping`, `calendar` o `expenses`. Que un módulo esté desactivado para un espacio
no significa instalar o desinstalar código en ejecución: significa controlar su
disponibilidad para ese espacio mediante configuración y permisos.

Una entidad común `SpaceModule` podrá registrar qué módulos están activos en cada
espacio. Los datos concretos permanecerán en los modelos de cada app y siempre
referenciarán al espacio correspondiente.

## Fases

1. Definir el catálogo estable de identificadores de módulos.
2. Crear la configuración de módulos activos por espacio.
3. Exponer APIs para consultar, activar y desactivar módulos.
4. Crear permisos reutilizables que validen membresía y módulo activo.
5. Definir el contrato común de navegación y resúmenes de módulos.
6. Implementar cada módulo en su propia app y con sus propias pruebas.

## Reglas esenciales

- Desactivar un módulo no debe eliminar sus datos automáticamente.
- Un módulo no puede exponer datos de otro espacio.
- Las reglas de membresía tienen prioridad sobre la activación del módulo.
- Las dependencias entre módulos deben ser explícitas y mínimas.
- Cada módulo debe poder probarse de forma aislada.

## Orden inicial sugerido

1. Tareas, para validar asignación y colaboración.
2. Lista de la compra, para validar cambios compartidos sencillos.
3. Calendario, para incorporar recurrencia y vistas temporales.
4. Gastos, por requerir reglas económicas y de reparto más delicadas.

## Criterio de finalización

Dos espacios pueden tener combinaciones distintas de módulos y la API aplica de
forma consistente la activación, la membresía y el aislamiento de datos.

