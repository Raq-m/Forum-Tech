# Sesión 7: PostgreSQL, integridad, ORM y transacciones en Forum Tech

Fecha: 25/10/2026. Material: `11202_PR07_Sesión 7.pdf`.

El PDF utiliza Tech2Hand (productos, precios y reservas). Esta implementación
aplica la sesión completa al dominio de Forum Tech. El apartado numerado 7 del
PDF trata únicamente la instalación de PostgreSQL; aquí se desarrollan también
los contenidos siguientes de la sesión.

## 1. Qué cambia y por qué

Antes: navegador → Django → SQLite (`db.sqlite3`).
Ahora en desarrollo: navegador → Django ORM → psycopg → PostgreSQL.

PostgreSQL es un servidor. Django necesita dirección, puerto, usuario, contraseña
y nombre de base para conectarse. El driver `psycopg` transporta las consultas.
SQLite sigue disponible para comparar resultados y ejecutar pruebas rápidas.

| Ejemplo del PDF | Aplicación en Forum Tech |
| --- | --- |
| Producto | Hilo (`Thread`) |
| Vendedor | Autor (`author`) |
| Categoría | Etiqueta (`Tag`), relación de muchos a muchos |
| Precio positivo | Valor de voto obligatoriamente `-1` o `1` |
| Favorito único | Voto único por usuario y publicación; seguimiento único |
| Reserva concurrente | Fusión concurrente de hilos |
| Archivar producto del vendedor | `archive_thread(thread_id, user)` |
| Precio medio por categoría | Visitas medias por etiqueta |

No se añaden productos ni precios al foro. Se conservan las reglas de votos,
reportes, borrado lógico, soluciones aceptadas y seguimiento existentes.

## 2. Entorno preparado en este equipo (macOS)

Se ha utilizado PostgreSQL **17.10**, ya instalado en `/opt/homebrew/bin`.
El PDF incluye pasos para Windows; aquí se usan los ejecutables de macOS.

La sesión ha dejado:

- Python 3.12.15 en `.local/python/` y entorno virtual `.venv312/`.
- Django 5.2.18 y dependencias de `requirements.txt`.
- Clúster PostgreSQL en `.local/postgresql/`.
- Servidor escuchando en `127.0.0.1:55432` (puerto propio para esta práctica).
- Base `forumtech`, cuyo propietario es el rol `forumtech`.
- Rol de aplicación sin privilegios de superusuario; tiene `CREATEDB` para tests locales.
- `.env` con secretos aleatorios, permisos privados y exclusión de Git.

Estas carpetas son locales y no se incluyen en el código compartido. El clúster
es persistente, pero el proceso debe arrancarse de nuevo tras reiniciar el Mac.

```bash
source .venv312/bin/activate
/opt/homebrew/bin/psql --version
/opt/homebrew/bin/pg_ctl -D "$PWD/.local/postgresql" status
```

Si está detenido:

```bash
/opt/homebrew/bin/pg_ctl -D "$PWD/.local/postgresql" \
  -l "$PWD/.local/postgresql.log" \
  -o '-p 55432 -k /tmp -h 127.0.0.1' start
```

Para detener solamente esta instancia:

```bash
/opt/homebrew/bin/pg_ctl -D "$PWD/.local/postgresql" stop -m fast
```

## 3. Cómo reproducir la instalación en otro equipo

Instala Python 3.12 y PostgreSQL, activa un entorno y ejecuta:

```bash
python3.12 -m venv .venv312
source .venv312/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Con un administrador de PostgreSQL crea un rol dedicado. `\password` pide la
contraseña sin dejarla en el historial del comando SQL:

```sql
CREATE ROLE forumtech LOGIN;
\password forumtech
CREATE DATABASE forumtech OWNER forumtech;
-- Solo en el entorno de pruebas local:
ALTER ROLE forumtech CREATEDB;
```

Completa `.env` con una clave Django aleatoria y las credenciales elegidas.
El puerto de la plantilla es `5432`; en este equipo es `55432`.

```dotenv
SECRET_KEY=<clave aleatoria>
DB_ENGINE=postgresql
POSTGRES_DB=forumtech
POSTGRES_USER=forumtech
POSTGRES_PASSWORD=<tu contraseña>
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

`config/settings/postgresql.py` construye la conexión y detecta credenciales
vacías. `development.py` la utiliza por defecto. No se han modificado las
opciones de despliegue de `production.py`.

`base.py` conserva SQLite. `testing.py` permite probar con SQLite y
`testing_postgresql.py` selecciona PostgreSQL explícitamente.

## 4. Migraciones: estructura y datos son cosas diferentes

```bash
python manage.py check
python manage.py migrate
python manage.py showmigrations forum
```

`check` revisa la configuración; por sí solo no garantiza que el servidor sea
accesible. `migrate` sí necesita conectarse y crea las tablas.

La migración `0010` añade visitas, un índice compuesto y restricciones de voto.
Las migraciones anteriores crean usuarios, hilos, respuestas, reportes, etc.
Todas se han aplicado a la nueva base PostgreSQL.

No había un archivo `db.sqlite3` en la copia recibida. No hubo datos antiguos
que trasladar. Cambiar de motor no mueve datos automáticamente: una copia del
archivo SQLite y una exportación deben hacerse antes si se trabaja con otra copia
que sí contenga datos. No se debe interpretar una base nueva vacía como pérdida
de la base anterior.

Si una base antigua contiene votos distintos de `-1` y `1`, la nueva restricción
fallará al migrar. Hay que revisar esos registros y decidir su corrección antes
de continuar; la migración no los elimina silenciosamente.

## 5. Integridad: formulario y base de datos

En `forum/models.py` hay dos nuevas reglas `CheckConstraint`:

```python
models.CheckConstraint(
    condition=models.Q(value__in=[-1, 1]),
    name="thread_vote_value_valid",
)
```

También existe la equivalente para `ReplyVote`.

El campo `choices` ayuda a validar formularios. La restricción SQL evita que
un script, `objects.create()` o `update()` guarde un valor inválido saltándose
el formulario. La base lanza `IntegrityError`.

Un voto `0` en la petición HTTP sigue significando **retirar el voto**: la vista
elimina el registro. No se guarda una fila de voto con valor cero.

Se mantienen las restricciones únicas existentes: un voto por usuario y objeto,
un seguimiento por pareja y un reporte por usuario y publicación. Las claves
foráneas garantizan que las relaciones apunten a filas existentes.

## 6. Índices: ayudar a localizar y ordenar

El índice nuevo es:

```python
models.Index(
    fields=["is_deleted", "-created_at"],
    name="thread_visible_date_idx",
)
```

El listado filtra hilos no eliminados y ordena por fecha descendente; este índice
combina ambas columnas. Las claves foráneas ya tienen índices generados por Django.
No se crean índices sobre cada columna indiscriminadamente: ocupan espacio y
encarecen escrituras.

El planificador decide si usa un índice. Con pocos hilos puede elegir recorrer
la tabla (`Seq Scan`), algo perfectamente razonable.

## 7. ORM avanzado y estadísticas

Abre el shell:

```bash
python manage.py shell
```

```python
from forum.statistics import (
    resumen_foro, etiquetas_populares,
    hilos_populares, media_visitas_por_etiqueta,
)
resumen_foro()
list(etiquetas_populares().values("name", "num_hilos"))
list(hilos_populares().values("title", "puntuacion"))
list(media_visitas_por_etiqueta())
```

`aggregate()` devuelve un resumen global: total de hilos, media de respuestas,
visitas mínimas y máximas. `annotate()` añade un cálculo a cada fila: por ejemplo,
el número de hilos visibles de cada etiqueta.

`Count`, `Avg`, `Min` y `Max` son cálculos ejecutados por la base.
`values()` devuelve diccionarios de columnas y `values_list()` devuelve valores:

```python
from forum.search import hilos_visibles
list(hilos_visibles().values("id", "title")[:5])
list(hilos_visibles().values_list("id", flat=True)[:5])
```

Las consultas de `forum/search.py` ya calculaban puntuación y respuestas mediante
subconsultas. Se conservan: sumar votos uniendo a la vez votos, etiquetas y
respuestas puede multiplicar filas y producir resultados incorrectos.
Las estadísticas cuentan solo hilos visibles; las respuestas eliminadas tampoco
se incluyen en sus recuentos.

`Q()` permite combinar condiciones con OR (`|`), AND (`&`) y negación (`~`):

```python
from django.db.models import Q
hilos_visibles().filter(Q(title__icontains="python") | Q(content__icontains="django"))
```

## 8. Evitar N+1: no preguntar lo mismo una vez por fila

Si cargas diez hilos y consultas su autor por separado, puedes ejecutar una
consulta inicial más diez para los autores.

`select_related("author")` carga el autor mediante un JOIN: adecuado para
`ForeignKey` y `OneToOne`. `prefetch_related("tags")` precarga las etiquetas en
otra consulta: adecuado para relaciones múltiples.

El listado ya utiliza ambas técnicas. El detalle utiliza `Prefetch` con un
queryset de respuestas que carga sus autores y calcula votos. Se ha añadido una
prueba que comprueba que acceder a autores y etiquetas de varios hilos requiere
**dos consultas**, independientemente del número de hilos del conjunto.

Los querysets son perezosos: definirlos no suele ejecutar SQL; iterarlos sí.
Si solo quieres comprobar existencia, utiliza `.exists()`. Si solo quieres el
número, utiliza `.count()` sin cargar todos los objetos.

## 9. F(): incrementar visitas sin perder cambios concurrentes

El detalle de un hilo ahora suma una visita en SQL:

```python
Thread.objects.filter(pk=thread.pk).update(
    views_count=F("views_count") + 1,
)
```

Si dos peticiones llegan juntas, cada incremento se realiza sobre el valor
actual de la base. Leer primero en Python y guardar después podría pisar uno de
los incrementos. Se cuentan solicitudes al detalle, no visitantes únicos.
Los enlaces de hilos fusionados redirigen sin sumar visitas al origen.

## 10. Transacciones: todo o nada

`forum/services.py` ya contenía `merge_threads()` con `transaction.atomic`.
La fusión actualiza avisos, mueve respuestas y marca el origen como fusionado.
Si falla cualquier paso, se revierten todos: no quedan respuestas movidas con
avisos apuntando al lugar equivocado.

Se ha corregido además la referencia a solución aceptada del origen: se limpia
al mover sus respuestas, porque ya no pertenecen a ese hilo.

`update_fields` limita las columnas que escribe `save()`. `update()` permite
actualizar varias filas sin cargarlas, pero no llama a `save()` ni a sus señales.
Por eso se utiliza deliberadamente para mover respuestas sin generar avisos de
"nueva respuesta". Los eventos WebSocket existentes usan `on_commit`, de modo
que se envían después de confirmar los cambios.

`bulk_create()` permite insertar muchos objetos en bloque, pero tampoco ejecuta
`save()` ni las señales habituales. En este foro hay notificaciones basadas en
señales: no conviene sustituir las creaciones normales sin tratar esos efectos.

## 11. Bloqueos: dos operaciones al mismo tiempo

La fusión obtiene los dos hilos con `select_for_update()` dentro de una
transacción y ordena los bloqueos por clave primaria. El bloqueo dura hasta
commit o rollback. Otra operación que quiera bloquear la misma fila espera y
relee el estado actualizado. Después detecta que el origen ya está fusionado.

`reply_create()` ya bloqueaba el hilo al comprobar si admite respuestas.
`aceptar_solucion()` ahora también bloquea y relee el hilo, y comprueba en la base
que la respuesta siga perteneciendo a él: no confía en objetos Python obsoletos.

Esto coordina las operaciones que respetan el mismo protocolo de bloqueo. No
supone una garantía para cualquier escritura SQL externa o actualización masiva
que omita las comprobaciones de negocio.

## 12. Ejercicios del PDF resueltos para el foro

1. Cinco categorías con más productos → `etiquetas_populares()`.
2. Diez productos favoritos → `hilos_populares()`, por puntuación de votos.
3. Precio medio por categoría → `media_visitas_por_etiqueta()`.
4. Archivar solo si es el vendedor → `archive_thread(thread_id, user)`.
   Solo el autor autenticado y no suspendido puede archivar; un segundo intento
   se rechaza. Usa borrado lógico y bloqueo de fila; se practica desde el servicio.
5. Guardar `EXPLAIN` → comando `analizar_foro` y archivo de resultados.

Ejemplo para el ejercicio 4, en el shell y con un hilo de práctica:

```python
from forum.models import Thread
from forum.services import archive_thread
hilo = Thread.objects.filter(is_deleted=False, merged_into__isnull=True).first()
# Esta llamada modifica datos: oculta el hilo elegido.
# archive_thread(hilo.pk, hilo.author)
```

## 13. SQL y EXPLAIN: observar antes de optimizar

```bash
python manage.py analizar_foro
python manage.py analizar_foro > docs/sesion_7_explain.txt
```

Este comando solo consulta: muestra estadísticas, SQL generado y plan de
consulta. La salida guardada corresponde al pequeño conjunto de demostración;
no demuestra una mejora de rendimiento con grandes volúmenes. Repite la medición
cuando tengas más datos. No utiliza `EXPLAIN ANALYZE`, que ejecutaría la consulta.

Conexión manual (la contraseña está en tu `.env`):

```bash
/opt/homebrew/bin/psql -h 127.0.0.1 -p 55432 -U forumtech -d forumtech -W
```

Dentro de `psql`:

```sql
\dt
\d forum_thread
SELECT id, title, views_count FROM forum_thread ORDER BY created_at DESC;
SELECT COUNT(*) FROM forum_thread
WHERE NOT is_deleted AND merged_into_id IS NULL;
\q
```

## 14. Pruebas ejecutadas y qué demuestran

```bash
python manage.py test --settings=config.settings.testing_postgresql --noinput
python manage.py test --settings=config.settings.testing --noinput
python manage.py makemigrations --check --dry-run
```

La suite se mantiene modular por tema (`test_merge.py`, `test_votes.py`, etc.).
`forum/test_session7.py` añade las comprobaciones de esta sesión sin mover los
archivos anteriores ni alterar su forma de ejecución.

La primera ejecución de la sesión 7 descubrió 99 pruebas. La revisión contra el
PDF original del 26/10/2026 añade tres pruebas de estadísticas; con la sesión 8,
la suite conjunta, tras revisar también la sesión 8, contiene 123 pruebas
(resultados en el apartado 18).
- Valores de voto inválidos y duplicados rechazados por la base.
- Estadísticas correctas con varios votos, respuestas y etiquetas.
- Acceso a autores y etiquetas en dos consultas.
- Visitas del detalle y redirecciones de hilos fusionados.
- Archivo restringido al autor y rechazo de repetición.
- Solución rechazada cuando se recibe una respuesta obsoleta tras una fusión.
- Rollback de respuestas y avisos al simular un fallo al final de la fusión.
- Dos conexiones concurrentes intentando fusionar el mismo origen: solo una gana.

La prueba concurrente utiliza `TransactionTestCase`: permite commits reales y
conexiones independientes. Un `TestCase` ordinario envuelve cada prueba en una
transacción y no reproduce ese escenario de la misma manera.

## 15. Arrancar y probar en el navegador

```bash
source .venv312/bin/activate
python manage.py runserver
```

Abre `http://127.0.0.1:8000/forum/threads/` y entra en un hilo para ver las visitas.
Los datos de demostración se crean con `python manage.py datos_demo` y el comando
puede repetirse sin duplicar el conjunto. Los usuarios `demo_ana`, `demo_luis` y
`demo_marta` usan `demo-1234`, exclusivamente para la práctica local.

El administrador local preparado se llama `forum_admin`. Su contraseña aleatoria
está en `.local/admin-password.txt`; se puede cambiar sin mostrar la anterior:

```bash
python manage.py changepassword forum_admin
```

En otro equipo crea tu administrador con `python manage.py createsuperuser`.

## 16. Copias de seguridad

Con el servidor local arrancado:

```bash
/opt/homebrew/bin/pg_dump -h 127.0.0.1 -p 55432 -U forumtech -d forumtech -W \
  -f .local/forumtech_backup.sql
```

Para restaurar en una base vacía creada previamente (ejemplo `forumtech_restore`):

```bash
/opt/homebrew/bin/psql -h 127.0.0.1 -p 55432 -U forumtech -d forumtech_restore -W \
  -v ON_ERROR_STOP=1 -f .local/forumtech_backup.sql
```

Un backup puede contener datos personales y hashes de contraseñas; se guarda en
la carpeta local ignorada, no en documentación compartida.

## 17. Alcance de esta sesión

PostGIS y pgvector se mencionan como posibilidades futuras, igual que en el PDF.
La sesión termina con PostgreSQL, integridad, consultas, índices y transacciones.
La siguiente sesión del material aborda Django REST Framework.

## 18. Revisión contra el PDF original (26/10/2026)

Se han cotejado las 67 páginas del PDF aportado con la implementación, las
migraciones y la base local. Las instrucciones de Windows se adaptan a macOS;
los ejemplos de productos se traducen al dominio del foro de esta manera:

| Apartados del PDF | Evidencia en Forum Tech |
| --- | --- |
| 7–16: PostgreSQL, rol, base, driver y entorno | PostgreSQL 17.10, base y rol `forumtech`, psycopg, `.env.example` y `config/settings/postgresql.py` |
| 17–21: conexión, migraciones y administrador | Conexión real comprobada; cero migraciones pendientes; administrador `forum_admin` activo |
| 22–27: SQL, CHECK y UNIQUE | `analizar_foro`, restricciones de voto válido y voto/seguimiento único; pruebas de `IntegrityError` |
| 28–33: índices y migración | `thread_visible_date_idx` sobre `is_deleted ASC, created_at DESC`, confirmado en PostgreSQL; migración `0010` |
| 34–43 y 80–85: agregaciones y proyecciones | `forum/statistics.py`, anotaciones de `hilos_visibles()` y ejemplos de `values()`/`values_list()` del apartado 7 |
| 44–48: N+1, select/prefetch y Prefetch | Autor precargado, etiquetas precargadas y respuestas del detalle con `Prefetch`; prueba de dos consultas |
| 49–58: atomicidad, servicio y bloqueo | `merge_threads()` y `archive_thread()`; pruebas de rollback, rechazo de repetición y fusión concurrente |
| 59: F() | Incremento SQL de visitas en el detalle web; prueba de recargas y redirección |
| 60–65: lazy, exists, count, update y bulk_create | Explicaciones en apartados 8 y 10; `update()` en visitas/fusión; no se sustituyen las creaciones con señales por inserciones masivas |
| 66–68: EXPLAIN y medición | `analizar_foro` y `docs/sesion_7_explain.txt`; el plan con pocos datos no acredita una mejora a gran escala |
| 69–79: pruebas y organización | Módulos existentes por tema, `forum/test_session7.py` y ejecución con PostgreSQL |
| 86–92: consola SQL | Comandos psql, tablas, descripción y consultas del apartado 13 |
| 93–94: PostGIS y pgvector | Solo preparación conceptual; el PDF pospone su instalación |
| 95–96: secretos y backup | `.env` y `.local/` ignorados; instrucciones de copia y restauración del apartado 16 |
| 100: cinco categorías más pobladas | `etiquetas_populares()`, con prueba del límite de cinco y exclusión de hilos ocultos |
| 101: diez productos más guardados | `hilos_populares()`, adaptado a puntuación de votos; prueba del límite de diez y ausencia de multiplicación por relaciones |
| 102: media por categoría | `media_visitas_por_etiqueta()`, con prueba de dos hilos visibles, ocultos y grupos vacíos |
| 103: archivar solo si es el vendedor | `archive_thread(thread_id, user)`, solo autor no suspendido; pruebas de permisos y segundo intento |
| 104: guardar EXPLAIN | Resultado guardado y comando reproducible en el apartado 13 |

El foro no tiene precios, marcas, reservas de compra ni categorías con una única
clave foránea. Por ello no se copian los índices `price` o `status/category`:
las etiquetas son una relación muchos a muchos con sus propios índices, y el
índice compuesto se aplica al filtro y orden reales de los hilos. Tampoco se
introduce una reserva artificial: la fusión permite practicar el mismo bloqueo
y rechazo de una segunda operación sobre un origen ya procesado.

La organización de pruebas ya era modular por funcionalidad. Se conserva esa
estructura en lugar de mover todos los archivos a `forum/tests/`, lo cual no
cambiaría las garantías comprobadas.

### Correcciones de esta revisión

- La consulta SQL de recuento del apartado 13 excluye también los hilos
  fusionados, igual que `hilos_visibles()`.
- Se añaden tres pruebas para los rankings y las medias de los ejercicios
  100–102, incluyendo hilos eliminados/fusionados y etiquetas sin hilos visibles.
- Se distingue la ejecución inicial de 99 pruebas del total actual conjunto de
  las sesiones 7 y 8.

Resultado conjunto tras revisar también la sesión 8: **123 pruebas correctas con
PostgreSQL**. Con SQLite, 123 descubiertas, 122 correctas y una omitida por
requerir bloqueo de filas.
No hay cambios de modelos pendientes. La conexión, el rol sin superusuario,
las migraciones, el índice compuesto y las dos restricciones CHECK se han
verificado directamente en PostgreSQL.

Se ha verificado además una copia con `pg_dump --format=custom` y su restauración
con `pg_restore --exit-on-error --no-owner --no-privileges` en una base temporal
independiente. Las 19 tablas restauradas tienen los mismos recuentos que la
instantánea de origen. La copia se conserva en
`.local/backups/sesion7_7972b8a4220d406a8e4c71273eefd055.dump`, con permisos
privados y fuera de Git. La base temporal se eliminó al terminar; la base de
trabajo no se ha reemplazado. Los comandos del apartado 16 usan el formato SQL
de texto; una copia de formato custom se restaura con `pg_restore`, no con psql.
La comparación de EXPLAIN con grandes volúmenes sigue siendo un ejercicio para
cuando exista ese conjunto de datos, tal como indica el PDF.
