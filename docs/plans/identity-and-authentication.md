# Plan de implementación: identidad y autenticación

## Objetivo

Permitir que una persona cree una cuenta, se identifique y consulte su propia
información utilizando el sistema de autenticación de Django.

## Decisión propuesta

Crear una app `accounts` y definir desde el inicio un modelo `User` basado en
`AbstractUser`. Seguirá utilizando la autenticación, contraseñas y permisos de
Django, pero permitirá ampliar el perfil en el futuro sin sustituir el modelo de
usuario cuando ya existan datos.

Esta decisión debe cerrarse antes de añadir migraciones de negocio. La PWA y la
API se servirán normalmente bajo el mismo origen, por lo que la opción inicial
será la autenticación por sesión de Django con cookies seguras y protección CSRF.
Los tokens se posponen hasta que exista un cliente nativo o una integración externa
que los necesite.

## Fases

1. Definir el modelo de usuario y configurar `AUTH_USER_MODEL`.
2. Crear migraciones y administración básica.
3. Incorporar registro, inicio y cierre de sesión.
4. Añadir un endpoint para consultar y actualizar la cuenta actual.
5. Proteger por defecto las APIs privadas.
6. Añadir recuperación y cambio seguro de contraseña.
7. Configurar cookies, CSRF y HTTPS para el despliegue doméstico.

## Pruebas mínimas

- Registro con datos válidos e inválidos.
- Identificación correcta y credenciales incorrectas.
- Acceso anónimo rechazado en recursos privados.
- Un usuario no puede consultar ni modificar otra cuenta.
- Contraseñas almacenadas mediante los mecanismos seguros de Django.
- Cookies de sesión inaccesibles desde JavaScript y operaciones mutables protegidas
  frente a CSRF.

## Criterio de finalización

Un usuario puede completar el ciclo de alta, autenticación, consulta de su cuenta,
cierre de sesión y recuperación de acceso desde la API.

