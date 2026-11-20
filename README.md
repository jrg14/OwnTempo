# OwnTempo

**Tu vida, a tu ritmo.**

OwnTempo es una aplicación de organización personal y compartida que permite gestionar diferentes aspectos de la vida cotidiana desde un único lugar.

Su principal objetivo es ofrecer una experiencia sencilla, intuitiva y altamente personalizable, donde la aplicación se adapta a las necesidades de cada usuario, y no al revés.

## 1. Visión del proyecto

Crear una aplicación que centralice las herramientas de organización utilizadas en el día a día, evitando la necesidad de utilizar múltiples aplicaciones independientes.

OwnTempo busca que cada persona pueda organizar su vida a su propio ritmo, seleccionando únicamente las funcionalidades que necesita.

**Principios fundamentales:**

- **Personalización:** cada usuario configura su propia experiencia.
- **Modularidad:** las funcionalidades son independientes y pueden activarse o desactivarse.
- **Simplicidad:** interfaz intuitiva, sin complejidad innecesaria.
- **Colaboración:** posibilidad de organizar información individualmente o con otras personas.
- **Flexibilidad:** adaptación a diferentes estilos de vida.
- **Accesibilidad:** diseñada para usuarios con distintos niveles de experiencia tecnológica.
- **Privacidad:** protección y control de los datos personales y compartidos.

## 2. Público objetivo

OwnTempo no está dirigida exclusivamente a un tipo de usuario.

Debe poder utilizarse en diferentes contextos:

- **Uso individual:** organización de tareas, compras, gastos, eventos y rutinas personales.
- **Parejas:** gestión de responsabilidades, gastos y planificación compartida.
- **Familias:** coordinación de actividades, compras y tareas domésticas.
- **Compañeros de piso:** organización de gastos comunes, limpieza y compras.
- **Otros grupos:** espacios compartidos adaptados a diferentes necesidades.

La aplicación debe permitir que un mismo usuario participe en varios espacios simultáneamente.

## 3. Concepto de espacios

Los espacios son uno de los elementos principales de OwnTempo.

Un espacio representa un entorno de organización que puede ser individual o compartido.

Ejemplos:

- Mi espacio personal.
- Nuestro hogar.
- Mi pareja.
- Piso compartido.
- Otros espacios personalizados.

Cada espacio tendrá:

- Nombre e identidad visual configurables.
- Uno o varios miembros.
- Módulos habilitados.
- Información independiente.
- Configuración propia.
- Permisos de acceso según el rol del usuario.

Un usuario podrá pertenecer a varios espacios y cambiar fácilmente entre ellos.

Los datos de un espacio no deben ser accesibles desde otros espacios sin autorización.

## 4. Sistema modular

OwnTempo estará formada por módulos independientes.

Cada usuario podrá seleccionar qué funcionalidades desea utilizar, ocultando aquellas que no necesite.

### Módulos principales

**Listas de la compra**
- Creación de listas personales o compartidas.
- Añadir, modificar y eliminar productos.
- Cantidades y categorías.
- Marcar productos como comprados.
- Sincronización entre miembros.

**Gestión de tareas**
- Tareas personales y compartidas.
- Asignación de responsables.
- Fechas de vencimiento.
- Prioridades.
- Estados de las tareas.
- Tareas recurrentes.
- Recordatorios.

**Control de gastos**
- Registro manual de ingresos y gastos.
- Categorías personalizables.
- Gastos individuales y compartidos.
- Reparto de gastos entre miembros.
- Resúmenes y estadísticas.
- Presupuestos.

**Calendario**
- Eventos personales y compartidos.
- Planificación de actividades.
- Recordatorios.
- Eventos recurrentes.
- Visualización por día, semana o mes.

### Posibles módulos futuros

- Hábitos y rutinas.
- Planificación de comidas.
- Recetas.
- Inventario doméstico.
- Organización de documentos.
- Objetivos personales.
- Seguimiento de suscripciones.
- Organización de mascotas.
- Notas y listas personalizadas.

Estos módulos no forman parte necesariamente del MVP.

La arquitectura debe facilitar su incorporación futura sin modificar significativamente los módulos existentes.

## 5. Personalización

La personalización será el principal elemento diferenciador de OwnTempo.

El usuario debe sentir que la aplicación se adapta a él.

Se contemplan las siguientes capacidades:

- Activar y desactivar módulos.
- Personalizar el panel principal.
- Reordenar secciones y tarjetas.
- Elegir qué información mostrar.
- Configurar espacios individualmente.
- Personalizar categorías.
- Ajustar preferencias de notificaciones.
- Seleccionar preferencias visuales.
- Modificar la configuración en cualquier momento.

La personalización debe ser sencilla y no requerir conocimientos técnicos.

## 6. Experiencia de usuario

OwnTempo debe transmitir sencillez, tranquilidad y control.

La experiencia debe evitar la sobrecarga visual y la acumulación de opciones innecesarias.

### Onboarding

Durante el primer acceso, la aplicación guiará al usuario mediante una configuración inicial sencilla.

El proceso podrá incluir:

1. Creación de cuenta.
2. Selección del tipo de uso: individual, pareja, familia u otros.
3. Creación del primer espacio.
4. Selección de los módulos deseados.
5. Configuración inicial del panel principal.
6. Invitación opcional de otros miembros.

El usuario podrá modificar posteriormente todas estas preferencias.

### Panel principal

El panel principal será configurable y mostrará únicamente la información relevante para el usuario.

Podrá incluir resúmenes de tareas pendientes, próximas actividades, listas de compra y gastos.

La navegación debe ser consistente y permitir acceder rápidamente a las funciones habituales.

## 7. Colaboración y sincronización

OwnTempo debe permitir la colaboración entre diferentes usuarios.

Características generales:

- Invitaciones para unirse a espacios.
- Gestión de miembros.
- Roles y permisos.
- Información compartida.
- Sincronización de cambios.
- Separación entre información personal y compartida.

La colaboración básica debe ser una característica accesible desde la versión gratuita.

## 8. Plataforma e idioma

La aplicación estará orientada inicialmente a usuarios de habla hispana.

**Idioma inicial:** español.

Se diseñará con una estructura que permita incorporar otros idiomas en el futuro.

**Plataforma objetivo:**
- Aplicación web progresiva (PWA) adaptable a móvil, tableta y escritorio.

La PWA podrá instalarse desde el navegador en la pantalla de inicio de los
dispositivos compatibles, sin publicar una aplicación nativa. Android e iOS no
forman parte del alcance actual; si fueran necesarios en el futuro se evaluará un
cliente específico que reutilice la API existente.

## 9. Arquitectura tecnológica propuesta

La arquitectura inicial estará basada en tecnologías conocidas y mantenibles.

### Backend
- Python.
- Django.
- Django REST Framework.
- API REST.

### Base de datos
- PostgreSQL.

### Frontend PWA
- React.
- TypeScript.
- Vite.
- Service worker y manifiesto web mediante `vite-plugin-pwa`.
- Nginx para servir los archivos estáticos y redirigir `/api/` a Django.

### Herramientas complementarias
- Git para control de versiones.
- Docker y Docker Compose para facilitar el desarrollo y despliegue doméstico.
- Herramientas de IA para asistir en la programación.
- Sistema de suscripciones integrado en una fase posterior.

La arquitectura debe priorizar la mantenibilidad, seguridad, modularidad y control de costes.

Las decisiones tecnológicas podrán revisarse durante el desarrollo.

## 10. Modelo de negocio

OwnTempo utilizará inicialmente un modelo **freemium**.

### Versión gratuita

Permitirá utilizar las funcionalidades esenciales de organización personal y compartida.

El objetivo es que resulte útil sin necesidad de contratar una suscripción.

### Versión Premium

Podrá incluir:

- Personalización avanzada.
- Espacios adicionales o ilimitados.
- Estadísticas e informes avanzados.
- Automatizaciones.
- Recordatorios avanzados.
- Funcionalidades adicionales de determinados módulos.

Se valorará una suscripción mensual y anual a un precio accesible.

La monetización no debe perjudicar la experiencia de usuario ni impedir el uso básico de la aplicación.

No se priorizará la publicidad invasiva.

## 11. MVP — Primera versión funcional

La primera versión debe centrarse en validar la utilidad del producto con el mínimo desarrollo necesario.

### Funcionalidades prioritarias

1. Registro e inicio de sesión.
2. Creación y gestión de espacios.
3. Invitación de miembros.
4. Listas de compra compartidas.
5. Gestión de tareas.
6. Panel principal configurable.
7. Registro básico de gastos.
8. Calendario básico.

Se desarrollarán progresivamente, priorizando la estabilidad y la experiencia de usuario.

### Fuera del alcance inicial

- Integraciones bancarias.
- Asistentes de inteligencia artificial integrados.
- Automatizaciones complejas.
- Funcionalidades empresariales.
- Sistemas avanzados de analítica.
- Integraciones externas no esenciales.

## 12. Desarrollo asistido por inteligencia artificial

El proyecto utilizará herramientas de inteligencia artificial para acelerar el desarrollo y mejorar la productividad.

La IA podrá utilizarse para:

- Diseñar componentes.
- Implementar funcionalidades.
- Generar pruebas.
- Documentar código.
- Revisar arquitectura.
- Detectar errores.
- Proponer mejoras.
- Refactorizar código existente.

El desarrollo seguirá criterios de calidad, seguridad y mantenibilidad.

Las funcionalidades deberán implementarse de manera incremental, evitando generar grandes cantidades de código sin validar.

Las decisiones de arquitectura, permisos, seguridad y modelo de datos deberán revisarse antes de su integración.

## 13. Seguridad y privacidad

La aplicación gestionará información personal y potencialmente sensible.

Por ello, deberá contemplar:

- Autenticación segura.
- Autorización por usuario y espacio.
- Separación de datos privados y compartidos.
- Validación de datos en el backend.
- Comunicaciones cifradas.
- Protección frente a accesos no autorizados.
- Gestión de eliminación de cuentas y datos.
- Copias de seguridad y recuperación.
- Cumplimiento de la normativa de protección de datos aplicable, incluyendo RGPD.

## 14. Objetivos del proyecto

### Corto plazo
- Definir la identidad del producto.
- Diseñar la experiencia inicial.
- Establecer la arquitectura.
- Desarrollar un MVP funcional.
- Probarlo con usuarios reales.

### Medio plazo
- Mejorar la experiencia según el feedback.
- Conseguir usuarios recurrentes.
- Implementar funciones Premium.
- Publicar la aplicación en las tiendas.
- Validar el modelo de monetización.

### Largo plazo
- Ampliar el catálogo de módulos.
- Mejorar la personalización.
- Incorporar nuevos idiomas.
- Desarrollar automatizaciones útiles.
- Conseguir ingresos recurrentes que permitan mantener y evolucionar el proyecto.

## 15. Filosofía del producto

OwnTempo no pretende obligar a las personas a organizarse de una determinada manera.

Cada usuario tiene sus propias necesidades, prioridades y rutinas.

La aplicación debe proporcionar las herramientas necesarias para que cada persona encuentre su propia forma de organizarse.

**OwnTempo — Tu vida, a tu ritmo.**

## Desarrollo local con Docker

### Requisitos

- Docker Engine.
- Docker Compose v2 (`docker compose`).

### Puesta en marcha

1. Copia `.env.example` a `.env` y ajusta las variables si lo necesitas.
2. Construye y levanta PostgreSQL, la API y la PWA:

   ```bash
   docker compose up --build
   ```

3. Abre la PWA en `http://localhost:8080`.
4. Comprueba la API a través del mismo origen en
   `http://localhost:8080/api/v1/health/`. El backend también queda accesible
   directamente en `http://localhost:8000` para desarrollo.

El contenedor del backend espera a PostgreSQL, aplica las migraciones, recopila
los archivos estáticos e inicia Gunicorn. Para ejecutar las pruebas:

```bash
docker compose run --rm backend python manage.py test
```

Para detener los servicios sin eliminar los datos de PostgreSQL:

```bash
docker compose down
```

## Desarrollo local de la PWA

El cliente web se encuentra en `frontend/` y utiliza React, TypeScript y Vite. Con
el backend iniciado, ejecuta:

```bash
cd frontend
npm install
npm run dev
```

La pantalla inicial consulta automáticamente `GET /api/v1/health/`. En desarrollo,
`VITE_API_URL` permite indicar otra dirección para el backend; en la imagen Docker
de producción se usa el mismo origen y Nginx redirige `/api/` al servicio Django.
Consulta `frontend/README.md` para las instrucciones completas.

## Despliegue doméstico

El navegador debe acceder normalmente a un único origen: la PWA se sirve en `/` y
la API en `/api/`. PostgreSQL no publica ningún puerto fuera de la red interna de
Docker. Para acceder desde fuera de la red local se recomienda una VPN o un proxy
seguro con HTTPS, sin exponer directamente Django ni PostgreSQL a Internet.

Los datos persistentes se guardan en el volumen `postgres_data`. Es necesario
establecer una política de copias de seguridad antes de utilizar datos reales.
