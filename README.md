# Forum Tech

Forum Tech es una plataforma web orientada a crear una comunidad tecnológica donde los usuarios puedan plantear preguntas, iniciar debates, compartir conocimientos y aportar soluciones.

El contenido se organiza mediante categorías, subforos y etiquetas, incorporando progresivamente perfiles de usuario, reputación, votaciones, moderación, búsqueda y notificaciones.

## Estado del proyecto

Actualmente se encuentra completada la base técnica correspondiente a la **Sesión 1**:

- Entorno virtual de Python configurado.
- Django instalado y proyecto inicializado.
- Aplicaciones `core`, `accounts` y `forum`.
- Sistema de templates configurado.
- Carpetas de archivos estáticos y media.
- Página de inicio funcional.
- Panel de administración de Django funcional.
- Base de datos inicial migrada.
- Repositorio Git configurado.
- Requisitos funcionales RF01-RF21 definidos.
- Requisitos no funcionales RNF01-RNF10 definidos.

La implementación de los modelos de negocio se realizará progresivamente en las siguientes sesiones.

## Tecnologías actuales

- Python 3
- Django 4.2
- SQLite
- HTML
- CSS
- JavaScript
- Git y GitHub

## Estructura principal

```text
Forum/
├── accounts/          # Usuarios y perfiles
├── config/            # Configuración principal de Django
├── core/              # Funcionalidades generales
├── forum/             # Funcionalidades del foro
├── media/             # Archivos subidos
├── static/
│   ├── css/
│   ├── images/
│   └── js/
├── templates/
│   └── core/
│       └── home.html
├── manage.py
└── requirements.txt
Instalación local
1. Clonar el repositorio
git clone https://github.com/malena1688/Forum-Tech.git
cd Forum-Tech

2. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

3. Instalar las dependencias
python3 -m pip install -r requirements.txt

4. Aplicar las migraciones
python3 manage.py migrate

5. Ejecutar el servidor
python3 manage.py runserver

La aplicación estará disponible normalmente en:
http://127.0.0.1:8000/
Comprobación del proyecto
python3 manage.py check

Módulos principales
core
Contiene las funcionalidades generales del proyecto y la página de inicio.
accounts
Está destinado a la gestión de usuarios, autenticación y perfiles. La base para el usuario personalizado se desarrollará en la Sesión 2.
forum
Está destinado a las funcionalidades principales de la comunidad: categorías, subforos, hilos, respuestas, etiquetas, votaciones y otras funciones que se implementarán progresivamente.
Funcionalidades planificadas
- Registro, inicio y cierre de sesión.
- Perfiles personalizables.
- Categorías y subforos.
- Hilos de discusión y preguntas.
- Respuestas y soluciones aceptadas.
- Etiquetas.
- Votaciones y reacciones.
- Reputación, rangos e insignias.
- Marcadores.
- Notificaciones.
- Búsqueda y filtrado.
- Feeds de contenido.
- Moderación y reportes.
- Contenido técnico con Markdown/WYSIWYG y bloques de código.
Próximos pasos
La Sesión 2 se centrará en mejorar la arquitectura y configuración del proyecto, incluyendo la separación de settings por entorno, gestión de variables de entorno y secretos, logging, base para un usuario personalizado y pruebas iniciales.
Documentación
La documentación de la Sesión 1 incluye:
- Requisitos funcionales: RF01-RF21
- Requisitos no funcionales: RNF01-RNF10
Equipo
Proyecto desarrollado de forma colaborativa utilizando Git y GitHub.
