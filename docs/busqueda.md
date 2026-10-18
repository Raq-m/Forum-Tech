# Búsqueda y descubrimiento (módulo 5)

Página principal del foro: `/forum/threads/`. Todo se calcula en el servidor y respeta las reglas de la parte 4.

## Qué incluye

- **Feeds** (pestañas): Nuevos, Populares, Sin respuesta y Siguiendo (este último exige sesión iniciada)
- **Búsqueda de texto**: cada palabra debe aparecer en el título, el contenido o una respuesta visible
- **Filtros**: autor, etiquetas, rango de fechas, votos mínimos y estado (resuelto o sin resolver). Se combinan entre sí y con cualquier pestaña
- **Autocompletado**: sugerencias de títulos mientras se escribe (`/forum/threads/suggest/?q=...`)
- **Etiquetas** (`#python`), **solución aceptada** (solo la acepta el autor del hilo; sube al inicio) y **seguir usuarios**
- Paginación de 10 hilos por página

## Reglas que se respetan

- Se excluyen los hilos ocultos (`is_deleted`) y los fusionados (`merged_into`)
- Se excluyen las respuestas ocultas, tanto de los resultados como del recuento de respuestas
- La solución aceptada deja de contar como tal si la respuesta se oculta
- Seguir y aceptar solución respetan las suspensiones temporales
- Votos y respuestas se calculan con subconsultas, para que no se multipliquen las filas

## Archivos

- `forum/search.py`: consultas (`hilos_visibles`, `buscar_hilos` y los feeds)
- `forum/views_busqueda.py`: la página de hilos y las sugerencias
- `forum/views_social.py`: aceptar solución y seguir o dejar de seguir
- `forum/solucion.py`: regla de quién puede aceptar una solución
- `forum/models.py` y migración `0009`: `Tag`, `UserFollow`, `Thread.tags` y `Thread.accepted_reply`
- `templates/forum/thread_list.html` y `thread_detail.html`
- `forum/templatetags/forum_extras.py`: ayuda para saber si se sigue a un autor

## Cómo probarlo

```
python manage.py datos_demo --usuario TU_USUARIO
python manage.py runserver
python manage.py test
```

`datos_demo` crea usuarios con contraseña conocida (`demo-1234`): es solo para desarrollo y nunca debe ejecutarse en un servidor real.

## Pendiente

| Qué falta | Módulo |
|---|---|
| Formulario de creación y edición de hilos con campo de etiquetas (usar `Tag.desde_texto`) | Módulo 2: Estructura de contenidos y navegación |
| Usar el editor del módulo 3 al crear hilos y respuestas | Módulo 2 y módulo 3 |
| Mostrar seguidores y a quién se sigue en el perfil | Módulo 1: Usuarios y perfiles |
| Búsqueda de texto completo con ranking de relevancia y tolerancia a erratas | Módulo 6: Arquitectura técnica (PostgreSQL, Meilisearch o Elasticsearch) |
| Autocompletado de etiquetas | Módulo 5 (mejora opcional) |