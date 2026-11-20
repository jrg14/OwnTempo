# Plan de implementación: espacios, miembros y permisos

## Estado

En desarrollo. El espacio personal y el modelo común de pertenencia están
implementados y documentados en
[`../features/personal-space.md`](../features/personal-space.md). Permanecen
pendientes los espacios compartidos, las invitaciones y la gestión de miembros.

## Objetivo

Proporcionar una base común para mantener separados los datos personales y los
datos compartidos con una pareja, familia, compañeros de piso u otros grupos.

## Modelo de dominio propuesto

- `Space`: contexto personal o compartido, con nombre, tipo y propietario inicial.
- `Membership`: relación entre un usuario y un espacio, con rol y estado.
- `Invitation`: invitación pendiente para incorporarse a un espacio compartido.

Cada recurso de un módulo pertenecerá a un espacio. Un contexto personal será un
espacio con un único miembro; así los módulos no necesitan implementar dos modelos
distintos para datos privados y compartidos.

## Fases

1. Definir espacios personales y compartidos y sus restricciones. Completada.
2. Crear automáticamente el espacio personal al registrar un usuario. Completada.
3. Implementar creación, consulta, edición y abandono de espacios compartidos.
4. Implementar membresías, invitaciones y aceptación o rechazo.
5. Incorporar roles iniciales de propietario, administrador y miembro.
6. Centralizar permisos por espacio para reutilizarlos en todos los módulos.

## Reglas esenciales

- Solo los miembros pueden consultar el contenido de un espacio.
- Un espacio personal no admite miembros adicionales.
- Cada usuario debe conservar acceso a su propio espacio personal.
- El último propietario no puede abandonar un espacio compartido sin transferirlo
  o eliminar el espacio.
- Las consultas de cada módulo deben filtrar siempre por espacios accesibles.

## Pruebas mínimas

- Aislamiento de datos entre espacios.
- Ciclo completo de invitación y membresía.
- Permisos de cada rol.
- Operaciones inválidas sobre el espacio personal.
- Intentos de acceso directo por usuarios ajenos.

## Criterio de finalización

Un usuario dispone de un espacio personal, puede crear un espacio compartido,
invitar a otra persona y ambos acceden únicamente a los espacios autorizados.

