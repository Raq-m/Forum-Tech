# Sesión 8: API REST de Forum Tech

Fecha: 26/10/2026. Material de referencia: `11202_PR07_Sesión 8.pdf`.

La sesión de Tech2Hand se adapta al foro: la web HTML y la nueva API JSON
trabajan con los mismos modelos, usuarios y PostgreSQL. La API está versionada
en `/api/v1/`. No requiere migraciones ni crea otra base de datos de aplicación.

## 1. Adaptación del material

| Tech2Hand | Forum Tech |
| --- | --- |
| Producto, vendedor | Hilo, autor |
| Categorías y marcas de solo lectura | Etiquetas de solo lectura |
| Precio mínimo y máximo | Puntuación y visitas mínimas y máximas |
| Favoritos privados y acción `favorite` | Votos propios privados y acción `vote` |
| Productos populares | Hasta 20 hilos por puntuación y visitas |
| Mis productos | Mis hilos (`mine`) |
| Productos de la misma categoría | Hilos con alguna etiqueta en común (`similar`) |
| Estadísticas de productos | Resumen de hilos, respuestas y visitas de la sesión 7 |

Las imágenes de productos, marcas, precios y favoritos de productos no pertenecen
al modelo del foro. No se añaden esas entidades. Un voto positivo no es un
favorito: se conserva el voto existente con valores `1`, `-1` y retirada con `0`.

## 2. Instalación y arranque

Desde la raíz del proyecto:

```bash
source .venv312/bin/activate
python -m pip install -r requirements.txt
python manage.py check
python manage.py runserver
```

Si el entorno no tiene pip, primero ejecuta `python -m ensurepip`.
PostgreSQL debe estar arrancado como se explica en `sesion_7.md`.

Se incorporan `djangorestframework`, `django-filter`, `drf-spectacular` y
`drf-spectacular-sidecar`. Este último sirve Swagger y ReDoc con recursos locales,
sin depender de un CDN. No se necesita el lector de PDF para ejecutar la app.

## 3. Archivos y arquitectura

```text
Web HTML ──┐
           ├── servicios / ORM ── PostgreSQL
API JSON ──┘
```

- `api/serializers.py`: representación pública, campos anidados y validación.
- `api/permissions.py`: autenticación, autoría y suspensiones.
- `api/filters.py`: filtros declarativos con django-filter.
- `api/views.py`: APIView, ListAPIView y ViewSets.
- `api/urls.py`: DefaultRouter y rutas especiales.
- `api/tests/test_threads.py`: pruebas con APITestCase.
- `config/settings/base.py`: apps, sesión, paginación, filtros y OpenAPI.
- `config/urls.py`: montaje de la API, login y documentación.
- `forum/services.py`: voto compartido por web/API y archivo lógico existente.
- `forum/views.py`: usa el servicio compartido para los votos de hilos.

`ModelSerializer` convierte modelos a JSON y valida los datos recibidos.
`ModelViewSet` implementa listar, crear, consultar, PUT, PATCH y DELETE.
`ReadOnlyModelViewSet` permite solo listar y consultar. El router genera sus rutas.
`APIView` ofrece control explícito para saludo y estadísticas; `ListAPIView`
reutiliza listado y paginación para populares.

## 4. Endpoints

| Método | Ruta | Acceso y efecto |
| --- | --- | --- |
| GET | `/api/v1/` | Índice público de recursos |
| GET | `/api/v1/hello/` | Saludo público |
| GET | `/api/v1/threads/` | Hilos visibles paginados |
| POST | `/api/v1/threads/` | Cuenta autenticada no suspendida; crea hilo |
| GET | `/api/v1/threads/{id}/` | Detalle público |
| PUT / PATCH | `/api/v1/threads/{id}/` | Solo autor no suspendido |
| DELETE | `/api/v1/threads/{id}/` | Solo autor no suspendido; borrado lógico |
| POST | `/api/v1/threads/{id}/vote/` | Cuenta no suspendida; establece o retira su voto |
| GET | `/api/v1/threads/mine/` | Hilos visibles del usuario autenticado |
| GET | `/api/v1/threads/{id}/similar/` | Hilos visibles con etiquetas compartidas |
| GET | `/api/v1/threads/popular/` | Los primeros 20 por puntuación y visitas, paginados |
| GET | `/api/v1/tags/` | Etiquetas públicas de solo lectura |
| GET | `/api/v1/tags/{id}/` | Detalle de etiqueta |
| GET | `/api/v1/votes/` | Solo votos del usuario autenticado sobre hilos visibles |
| GET | `/api/v1/votes/{id}/` | Solo un voto propio sobre un hilo visible |
| GET | `/api/v1/stats/` | Resumen de hilos visibles |
| GET | `/api/schema/` | Esquema OpenAPI |
| GET | `/api/docs/` | Swagger interactivo |
| GET | `/api/redoc/` | ReDoc |

Las respuestas del foro siguen publicándose mediante su formulario web. Esta
sesión expone el CRUD del recurso principal (hilos), no todos los modelos del foro.

## 5. Probar con tu cuenta en el navegador

1. Abre <http://127.0.0.1:8000/api/v1/threads/>.
2. Pulsa **Log in** y usa tu cuenta existente. También puedes entrar en
   <http://127.0.0.1:8000/api/auth/login/>. Si ya has iniciado sesión en la web
   con el mismo host, la API reconoce esa sesión.
3. En el formulario de creación, o en **Raw data** con `application/json`, envía:

   ```json
   {
     "title": "Prueba de la API de la sesión 8",
     "content": "He creado este hilo desde la API REST.",
     "tags": []
   }
   ```

4. Debe responder **201 Created**, con tu usuario como `author`. El hilo también
   aparece en la web <http://127.0.0.1:8000/forum/threads/>.
5. Abre `/api/v1/threads/ID/` usando el ID recibido. Puedes modificarlo con PUT o
   PATCH; por ejemplo `{"title": "Título actualizado"}` con PATCH en Swagger.
6. En `/api/v1/threads/ID/vote/`, envía `{"value": 1}`, después `{"value": -1}`
   y finalmente `{"value": 0}`. Responde con `score` y `user_vote`. Repetir el
   mismo voto no crea duplicados; `0` elimina el voto.
7. Consulta `/api/v1/votes/` y `/api/v1/threads/mine/`: son listas privadas.
8. Con otra cuenta, intenta modificar ese hilo: debe responder **403**.
9. Si eliminas el hilo de práctica con DELETE, responde **204** y deja de salir
   tanto en la API como en la web; sus respuestas se conservan en la base.

Son operaciones reales sobre tus datos locales. Usa un hilo de práctica.
Swagger en <http://127.0.0.1:8000/api/docs/> permite elegir el endpoint,
pulsar **Try it out**, introducir el JSON y ejecutar. Inicia sesión antes en la
API navegable; Swagger usa la cookie de sesión y envía el token CSRF.

## 6. Filtros, búsqueda, orden y paginación

Los listados usan páginas de 12 y devuelven `count`, `next`, `previous` y `results`.
Ejemplos:

```text
/api/v1/threads/?page=2
/api/v1/threads/?search=django
/api/v1/threads/?tag=python
/api/v1/threads/?author=ana
/api/v1/threads/?resolved=true
/api/v1/threads/?is_locked=false
/api/v1/threads/?min_votes=1&max_votes=10
/api/v1/threads/?min_views=5&max_views=100
/api/v1/threads/?ordering=-puntuacion
/api/v1/threads/?search=django&min_votes=1&ordering=-views_count
```

`search` consulta título, contenido del hilo y nombre de etiquetas. La búsqueda
web sigue teniendo su comportamiento anterior, que también consulta respuestas.
Los órdenes permitidos son `created_at`, `views_count`, `puntuacion` y
`num_respuestas`, con `-` para descendente. El orden predeterminado es más
recientes primero, con desempate por ID.

Desde otra terminal:

```bash
curl -H 'Accept: application/json' \
  'http://127.0.0.1:8000/api/v1/threads/?search=django&min_votes=1&ordering=-views_count'
```

La respuesta depende de tus hilos y votos actuales. Si no hay coincidencias,
`count` vale `0` y `results` es `[]`; no es un fallo.

## 7. Seguridad y reglas compartidas

- La identidad procede de `request.user`. El cliente no puede asignar otro autor.
- El autor público contiene solo `id` y `username`; no expone email, teléfono,
  contraseña, suspensión ni privilegios.
- Visitas, bloqueo, solución aceptada y fechas son de solo lectura. Las acciones
  de moderación y aceptación de solución mantienen sus vías existentes.
- Los hilos eliminados o fusionados se excluyen del detalle, listas, similares,
  populares y votos privados. Los votos ajenos responden 404.
- DELETE reutiliza `archive_thread()`, con bloqueo y borrado lógico.
- Web y API usan `record_thread_vote()` para los votos de hilos. El bloqueo de
  fila coordina votos con archivo y fusión; la transacción evita cambios parciales.
- Crear y actualizar hilos utiliza transacciones; se mantienen las señales de
  menciones y las notificaciones posteriores al commit.
- Se reutiliza `validate_forum_content()` para título y contenido. Los campos
  vacíos y las etiquetas inexistentes devuelven 400.
- La autenticación usa la sesión Django y exige CSRF en escrituras autenticadas.
  Con esta configuración, una escritura anónima responde 403. JWT y CORS para
  clientes separados quedan fuera de esta sesión, como en el material.
- GET de detalle en la API no incrementa visitas: el contador de la sesión 7
  continúa contando solicitudes al detalle web.

Los querysets reutilizan `hilos_visibles()`, las subconsultas de puntuación y
respuestas, `select_related("author")` y `prefetch_related("tags")`. Así no se
multiplican votos al unir etiquetas y respuestas ni se consulta el autor por fila.

## 8. Verificación ejecutada

```bash
python manage.py check
python manage.py test api --settings=config.settings.testing --noinput
python manage.py test --settings=config.settings.testing_postgresql --noinput
python manage.py test --settings=config.settings.testing --noinput
python manage.py makemigrations --check --dry-run --settings=config.settings.testing
python manage.py spectacular --file /tmp/forum-openapi.yaml --validate --fail-on-warn
```

Resultados del 26/10/2026:

- API: 21 pruebas correctas.
- Suite PostgreSQL: 123 pruebas correctas, incluida la concurrencia de sesión 7.
- Suite SQLite: 123 descubiertas, 122 correctas y una omitida por requerir bloqueos.
- Sin cambios de modelos pendientes.
- Esquema OpenAPI válido, sin advertencias.

Las pruebas cubren CRUD, autor impuesto por servidor, campos protegidos, datos
públicos, borrado lógico, visibilidad, suspensiones, validación, votos privados,
filtros, orden, paginación, etiquetas de solo lectura, ejercicios, documentación
y una sesión real con CSRF. Se ejecutan en una base de prueba separada.

## 9. Conceptos para explicar la práctica

REST organiza la API en recursos y métodos HTTP. GET consulta, POST crea o ejecuta
una acción, PUT sustituye los campos editables, PATCH modifica parcialmente y
DELETE archiva el recurso. JSON es el formato de intercambio. Los códigos
principales son 200 (lectura o modificación), 201 (creación), 204 (borrado sin
cuerpo), 400 (datos inválidos), 403 (sin permiso) y 404 (no visible o inexistente).

Autenticación identifica al usuario; los permisos deciden qué puede hacer.
Los permisos de objeto protegen un hilo concreto; los querysets limitan lo que
aparece en las listas. OpenAPI describe la API y Swagger/ReDoc permiten explorar
esa descripción. La interfaz HTML y la API comparten servicios y base de datos.

Referencia de implementación: documentación oficial de DRF
<https://www.django-rest-framework.org/tutorial/quickstart/> y permisos
<https://www.django-rest-framework.org/api-guide/permissions/>.

## 10. Revisión contra el PDF original

Se ha cotejado la implementación con los contenidos y ejercicios del PDF de
85 páginas. Esta tabla registra sus equivalencias para el foro:

| Apartados del PDF | Implementación y evidencia |
| --- | --- |
| 8–13: dependencias, settings y app | Dependencias registradas en requirements; apps DRF, filtros y OpenAPI; app `api` |
| 14–25: serializers, relaciones y validación | `PublicUserSerializer`, `TagSerializer`, `ThreadSerializer` y `ThreadVoteSerializer`; campos protegidos y filtros de contenido |
| 26–28: APIView y ViewSet | `HelloAPIView`, `StatsAPIView` y `ThreadViewSet` |
| 29–34: permiso de propietario y autor del servidor | `IsActiveAuthorOrReadOnly`; autor asignado en `perform_create`; pruebas de PATCH/DELETE de terceros y suplantación de autor |
| 35–41: catálogos de lectura y router | `TagViewSet`, `DefaultRouter`, índice y CRUD de hilos |
| 42–50: paginación, búsqueda, filtros y orden | Páginas de 12, SearchFilter, OrderingFilter y `ThreadFilter` con rangos de votos/visitas |
| 51–55: colección privada y acción personalizada | `ThreadVoteViewSet` filtra por usuario; acción `vote` con serializer específico y permisos de cuenta activa |
| 56–59: vista genérica y populares | `PopularThreadsAPIView`, máximo 20 hilos visibles por puntuación y visitas; prueba de ambas páginas |
| 60–61: sesión y permisos | Sesión Django existente, comprobación CSRF real, autoría y suspensión |
| 62–75 y 94: APITestCase y cobertura | 21 pruebas de API; suite conjunta con PostgreSQL y SQLite |
| 76–83: OpenAPI, Swagger y ReDoc | Esquema validado sin advertencias; recursos Swagger/ReDoc locales |
| 84–90: curl y dominio compartido | Ejemplo del apartado 6, servicio compartido de voto y archivo; mismos modelos y base que la web |
| 91–93: alcance y versión | Prefijo `/api/v1/`; JWT, refresh y CORS para clientes separados se posponen como en el PDF |
| 97: mis productos | `GET /api/v1/threads/mine/`, paginado y limitado al autor autenticado |
| 98: similares | `GET /api/v1/threads/{id}/similar/`, etiquetas comunes, sin el propio hilo ni duplicados |
| 99: estadísticas | `GET /api/v1/stats/`, reutiliza `resumen_foro()` con Count, Avg, Min y Max |
| 100: PATCH por tercero y propietario | Pruebas de 403 para tercero y 200 para autor |
| 101: consulta combinada y diario | Ejecución real documentada a continuación |

Se conservan las adaptaciones del apartado 1: no hay marcas, precios ni imágenes
de productos en el foro, y los votos no se presentan como favoritos. El resumen
de estadísticas usa los indicadores de la sesión 7; no incorpora precios ni un
recuento de cuentas ajeno a las estadísticas públicas actuales.

### Fallos corregidos durante la revisión

1. Las respuestas POST/PUT/PATCH podían omitir `puntuacion`, `num_respuestas` y
   `esta_resuelto` porque el objeto recién guardado no tenía las anotaciones del
   queryset de lectura. Ahora se vuelve a consultar dentro de la transacción y
   se devuelve el hilo con sus estadísticas actuales.
2. La acción de voto tenía una descripción OpenAPI correcta, pero su formulario
   navegable y sus metadatos OPTIONS utilizaban `ThreadSerializer`. Ahora la
   propia acción configura `VoteInputSerializer`, de modo que muestra `value`
   con las opciones `-1`, `0` y `1`.

Las dos regresiones se reprodujeron antes de corregirlas. Las cuatro pruebas
nuevas verifican las respuestas completas después de guardar, el formulario de
voto, el límite/paginación de populares y los similares sin duplicados junto con
la privacidad del filtro de mis hilos. El esquema OpenAPI vuelve a validarse sin
advertencias tras los cambios.

### Diario del ejercicio 101, adaptado al foro

Consulta ejecutada el 26/10/2026, respuesta HTTP 200:

```text
GET /api/v1/threads/?search=django&min_votes=1&ordering=-views_count
```

Extracto de la respuesta real, mostrando solo los campos relevantes:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Duda con Django y las vistas",
      "puntuacion": 2,
      "views_count": 0
    }
  ]
}
```

La búsqueda y el mínimo de votos se aplican juntos y el orden es por visitas
descendentes. Esta ejecución con una coincidencia acredita la combinación de
parámetros; las pruebas con varios hilos comprueban la ordenación. Los resultados
cambian al crear, votar, visitar o archivar hilos.
