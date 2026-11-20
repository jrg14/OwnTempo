# Identidad, espacios y colaboración

## Usuarios

Cada persona tendrá una cuenta basada en el sistema de usuarios de Django. La
cuenta identificará al usuario en toda la aplicación y le permitirá acceder a sus
datos personales y a los grupos de los que forme parte.

## Espacios

Se propone utilizar **espacio** como concepto común para representar un contexto
de organización:

- Un espacio personal pertenece a una sola persona.
- Un espacio compartido reúne a varias personas y representa, por ejemplo, una
  pareja, una familia o un piso compartido.

Los grupos serán, por tanto, espacios compartidos. Este enfoque permite que los
módulos trabajen siempre dentro de un espacio y mantengan aislados sus datos.

## Ejemplos

- `Personal de Ana`: gastos, calendario y tareas privadas de Ana.
- `Ana y Luis`: calendario y lista de la compra de la pareja.
- `Familia García`: tareas domésticas y calendario familiar.
- `Piso compartido`: gastos comunes y turnos de limpieza.

## Capacidades deseadas

- Crear, editar y abandonar espacios compartidos.
- Invitar y eliminar miembros.
- Definir roles y permisos.
- Activar módulos distintos en cada espacio.
- Cambiar rápidamente entre espacios.
- Mantener una separación estricta de la información.

## Decisiones adoptadas

- Cada usuario tiene exactamente un espacio personal.
- Los datos privados pertenecen al espacio personal y los comunes a un espacio
  compartido.

## Cuestiones abiertas

- Qué roles estarán disponibles en la primera versión.
- Cómo se enviarán y aceptarán las invitaciones.
- Cómo se mostrará información de varios espacios en una vista global.

