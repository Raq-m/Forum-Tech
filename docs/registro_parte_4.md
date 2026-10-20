# FORUM TECH — Registro de la parte 4

Fecha: 17/10/2026
Rama: feature/forum-interaccion
Tema: Interaccion, moderacion y comunidad

## 1. Objetivo

Implementar interacciones entre usuarios, notificaciones y herramientas
de moderacion sobre los hilos y respuestas de FORUM TECH.

## 2. Trabajo implementado

### Base del foro
- Modelos de hilos y respuestas relacionados con el usuario personalizado.
- Pagina de detalle con respuestas y puntuaciones.
- Publicacion de respuestas con autor asignado desde el servidor.

### Votaciones
- Votos positivos y negativos en hilos y respuestas.
- Cambio y retirada del voto.
- Un unico voto por usuario y publicacion.
- Inicio de sesion obligatorio.
- Botones que actualizan la puntuacion sin recargar la pagina.

### Notificaciones
- Avisos al autor cuando otra persona responde a su hilo.
- Menciones @usuario en nuevos hilos y respuestas.
- Busqueda de usuarios sin distinguir mayusculas.
- Prevencion de avisos propios y menciones repetidas.
- Avisos por votos positivos en respuestas.
- Bandeja privada y marcado como leido.
- Conexion WebSocket autenticada y canal privado por usuario.
- Aviso en pantalla sin recargar la pagina.

### Reportes y moderacion
- Reportes de hilos y respuestas por spam, conducta inapropiada o duplicados.
- Prevencion de reportes repetidos por usuario y publicacion.
- Panel administrativo para revisar o descartar reportes.
- Grupo Moderadores con permisos asignados.
- Bloqueo y desbloqueo de hilos.
- Rechazo de nuevas respuestas en hilos bloqueados.
- Eliminacion suave y restauracion de hilos y respuestas.
- Restricciones de acceso y acciones sobre contenido eliminado.
- Suspension temporal de usuarios y levantamiento de la suspension.
- Restricciones aplicadas tambien a sesiones ya abiertas.
- Fusion de hilos con confirmacion y permisos.
- Movimiento de respuestas conservando sus votos.
- Actualizacion de notificaciones asociadas a respuestas movidas.
- Redireccion del enlace original al destino.
- Rechazo de acciones sobre el hilo original fusionado.

### Filtros de contenido
- Validacion de palabras y dominios bloqueados.
- Comprobacion de subdominios.
- Aplicacion al formulario de respuestas.
- Listas locales de demostracion.

## 3. Incidencias resueltas

- Uso del interprete correcto del entorno virtual.
- Correccion de indentacion y archivos de tests sin guardar.
- Recuperacion del modelo ThreadVote y regeneracion de una migracion
  no aplicada que proponia eliminarlo.
- Creacion de la configuracion local SECRET_KEY en .env.
- Correccion de rutas de votacion.
- Sustitucion del entorno Django 4.2 con Python 3.14 por un entorno
  separado con Django 5.2.18.
- Configuracion de Channels y Daphne.
- Asignacion de permisos de moderacion.
- Exclusion de .env y copias .bak del control de versiones.

## 4. Verificacion realizada

- Suite completa: 66 tests ejecutados, resultado OK.
- Comprobaciones de Django sin incidencias.
- Sin cambios de modelos pendientes de migracion.
- Dependencias sin conflictos segun pip check.
- Pruebas manuales de votaciones, avisos en tiempo real, reportes,
  revision de reportes, bloqueo, ocultacion y restauracion.
- Suspension comprobada: voto rechazado durante la suspension y
  aceptado despues de levantarla.
- Fusion comprobada mediante tests; prueba manual pendiente.

Los mensajes HTTP 400, 403, 404 y 405 generados deliberadamente por los
tests verifican rechazos esperados y no representan fallos de la suite.

## 5. Pendientes propios de la parte 4

- Probar manualmente la fusion desde el navegador.
- Sustituir las listas de demostracion por reglas acordadas por el equipo.
- Aplicar filtros a futuros formularios de creacion y edicion de hilos.
- Ampliar las pruebas de WebSockets para cubrir middleware de sesion,
  validacion de origen y publicacion despues de confirmar transacciones.
- Revisar permisos y acciones del administrador mediante tests especificos.
- Revisar menciones con puntuacion y contenido Markdown.
- Configurar Redis si se despliega con varios procesos.
- Revisar la configuracion ASGI y de canales para produccion.

La capa en memoria actual sirve para desarrollo en un unico proceso.
Los filtros por listas no garantizan que todos los enlaces sean seguros.

## 6. Dependencias de otros modulos

### Solucion aceptada
Los avisos por votos se aplican actualmente a cualquier respuesta.
Para distinguir el aviso "han votado tu solucion" falta implementar la
solucion aceptada, prevista en el modulo de estructura de contenidos.
No depende exclusivamente de la parte 5.

### Integracion del editor
El formulario nuevo de respuestas usa texto y no integra todavia todas
las funciones del editor de Raquel. Esa integracion corresponde al
trabajo conjunto con el modulo de editor.

### Parte 5: Busqueda y descubrimiento
Falta incorporar y comprobar en busquedas y feeds:
- Exclusion de hilos y respuestas eliminados.
- Exclusion de hilos originales ya fusionados.
- Filtros por autor, fecha, etiquetas, votos y estado resuelto.
- Busqueda de texto completo y autocompletado.
- Feeds de nuevos, populares, sin respuesta y siguiendo.

Estas tareas requieren las vistas y estructuras de la parte 5.
Etiquetas, solucion aceptada y seguimiento necesitan sus propias bases
antes de poder ofrecer todos los filtros y feeds.

## 7. Estado del trabajo

Parte 4 implementada y probada para desarrollo local, con las
limitaciones y pendientes anteriores. No se considera terminada
la preparacion para produccion ni la integracion con todos los modulos.

Se puede comenzar la parte 5 manteniendo este listado de pendientes.
