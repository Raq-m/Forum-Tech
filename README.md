# Forum-Tech

**Foro de desarrollo tecnológico creado con Python y Django.**

Forum-Tech es una aplicación web que permite compartir conocimientos, publicar preguntas, responder a otros usuarios y participar en una comunidad de aprendizaje sobre programación y tecnología.

Este documento explica cómo descargar, instalar, configurar y ejecutar el proyecto.

---

# 1. Características principales

- Registro e inicio de sesión de usuarios.
- Creación y publicación de hilos.
- Respuestas a publicaciones.
- Votación de hilos y respuestas.
- Aceptación de respuestas como solución.
- Seguimiento de usuarios.
- Sistema de notificaciones.
- Denuncia de publicaciones y respuestas.
- Etiquetas para clasificar contenidos.
- API REST.
- Documentación de API con Swagger y ReDoc.
- Panel de administración de Django.

# 2. Requisitos previos

Antes de comenzar, necesitas tener instaladas las siguientes herramientas:

| Herramienta | Versión utilizada o recomendada |
|---|---|
| Python | 3.12 |
| Git | Versión estable |
| pip | Incluido con Python |
| Visual Studio Code | Recomendado |

## 2.1. Python

Descarga Python desde su página oficial:

https://www.python.org/downloads/

Se recomienda Python 3.12.

En Windows, durante la instalación, activa la opción `Add Python to PATH`.

Comprueba la instalación:

**Windows:**

```powershell
py --version
```

**macOS y Linux:**

```bash
python3 --version
```

## 2.2. Git

Descarga Git desde:

https://git-scm.com/downloads

Comprueba la instalación:

```bash
git --version
```

## 2.3. Visual Studio Code

Descarga Visual Studio Code desde:

https://code.visualstudio.com/

Es el editor recomendado para trabajar con el proyecto.

# 3. Descargar el proyecto

Abre una terminal y ejecuta:

```bash
git clone https://github.com/malena1688/Forum-Tech.git
```

Entra en la carpeta del proyecto:

```bash
cd Forum-Tech
```

Para abrirlo en Visual Studio Code:

```bash
code .
```

Si el comando anterior no está disponible, abre Visual Studio Code y selecciona la carpeta `Forum-Tech` desde el menú Archivo.

# 4. Crear un entorno virtual

El entorno virtual permite instalar las dependencias del proyecto de forma aislada.

**Windows (PowerShell):**

```powershell
py -3.12 -m venv .venv
```

Activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación, puedes permitirla temporalmente en la sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después vuelve a ejecutar el comando de activación.

**Windows (CMD):**

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

**macOS y Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Cuando el entorno virtual esté activado, aparecerá `(.venv)` al principio de la línea de comandos.

# 5. Instalar las dependencias

**IMPORTANTE: Este paso es obligatorio antes de ejecutar Forum-Tech.**

El proyecto incluye un archivo `requirements.txt` que contiene las librerías necesarias y sus versiones.

Con el entorno virtual activado, actualiza pip:

```bash
python -m pip install --upgrade pip
```

Instala todas las dependencias:

```bash
python -m pip install -r requirements.txt
```

Espera a que termine la instalación antes de continuar.

# 6. Configurar la base de datos SQLite

Forum-Tech permite utilizar SQLite para realizar una instalación local y probar la aplicación.

SQLite no necesita instalar un servidor de base de datos independiente.

El proyecto selecciona SQLite cuando se configura la variable de entorno:

`DB_ENGINE=sqlite`

La forma de establecer esta variable depende de la terminal utilizada.

**Windows (PowerShell):**

```powershell
$env:DB_ENGINE="sqlite"
```

**Windows (CMD):**

```cmd
set DB_ENGINE=sqlite
```

**macOS:**

```bash
export DB_ENGINE=sqlite
```

**Linux:**

```bash
export DB_ENGINE=sqlite
```

Esta configuración se mantiene en la terminal actual. Si abres otra terminal, tendrás que establecer la variable de nuevo.

# 7. Ejecutar las migraciones

Las migraciones crean las tablas necesarias para almacenar los usuarios, publicaciones, respuestas y demás información del proyecto.

Con el entorno virtual activado y SQLite configurado, ejecuta:

```bash
python manage.py migrate
```

# 8. Crear un usuario administrador

Para acceder al panel de administración de Django, crea un superusuario:

```bash
python manage.py createsuperuser
```

Django solicitará:

- Nombre de usuario.
- Dirección de correo electrónico.
- Contraseña.

Guarda las credenciales para poder acceder posteriormente.

# 9. Comprobar la instalación

Antes de iniciar el servidor, comprueba que la configuración del proyecto es correcta:

```bash
python manage.py check
```

Si todo está correctamente configurado, Django mostrará un mensaje indicando que no se han detectado problemas.

# 10. Iniciar el servidor

Para arrancar Forum-Tech en local:

```bash
python manage.py runserver
```

Si el servidor se inicia correctamente, Django mostrará una dirección similar a:

```text
http://127.0.0.1:8000/
```

Abre esa dirección en el navegador para acceder a la aplicación.

Para detener el servidor, pulsa `CTRL + C` en la terminal.

# 11. Accesos principales

Con el servidor en funcionamiento, puedes acceder a las siguientes direcciones:

| Servicio | Dirección |
|---|---|
| Aplicación Forum-Tech | http://127.0.0.1:8000/ |
| Panel de administración | http://127.0.0.1:8000/admin/ |
| API REST | http://127.0.0.1:8000/api/v1/ |
| Especificación OpenAPI | http://127.0.0.1:8000/api/schema/ |
| Documentación Swagger | http://127.0.0.1:8000/api/docs/ |
| Documentación ReDoc | http://127.0.0.1:8000/api/redoc/ |

# 12. Configuración de PostgreSQL

Forum-Tech también dispone de configuración para utilizar PostgreSQL.

En el proyecto, PostgreSQL es el motor predeterminado cuando no se indica otro mediante `DB_ENGINE`.

La configuración de conexión utiliza:

| Variable | Descripción | Valor predeterminado |
|---|---|---|
| POSTGRES_DB | Nombre de la base de datos | Obligatoria |
| POSTGRES_USER | Usuario de PostgreSQL | Obligatoria |
| POSTGRES_PASSWORD | Contraseña | Obligatoria |
| POSTGRES_HOST | Dirección del servidor | 127.0.0.1 |
| POSTGRES_PORT | Puerto de conexión | 5432 |

## 12.1. Crear el archivo .env

En la carpeta principal del proyecto, crea un archivo llamado `.env`.

Su estructura debe ser:

```env
POSTGRES_DB=nombre_de_la_base_de_datos
POSTGRES_USER=nombre_del_usuario
POSTGRES_PASSWORD=contraseña_del_usuario
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Sustituye los valores de ejemplo por los datos de tu instalación de PostgreSQL.

El proyecto utiliza `python-dotenv` para cargar automáticamente el archivo `.env` desde la carpeta principal.

No es necesario cargarlo manualmente.

**IMPORTANTE:** No compartas el archivo `.env` ni publiques tus contraseñas en GitHub.

## 12.2. Comprobar la configuración

Una vez configurada la base de datos y creado el archivo `.env`, con PostgreSQL disponible y el entorno virtual activado, ejecuta:

```bash
python manage.py check
```

Después, para crear las tablas:

```bash
python manage.py migrate
```

Para crear el usuario administrador:

```bash
python manage.py createsuperuser
```

Para iniciar el servidor:

```bash
python manage.py runserver
```

Para utilizar PostgreSQL no debes establecer `DB_ENGINE=sqlite`.

# 13. Solución de problemas habituales

### Python no se reconoce como comando

Comprueba que Python está instalado y que se ha añadido al PATH en Windows.

### No se puede activar el entorno virtual en PowerShell

Ejecuta:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después vuelve a activar el entorno virtual.

### Error: No module named django

Comprueba que el entorno virtual está activado e instala las dependencias:

```bash
python -m pip install -r requirements.txt
```

### Error: No such table

Ejecuta las migraciones:

```bash
python manage.py migrate
```

### Error: faltan las variables de PostgreSQL

Comprueba que el archivo `.env` existe en la carpeta principal y contiene:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

### El puerto 8000 está ocupado

Puedes iniciar Django utilizando otro puerto:

```bash
python manage.py runserver 8001
```

En ese caso, accede a:

http://127.0.0.1:8001/

# 14. Recomendaciones importantes

- Activa siempre el entorno virtual antes de trabajar con Django.
- Instala las dependencias de `requirements.txt` antes de iniciar el servidor.
- Ejecuta las migraciones cuando corresponda.
- No compartas contraseñas ni archivos `.env`.
- No publiques credenciales privadas en el repositorio.
- El servidor de desarrollo de Django está pensado para pruebas locales, no para producción.

---

**Forum-Tech**

Proyecto desarrollado con Python y Django para compartir conocimientos, resolver dudas y aprender sobre tecnología y desarrollo de software.