# Plan de implementación: plataforma modular por espacio

## Estado

Implementado. El comportamiento real está documentado en
[`../features/modular-platform.md`](../features/modular-platform.md). Los módulos
de negocio permanecen pendientes y se incorporarán sobre este contrato común.

## Objetivo

Permitir que cada espacio active únicamente las funcionalidades que necesita,
manteniendo una navegación y unas reglas de permisos comunes para todos los
módulos.

Un módulo desactivado deja de estar disponible para ese espacio, pero sus datos
se conservan. La activación no instala ni desinstala código: controla la
disponibilidad funcional y el acceso a la API.

## Catálogo inicial

El catálogo inicial tendrá exactamente estos cinco módulos:

| Identificador | Nombre | Finalidad |
| --- | --- | --- |
| `tasks` | Tareas | Tareas personales o compartidas, con estado, fechas y responsables. |
| `shopping` | Lista de compras | Listas personales o compartidas y productos marcables como comprados. |
| `wishlist` | Lista de deseos | Productos, experiencias o ideas que una persona o un grupo quiere guardar. |
| `calendar` | Calendario | Eventos personales o compartidos, fechas y recordatorios futuros. |
| `expenses` | Gastos | Registro de gastos personales o comunes, con categorías y reparto posterior. |

Los identificadores serán estables y no dependerán del nombre visible, que podrá
traducirse o cambiarse más adelante.

No se añadirán al catálogo inicial hábitos, comidas, inventario, notas,
documentos ni suscripciones.

## Decisiones de producto

- La configuración de módulos pertenece al espacio, no al usuario.
- Todos los miembros de un espacio ven la misma activación de módulos.
- El propietario puede activar o desactivar módulos.
- Un miembro puede consultar un módulo activo, pero no cambiar la configuración
  del espacio.
- El espacio personal utiliza el mismo sistema que un espacio compartido.
- Propuesta de configuración inicial: los cinco módulos comienzan activos para
  que el primer acceso sea útil; el propietario podrá desactivarlos después.
- Desactivar un módulo no elimina datos ni cancela relaciones existentes.
- Un módulo no puede acceder a datos de otro espacio.
- Los cinco módulos iniciales no tendrán dependencias entre sí.

## Modelo de datos

Se añadirá una app común `apps.modules` y una entidad `SpaceModule`:

### `SpaceModule`

- `space`: espacio propietario de la configuración.
- `module_key`: uno de los identificadores del catálogo.
- `enabled`: indica si el módulo está disponible en el espacio.
- `created_at` y `updated_at`.

Restricciones:

- `space + module_key` será único.
- Solo se podrán registrar claves presentes en el catálogo estable.
- Al crear un espacio se crearán sus cinco configuraciones iniciales.
- La eliminación de un `SpaceModule` no se utilizará para desactivar; se cambiará
  `enabled` para conservar la configuración y evitar duplicados.

Los modelos de negocio de cada módulo deberán referenciar `Space` directamente.
No deberán depender de `SpaceModule`, porque los datos deben seguir existiendo
cuando el módulo se desactive.

## Catálogo técnico

El catálogo será la fuente única de metadatos de la plataforma. Cada entrada
contendrá como mínimo:

- `key`.
- `name`.
- `description`.
- `icon` o identificador visual semántico.
- `app_label` de Django, cuando el módulo tenga backend implementado.
- `route` de la PWA.
- `available`: indica si la feature está implementada y puede abrirse.

La API no expondrá claves arbitrarias recibidas del cliente. Validará siempre
contra este catálogo.

## API prevista

Todas las rutas requerirán sesión autenticada y pertenencia al espacio.

### Catálogo disponible

```http
GET /api/v1/modules/catalog/
```

Devuelve los cinco módulos iniciales y sus metadatos. Los módulos aún no
implementados podrán aparecer como `available=false`, pero no se podrán abrir.

### Configuración de un espacio

```http
GET   /api/v1/spaces/{space_id}/modules/
PATCH /api/v1/spaces/{space_id}/modules/{module_key}/
```

Respuesta prevista:

```json
{
  "key": "tasks",
  "name": "Tareas",
  "enabled": true,
  "available": true,
  "route": "/spaces/12/tasks/"
}
```

El `PATCH` recibirá:

```json
{
  "enabled": false
}
```

Solo el propietario podrá modificar `enabled`. Un miembro que no sea propietario
recibirá `403`; un módulo inexistente recibirá `404` sin crear configuración.

### Contrato de módulos

Cada módulo implementado deberá proporcionar:

- Identificador estable.
- Rutas agrupadas bajo el espacio activo.
- Filtrado obligatorio por `space`.
- Permiso común de miembro + módulo activo.
- Permiso de propietario para su configuración cuando corresponda.
- Pruebas de aislamiento y de módulo desactivado.
- Un resumen opcional para el panel futuro.

## Permisos reutilizables

Se crearán permisos comunes:

- `IsSpaceMember`: el usuario tiene una pertenencia activa.
- `IsSpaceOwner`: el usuario tiene rol `owner`.
- `HasActiveModule`: el módulo solicitado existe y está activo en ese espacio.

El orden de autorización será:

```text
sesión válida
    -> miembro del espacio
        -> módulo activo
            -> operación permitida por el rol
```

La falta de pertenencia tendrá prioridad sobre la activación del módulo. Saber
que un módulo está activo nunca debe permitir descubrir un espacio ajeno.

## Navegación de la PWA

La PWA incorporará dos niveles de contexto:

1. Selector de espacio: personal o compartido.
2. Navegación de módulos activos dentro del espacio seleccionado.

La navegación deberá:

- Cargar la configuración al cambiar de espacio.
- Mostrar solo módulos activos y disponibles.
- Mantener una ruta clara para el espacio y módulo actuales.
- Mostrar una configuración de módulos al propietario.
- No mostrar módulos desactivados como si fueran utilizables.
- Mostrar un estado vacío si un espacio no tiene módulos activos.
- Mantener accesibles los módulos aunque cambie el nombre del espacio.

## Activación inicial y migraciones

La migración creará `SpaceModule` para los espacios existentes. Los nuevos
espacios recibirán la configuración inicial mediante el servicio de creación de
espacios.

La operación deberá ser idempotente para poder reparar espacios incompletos con
un comando de mantenimiento, por ejemplo:

```bash
python manage.py ensure_space_modules
```

Si un módulo se desactiva, no se modifican ni eliminan sus datos. Si una futura
migración añade un nuevo módulo al catálogo, decidirá explícitamente si se activa
por defecto en espacios existentes.

## Orden de implementación

1. Crear `apps.modules` y el catálogo estable de cinco módulos.
2. Crear `SpaceModule`, migración y configuración inicial de espacios.
3. Añadir catálogo y configuración a la API.
4. Añadir permisos reutilizables de miembro, propietario y módulo activo.
5. Integrar selector de espacios y navegación de módulos en la PWA.
6. Implementar el módulo `tasks` como primera validación del contrato.
7. Implementar `shopping`.
8. Implementar `wishlist`.
9. Implementar `calendar`.
10. Implementar `expenses`, después de validar las reglas de reparto y privacidad.

## Pruebas mínimas

### Plataforma

- El catálogo devuelve exactamente los cinco módulos iniciales.
- Las claves del catálogo son únicas y estables.
- Cada espacio recibe una configuración por módulo.
- La configuración de un espacio no aparece en otro.
- Desactivar un módulo conserva sus datos.
- Repetir el comando de mantenimiento no duplica configuraciones.

### Permisos

- Un usuario anónimo no puede consultar el catálogo privado de un espacio.
- Un usuario ajeno no puede consultar ni modificar módulos de otro espacio.
- Un miembro puede consultar un módulo activo.
- Un miembro no puede activar ni desactivar módulos.
- El propietario puede cambiar la activación.
- Un módulo desactivado bloquea sus endpoints de negocio.
- Un módulo no disponible no puede abrirse aunque esté configurado.

### PWA

- El selector cambia de espacio sin mezclar configuraciones.
- Solo aparecen módulos activos y disponibles.
- El propietario ve la configuración de módulos.
- Los miembros no ven controles de propietario.
- La ruta y el estado activo se actualizan al cambiar de espacio.
- Se muestra un estado vacío cuando no hay módulos activos.

## Criterios de aceptación

La plataforma se considerará completada cuando:

1. Cada espacio tenga una configuración independiente de los cinco módulos.
2. El propietario pueda activar y desactivar módulos desde la PWA.
3. Los miembros vean únicamente módulos activos y disponibles.
4. La API rechace cualquier acceso sin pertenencia o con el módulo desactivado.
5. Desactivar un módulo no elimine sus datos.
6. Un módulo nuevo pueda añadirse al catálogo sin modificar los modelos de los
   demás módulos.
7. `tasks` pueda implementarse sobre el contrato común y superar sus pruebas de
   aislamiento.

## Fuera de alcance

- Panel inicial configurable.
- Dependencias complejas entre módulos.
- Activación por usuario dentro de un mismo espacio.
- Marketplace o instalación de módulos externos.
- Módulos no incluidos en el catálogo inicial.
