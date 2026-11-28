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

**Listas de deseos**
- Productos, experiencias e ideas personales o compartidas.
- Priorización y consulta posterior.
- Separación entre deseos privados y comunes.

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

1. Alta de usuario por parte del administrador e inicio de sesión.
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

### Informes mensuales con IA local

Los módulos de entrenamiento y gastos pueden generar informes mensuales mediante Ollama. La
IA se ejecuta únicamente al activar el perfil opcional `ai` de Docker Compose.
La pestaña **Informes** permite seleccionar un mes, indicar el objetivo del
periodo y encolar el análisis. El servicio `report-worker` procesa las
solicitudes sin bloquear la API.

Ollama se ejecuta con `OLLAMA_NO_CLOUD=1` y su puerto no se publica en el host.
Solo el worker puede acceder a su API mediante la red privada de Docker. La
descarga inicial obtiene el modelo desde el registro de Ollama, pero los JSON de
salud y entrenamiento no se envían fuera del despliegue local.

Los totales, promedios, comparaciones y previsiones se calculan en Django. Ollama solo recibe
un JSON agregado y devuelve la interpretación, que se valida antes de guardarse.
La instalación y el primer informe se explican paso a paso en
[Puesta en marcha completa](#puesta-en-marcha-completa).

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

1. Alta de usuarios mediante Django Admin e inicio de sesión desde la PWA.
2. Creación y gestión de espacios.
3. Invitación de miembros.
4. Listas de compra compartidas.
5. Listas de deseos personales y compartidas.
6. Gestión de tareas.
7. Panel principal configurable.
8. Registro básico de gastos.
9. Calendario básico.

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

## Puesta en marcha completa

### Requisitos

- Docker Engine.
- Docker Compose v2 (`docker compose`).
- Espacio libre para las imágenes, PostgreSQL y, si se activa la IA, el modelo.
- Para los informes, memoria suficiente para ejecutar un modelo local de 3B. El
  modelo configurado ocupa aproximadamente 1,9 GB en disco.

Todos los comandos siguientes se ejecutan desde la raíz del repositorio:

```bash
cd /ruta/al/proyecto/OwnTempo
```

### 1. Configurar las variables de entorno

Crea el archivo local de configuración la primera vez:

```bash
cp .env.example .env
```

Para un entorno doméstico o de producción, cambia al menos
`DJANGO_SECRET_KEY` y las credenciales de PostgreSQL. Las variables relacionadas
con los informes deben quedar así:

```env
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://ollama:11434
LOCAL_LLM_MODEL=qwen2.5:3b-instruct
LOCAL_LLM_TIMEOUT_SECONDS=180
```

El valor de `LOCAL_LLM_MODEL` debe coincidir exactamente con el modelo descargado
en Ollama.

### 2. Elegir el tipo de arranque

Para utilizar toda la aplicación, incluidos los informes mensuales, construye y
levanta los servicios con el perfil `ai`:

```bash
docker compose --profile ai up -d --build
```

Se iniciarán:

- `db`: PostgreSQL.
- `backend`: API Django, migraciones y archivos estáticos.
- `frontend`: PWA servida por Nginx.
- `ollama`: servidor local del modelo.
- `report-worker`: procesador asíncrono de informes.

Si no quieres utilizar los informes con IA, puedes arrancar únicamente la
aplicación principal:

```bash
docker compose up -d --build
```

### 3. Descargar el modelo local

Este paso solo es necesario la primera vez, o cuando cambie
`LOCAL_LLM_MODEL`:

```bash
docker compose --profile ai exec ollama ollama pull qwen2.5:3b-instruct
```

La descarga necesita conexión a Internet. Una vez instalado, los análisis se
realizan localmente y el volumen `ollama_data` conserva el modelo entre
reinicios.

Comprueba que está disponible:

```bash
docker compose --profile ai exec ollama ollama list
```

### 4. Comprobar el estado de los servicios

```bash
docker compose --profile ai ps
```

Los servicios deben aparecer como `running` o `healthy`. También puedes abrir el
health check en `http://localhost:8080/api/v1/health/`.

Si algún servicio falla, consulta sus logs:

```bash
docker compose --profile ai logs --tail=100 backend frontend
docker compose --profile ai logs --tail=100 report-worker ollama
```

### 5. Crear el primer administrador

OwnTempo no ofrece registro público. En una base de datos nueva crea el
administrador inicial con los servicios levantados:

```bash
docker compose exec backend python manage.py createsuperuser
```

Abre `http://localhost:8080/admin/`, inicia sesión con ese administrador y crea
los usuarios que utilizarán la aplicación. Cada usuario obtiene automáticamente
su espacio personal y podrá entrar en la PWA desde `http://localhost:8080`.

### 6. Activar y preparar Entrenamiento

Después de entrar en la PWA:

1. Abre el menú del perfil.
2. Entra en **Configurar módulos**.
3. Selecciona el espacio personal.
4. Activa **Entrenamiento**.
5. Abre el módulo y completa la estatura y la fecha de nacimiento.

El módulo de entrenamiento y sus informes solo funcionan en el espacio personal
del propietario; no aparecen en espacios compartidos.

### 7. Registrar datos del mes

El informe utiliza los datos guardados en el módulo:

- sesiones de fuerza, ejercicios, series, peso, repeticiones y duración;
- pasos diarios y objetivo de pasos;
- peso, IMC y mediciones de composición corporal;
- estatura, edad calculada y objetivo escrito al generar el informe.

Es posible generar un informe con pocos datos, pero indicará que la información
es insuficiente. Para obtener tendencias de salud conviene registrar al menos dos
mediciones durante el mes, idealmente una por semana.

### 8. Generar el primer informe

Dentro del espacio personal, abre:

```text
Entrenamiento → Informes
```

Después:

1. Selecciona el mes actual o uno anterior. No se permiten meses futuros.
2. Escribe el objetivo que tenías para ese periodo.
3. Pulsa **Generar informe**.
4. Espera mientras el estado muestra **En cola** o **Analizando**.

La petición web no queda bloqueada: `report-worker` recoge el trabajo desde
PostgreSQL y la página consulta su estado automáticamente. Cuando termina se
muestran el resumen, las puntuaciones, los puntos fuertes, los ajustes y las
acciones propuestas para el siguiente mes.

Si corriges datos o cambias el objetivo, usa **Regenerar informe**.

### 9. Preparar Gastos personales o comunes

Los informes de gastos funcionan tanto en el espacio personal como en uno
compartido. Para prepararlos:

1. En **Configurar módulos**, activa **Gastos** en el espacio que quieras analizar.
2. Abre **Gastos** y crea el periodo del mes.
3. En el espacio personal, registra el ingreso mensual y el saldo inicial.
4. En el espacio compartido, registra los participantes, sus ingresos y el
   criterio de reparto.
5. Añade los movimientos con una categoría y una fecha del mismo mes.

El informe personal utiliza exclusivamente los gastos personales del
propietario. El informe de un espacio compartido utiliza exclusivamente los
gastos comunes; nunca incorpora las líneas personales de sus miembros. Cuantos
más periodos anteriores existan, mejores serán las comparaciones y la detección
de tendencias. Con menos de dos meses históricos el informe avisa de que las
conclusiones son provisionales.

### 10. Generar un informe de gastos

Dentro del espacio que quieras analizar, abre:

```text
Gastos → Informes
```

Después:

1. Selecciona el mes actual o uno anterior.
2. Añade, si lo deseas, un presupuesto total y un objetivo de ahorro.
3. Marca únicamente las categorías que tú consideres evitables.
4. Pulsa **Generar análisis** y espera a que el worker termine.

El resultado muestra el gasto del mes, la comparación histórica, excesos por
categoría, tendencia, gastos recurrentes o extraordinarios, previsión anual y
escenarios reduciendo el gasto evitable un 10 % o un 20 %. En un mes todavía en
curso, la previsión anual escala el gasto por los días transcurridos y muestra
una advertencia. Puedes cambiar las opciones y pulsar **Regenerar análisis**.

### 11. Arranques posteriores

El modelo y la base de datos se conservan en volúmenes. En los siguientes
arranques solo necesitas ejecutar:

```bash
docker compose --profile ai up -d
```

Abre la aplicación en `http://localhost:8080`. El backend aplica automáticamente
las migraciones pendientes antes de iniciar Gunicorn.

### 12. Diagnóstico de informes

Si un informe termina con error, comprueba primero el modelo:

```bash
docker compose --profile ai exec ollama ollama list
```

Después revisa el worker y Ollama:

```bash
docker compose --profile ai logs --tail=100 report-worker ollama
```

Problemas habituales:

- **El modelo no aparece en `ollama list`:** ejecuta de nuevo `ollama pull`.
- **El nombre del modelo no coincide:** revisa `LOCAL_LLM_MODEL` en `.env` y
  reinicia los servicios.
- **`report-worker` no está iniciado:** asegúrate de usar `--profile ai`.
- **El informe quedó fallido antes de descargar el modelo:** vuelve a la pestaña
  **Informes** y pulsa **Regenerar informe**.
- **La generación supera el tiempo máximo:** aumenta
  `LOCAL_LLM_TIMEOUT_SECONDS` y reinicia el worker.

Para aplicar cambios en `.env` o reconstruir imágenes:

```bash
docker compose --profile ai up -d --build --force-recreate
```

### 13. Pruebas

Para ejecutar la suite completa del backend:

```bash
docker compose run --rm backend python manage.py test
```

Para comprobar el frontend:

```bash
cd frontend
npm install
npm run typecheck
npm run lint
npm run build
```

### 14. Detener la aplicación

Para detener y retirar los contenedores sin borrar PostgreSQL ni el modelo:

```bash
docker compose --profile ai down
```

No utilices `docker compose down -v` salvo que quieras eliminar definitivamente
la base de datos y los modelos descargados.

### Resumen rápido del primer arranque

```bash
cp .env.example .env
docker compose --profile ai up -d --build
docker compose --profile ai exec ollama ollama pull qwen2.5:3b-instruct
docker compose exec backend python manage.py createsuperuser
docker compose --profile ai ps
```

Después abre `http://localhost:8080`, activa Entrenamiento o Gastos en el espacio
correspondiente, registra datos y genera el informe desde la pestaña
**Informes**.

## Operación habitual con Docker

El contenedor del backend espera a PostgreSQL, aplica las migraciones, recopila
los archivos estáticos e inicia Gunicorn. La PWA utiliza el mismo origen y Nginx
redirige `/api/` al backend.

Los datos de PostgreSQL se almacenan en `postgres_data` y los modelos locales en
`ollama_data`. Configura copias de seguridad antes de introducir información
real de salud o entrenamiento.

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

### Administración de usuarios

La creación inicial del administrador y de los usuarios está incluida en la
[guía de puesta en marcha](#5-crear-el-primer-administrador). Desde
`http://localhost:8080/admin/` se pueden crear, desactivar o cambiar las
contraseñas de los usuarios domésticos.

La introducción de `AUTH_USER_MODEL` requiere una base de datos nueva. Si el
volumen de desarrollo anterior ya tenía migraciones aplicadas, respalda primero
cualquier dato necesario y recrea el volumen antes de arrancar esta versión.

## Despliegue doméstico

El navegador debe acceder normalmente a un único origen: la PWA se sirve en `/` y
la API en `/api/`. PostgreSQL no publica ningún puerto fuera de la red interna de
Docker. Para acceder desde fuera de la red local se recomienda una VPN o un proxy
seguro con HTTPS, sin exponer directamente Django ni PostgreSQL a Internet.

Los datos persistentes se guardan en el volumen `postgres_data`. Es necesario
establecer una política de copias de seguridad antes de utilizar datos reales.
