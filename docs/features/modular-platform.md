# Plataforma modular por espacio

## Estado

Implementada y verificada. `tasks` y `shopping` están disponibles; la plataforma
presenta los demás como próximos hasta implementar cada feature.

## Catálogo

El catálogo estable contiene cinco identificadores:

- `tasks`: Tareas.
- `shopping`: Lista de compras.
- `wishlist`: Lista de deseos.
- `calendar`: Calendario.
- `expenses`: Gastos.

Cada definición contiene nombre, descripción, icono semántico, segmento de ruta,
app Django cuando corresponde y estado de disponibilidad. Los identificadores
no dependen del texto visible.

## Configuración por espacio

La app `apps.modules` define `SpaceModule`, con:

- `space`.
- `module_key`.
- `enabled`.
- Fechas de creación y actualización.

La combinación espacio y clave es única y la base de datos rechaza claves fuera
del catálogo. Los cinco módulos comienzan activos. `tasks` y `shopping` tienen
`available=true`; en los demás, `available=false` impide abrirlos hasta que se
implemente su funcionalidad.

Todos los espacios existentes reciben sus configuraciones mediante migración.
Los espacios personales y compartidos nuevos las reciben dentro de su servicio
de creación.

El comando siguiente repara configuraciones faltantes de forma idempotente:

```bash
python manage.py ensure_space_modules
```

## API

### Catálogo

```http
GET /api/v1/modules/catalog/
```

Requiere autenticación y devuelve las cinco definiciones.

### Configuración del espacio

```http
GET   /api/v1/spaces/{space_id}/modules/
PATCH /api/v1/spaces/{space_id}/modules/{module_key}/
```

Los miembros pueden consultar. Solo el propietario puede modificar `enabled`.
Las respuestas combinan configuración y metadatos del catálogo, incluida la ruta
que utilizará el módulo cuando esté disponible.

## Permisos

La plataforma incorpora `HasActiveModule` para los futuros endpoints de negocio.
El permiso exige que la clave exista, esté activa en el espacio y tenga una
feature disponible. Debe combinarse con `IsSpaceMember` para mantener el orden:

```text
sesión -> pertenencia -> módulo activo y disponible -> operación
```

## PWA

Dentro del espacio activo se muestra:

- El catálogo completo.
- Estado activo o inactivo.
- Etiqueta `Próximamente` para features no implementadas.
- Controles de activación únicamente para propietarios.
- Navegación solo para módulos activos y disponibles.
- Estado vacío si no hay módulos activos que se puedan abrir.

La pantalla promocional también refleja los cinco módulos del catálogo inicial.

## Verificación realizada

- Catálogo exacto y autenticado.
- Creación automática para espacios personales y compartidos.
- Restricciones de claves y duplicados en base de datos.
- Reparación idempotente mediante comando.
- Independencia de configuración entre espacios.
- Lectura por miembros y modificación solo por propietarios.
- Rechazo de usuarios ajenos y claves desconocidas.
- Suite de Django, TypeScript, ESLint y build de producción.

## Fuera de alcance

- Modelos y endpoints de deseos, calendario o gastos.
- Panel inicial configurable.
- Activación distinta para miembros del mismo espacio.
- Dependencias entre módulos.
- Instalación de módulos externos.
