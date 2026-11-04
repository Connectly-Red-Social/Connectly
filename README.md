# 🌐 Connectly - Red Social con Algoritmos de Grafos

## 📋 Índice
- [🚀 Despliegue en Render](#-despliegue-en-render)
- [Descripción General](#-descripción-general)
- [Arquitectura y Tecnologías](#️-arquitectura-y-tecnologías)
- [Características Principales](#-características-principales)
- [Algoritmos Implementados](#-algoritmos-implementados)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación y Configuración](#️-instalación-y-configuración)
- [Base de Datos](#️-base-de-datos)
- [Funcionalidades Detalladas](#-funcionalidades-detalladas)
- [Cómo Mejorar el Proyecto](#-cómo-mejorar-el-proyecto)

---

## 🚀 Despliegue en Render

### Paso 1: Preparar Base de Datos MySQL en la Nube

**Opción A: Railway (Recomendado - Gratis)**
1. Ve a [Railway.app](https://railway.app/) y crea una cuenta
2. New Project → Add MySQL
3. En la pestaña "Connect", copia la **MySQL Connection URL**
4. **Importante:** Convierte el formato de `mysql://user:pass@host:port/dbname` a `mysql+pymysql://user:pass@host:port/dbname`

**Opción B: PlanetScale (Gratis)**
1. Ve a [PlanetScale.com](https://planetscale.com/)
2. Crea una nueva base de datos
3. Obtén la connection string en formato MySQL

### Paso 2: Tablas y datos (automático)

No hay que ejecutar scripts. Al arrancar, la app crea las tablas que falten y, si `social_media_users` está vacía, carga `data/SocialMediaUsersDataset.csv` (1500 usuarios). Solo define `DATABASE_URL` en Render.

### Paso 3: Subir a GitHub

```bash
git add .
git commit -m "Preparado para despliegue en Render"
git push origin main
```

### Paso 4: Desplegar en Render

1. Ve a [Render.com](https://render.com/) y crea una cuenta
2. Click en **"New +"** → **"Web Service"**
3. Conecta tu repositorio de GitHub
4. Configuración del servicio:
   - **Name:** `connectly` (o el que prefieras)
   - **Runtime:** `Python 3`
   - **Build Command:** 
     ```
     pip install -r Connectly/requirements.txt
     ```
   - **Start Command:** 
     ```
     cd Connectly && gunicorn --worker-class gthread --threads 100 -w 1 --bind 0.0.0.0:$PORT app:app
     ```
   
5. **Variables de Entorno** (Environment Variables):
   - Click en "Advanced" → "Add Environment Variable"
   - Agrega estas variables:
     - `DATABASE_URL`: Tu connection string completa (el de Railway/PlanetScale con formato `mysql+pymysql://...`)
     - `SECRET_KEY`: Genera una clave segura [aquí](https://randomkeygen.com/)
     - `PYTHON_VERSION`: `3.11.0`

6. Click en **"Create Web Service"**
7. Espera 5-10 minutos mientras Render hace el despliegue

### Paso 5: Probar tu Aplicación

- Tu app estará disponible en: `https://connectly.onrender.com` (o el nombre que elegiste)
- **Nota:** En el plan gratuito, la app se dormirá después de 15 minutos de inactividad
- El primer acceso después de dormir tomará ~30-60 segundos

### ⚠️ Consideraciones del Plan Gratuito

**Limitaciones:**
- ❄️ **Hibernación:** La app se duerme tras 15 min sin tráfico
- ⏱️ **Wake-up time:** 30-60 segundos para el primer acceso
- 💾 **Almacenamiento temporal:** Las imágenes subidas se borran al reiniciar

**Soluciones:**
- Para imágenes permanentes, integra [Cloudinary](https://cloudinary.com/) (tiene plan gratuito)
- Para evitar hibernación, actualiza a Render paid plan ($7/mes)

### 🔄 Actualizar la Aplicación

Cada vez que hagas push a GitHub, Render desplegará automáticamente:
```bash
git add .
git commit -m "Nuevas funcionalidades"
git push origin main
```

---

## 📖 Descripción General

**Connectly** es una red social completa construida con Flask que utiliza algoritmos avanzados de teoría de grafos para conectar usuarios basándose en intereses comunes. La aplicación implementa el **Algoritmo de Kosaraju** para encontrar componentes fuertemente conectados en un grafo de usuarios, permitiendo recomendaciones inteligentes y visualización de comunidades.

### ✨ Propósito del Proyecto
- Demostrar la aplicación de algoritmos de grafos en redes sociales reales
- Crear conexiones significativas entre usuarios con intereses similares
- Proporcionar una plataforma completa con chat en tiempo real, posts y sistema de seguimiento

---

## 🏗️ Arquitectura y Tecnologías

### Backend
- **Flask 3.1.1**: Framework web principal
- **Flask-SocketIO 5.5.1**: Comunicación en tiempo real para chat
- **SQLAlchemy 2.0.41**: ORM para manejo de base de datos
- **MySQL**: Base de datos relacional

### Algoritmos y Análisis de Datos
- **NetworkX 3.5**: Librería para análisis de grafos
- **Algoritmo de Kosaraju**: Componentes fuertemente conectados
- **BFS (Breadth-First Search)**: Sistema de recomendaciones
- **PyVis 0.3.2**: Visualización interactiva de grafos

### Frontend
- **Tailwind CSS 3.4.14**: Framework CSS utilitario
- **HTML/JavaScript**: Templates dinámicos
- **Socket.IO Client**: Comunicación bidireccional en tiempo real
- **Tom Select**: Selector avanzado de usuarios

### Visualización y Análisis
- **Matplotlib**: Gráficos estáticos
- **PyVis**: Gráficos interactivos en HTML
- **Pandas**: Procesamiento de datos

---

## 🎯 Características Principales

### 1. **Sistema de Autenticación**
- Login de usuarios estándar
- Panel de administrador especial (`admin/admin`)
- Gestión de sesiones con Flask

### 2. **Perfiles de Usuario**
- Información personal (nombre, género, país, intereses)
- Contador de posts, seguidores y seguidos
- Imagen de perfil
- Usuarios similares basados en intereses (algoritmo de Kosaraju)
- Recomendaciones de usuarios (BFS + coincidencias de interés secundario)

### 3. **Sistema de Seguimiento**
- Seguir/dejar de seguir usuarios
- Visualización de seguidores y seguidos
- Seguidores mutuos para chat
- Verificación de relaciones bidireccionales

### 4. **Publicaciones (Posts)**
- Crear posts con texto e imágenes
- Like/unlike de publicaciones
- Sistema de comentarios
- Feed principal ordenado cronológicamente
- Eliminar posts propios

### 5. **Chat en Tiempo Real**
- Mensajería instantánea usando WebSockets
- Solo disponible entre seguidores mutuos
- Envío de imágenes en mensajes
- Salas de chat privadas por pareja de usuarios

### 6. **Panel de Administrador**
- Visualización de todos los usuarios
- Filtrado por intereses
- **Visualización del grafo de usuarios** con PyVis
- Control del límite de nodos a visualizar
- Estadísticas de la red

### 7. **Sistema de Búsqueda y Filtros**
- Búsqueda por intereses
- Filtros por género
- Filtros por país
- Contadores dinámicos de usuarios por filtro

---

## 🧮 Algoritmos Implementados

### 1. **Algoritmo de Kosaraju (Componentes Fuertemente Conectados)**

**Ubicación**: [`Connectly/community_connection/script/community_data.py`](Connectly/community_connection/script/community_data.py) (líneas 48-106)

**¿Qué hace?**
Encuentra grupos de usuarios que están todos conectados entre sí a través de intereses comunes. Si dos usuarios comparten el mismo interés principal, se crea una conexión bidireccional.

**Funcionamiento**:
```
1. Crear grafo dirigido donde:
   - Nodos = Usuarios
   - Aristas = Conexiones bidireccionales si comparten interés

2. Primera pasada DFS:
   - Recorrer todos los nodos
   - Guardar orden de finalización en un stack

3. Transponer el grafo:
   - Invertir dirección de todas las aristas

4. Segunda pasada DFS (en orden del stack):
   - Cada árbol DFS = Un componente fuertemente conectado
   - Estos son los "círculos sociales" del mismo interés
```

**Aplicación en Connectly**:
- Agrupa usuarios con el mismo interés primario
- Los usuarios del mismo componente son "usuarios similares"
- Se muestran en el perfil como conexiones recomendadas

**Complejidad**: O(V + E) donde V = usuarios, E = conexiones

### 2. **BFS para Recomendaciones**

**Ubicación**: [`Connectly/community_connection/script/community_data.py`](Connectly/community_connection/script/community_data.py) (líneas 418-465)

**¿Qué hace?**
Explora la red de forma escalonada para encontrar "amigos de amigos" que el usuario aún no sigue.

**Funcionamiento**:
```
1. Iniciar con el usuario actual
2. Examinar a quién siguen sus seguidos
3. Agregar esos usuarios como recomendaciones
4. Continuar expandiendo hasta llenar la lista (máx 15)
```

**Aplicación**: Genera recomendaciones de usuarios basadas en conexiones sociales reales.

### 3. **Coincidencia de Segundo Interés**

**Ubicación**: [`Connectly/community_connection/script/community_data.py`](Connectly/community_connection/script/community_data.py) (líneas 213-228)

**¿Qué hace?**
Extrae y compara el segundo interés de los usuarios para recomendaciones más refinadas.

---

## 📁 Estructura del Proyecto

```
complejidad_Connectly/
├── Connectly/                          # Aplicación principal
│   ├── app.py                          # 🔴 NÚCLEO: Aplicación Flask, rutas, SocketIO
│   ├── services/                       # Modelos, esquema, seeding y registro
│   ├── graph.py                        # 📊 Implementación standalone del algoritmo de Kosaraju
│   ├── requirements.txt                # Dependencias de Python
│   │
│   ├── community_connection/           # Módulo de lógica de negocios
│   │   └── script/
│   │       └── community_data.py       # 🧠 CLASE PRINCIPAL: Lógica de grafos y BD
│   │
│   ├── static/                         # Recursos estáticos
│   │   ├── input.css                   # CSS fuente de Tailwind
│   │   ├── output.css                  # CSS compilado de Tailwind
│   │   ├── styles.css                  # Estilos personalizados
│   │   └── images/                     # Imágenes del proyecto
│   │
│   ├── storage/                        # Archivos generados dinámicamente
│   │   ├── admin_graph.html            # Visualización del grafo (PyVis)
│   │   └── [imágenes subidas]          # Posts y mensajes de chat
│   │
│   ├── templates/                      # Templates HTML (Jinja2)
│   │   ├── login.html                  # Página de login
│   │   ├── home.html                   # Feed principal
│   │   ├── profile.html                # Perfil de usuario
│   │   ├── chat.html                   # Interfaz de chat
│   │   ├── post_form.html              # Formulario de creación de post
│   │   ├── followers.html              # Lista de seguidores
│   │   ├── following.html              # Lista de seguidos
│   │   ├── search.html                 # Búsqueda de usuarios
│   │   ├── sidebar.html                # Barra lateral (componente)
│   │   ├── admin_dashboard.html        # Dashboard del admin
│   │   ├── admin_graph.html            # Visualización de grafos (admin)
│   │   └── view_all_users.html         # Lista completa de usuarios
│   │
│
├── data/
│   └── SocialMediaUsersDataset.csv     # 📊 Dataset de usuarios (1500 registros)
│
├── lib/                                # Librerías externas
│   ├── bindings/
│   │   └── utils.js                    # Utilidades JavaScript
│   ├── tom-select/                     # Selector avanzado de usuarios
│   │   ├── tom-select.complete.min.js
│   │   └── tom-select.css
│   └── vis-9.1.2/                     # Librería de visualización de grafos
│       ├── vis-network.min.js
│       └── vis-network.css
│
├── package.json                        # Configuración de npm
├── tailwind.config.js                  # Configuración de Tailwind CSS
└── README.md                           # 📖 Este archivo
```

---

## 🧱 Arquitectura por Bounded Contexts

Un solo despliegue Flask y una sola base MySQL, pero el código está separado por contexto. Cada contexto
tiene sus tablas (`models.py`) y su lógica (`service.py`); entre contextos solo se comparte el `user_id`.

```
Connectly/
├── app.py                     # Composición: crea la app, arranca la BD y registra rutas
├── shared/                    # Infraestructura común
│   ├── db.py                  #   engine (PyMySQL, pool_pre_ping, DATABASE_URL o respaldo local)
│   ├── metadata.py            #   MetaData único
│   ├── schema.py              #   create_all + columnas/FK faltantes + vista de compatibilidad
│   ├── seed.py                #   carga del dataset (solo si no hay perfiles)
│   ├── legacy_migration.py    #   migra bases con el esquema antiguo (social_media_users)
│   └── bootstrap.py           #   orquesta todo al arrancar (con lock para varios workers)
├── contexts/
│   ├── users/                 # Cuenta: users
│   ├── iam/                   # Acceso: credentials, roles, user_roles, login_attempts (+ rutas /login /register /logout)
│   ├── profiles/              # Perfil: profiles, interests, profile_interests
│   ├── social/                # posts, post_likes, comments, user_follows, messages,
│   │                          #   blocks, notifications, reports (+ rutas de bloqueo/reporte/notificaciones)
│   └── community/             # Grafo (Kosaraju) y recomendaciones: lectura sobre la vista social_media_users
└── application/
    └── registration.py        # Caso de uso: users + iam + profiles en una transacción
```

**Dataset:** `data/SocialMediaUsersDataset.csv` ya no es una tabla propia. Al primer arranque se reparte en
`users`, `credentials`, `profiles` e `interests`, conservando los `UserID` originales. `social_media_users` es ahora
una **vista de solo lectura** para que `contexts/community` siga funcionando sin reescribir sus consultas.

**Bases antiguas:** si `social_media_users` era una tabla real, el arranque la migra solo y la conserva como
`legacy_social_media_users`.

**Administrador:** se crea al primer arranque con `ADMIN_USERNAME` / `ADMIN_PASSWORD` (rol `admin`).

## 🛠️ Instalación y Configuración

### Prerrequisitos
- Python 3.8 o superior
- MySQL 8.0 o superior
- Node.js y npm (para Tailwind CSS)
- Git

### Paso 1: Clonar el Repositorio
```bash
cd complejidad_Connectly
```

### Paso 2: Configurar Entorno Virtual de Python
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

### Paso 3: Instalar Dependencias de Python
```bash
cd Connectly
pip install -r requirements.txt
```

### Paso 4: Configurar Base de Datos MySQL

1. **Crear la base de datos vacía**:
```sql
CREATE DATABASE connectly CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. **Conexión**: la app lee `DATABASE_URL` (ver `.env.example`). Si no existe, usa el respaldo local `mysql+pymysql://root:Nicolas20@localhost:3306/connectly` definido en `Connectly/services/db.py`.

### Paso 5: Tablas y datos (automático)

Al ejecutar la app (`bootstrap_database` en `services/bootstrap.py`):
- `services/schema.py` crea las tablas definidas en `services/models.py` si no existen y actualiza bases antiguas.
- `services/seed.py` carga el CSV solo si `social_media_users` está vacía (no duplica datos).

### Paso 7: Configurar Tailwind CSS (Opcional)

```bash
# En el directorio raíz del proyecto
npm install

# Compilar CSS (si haces cambios en templates)
npx tailwindcss -i ./Connectly/static/input.css -o ./Connectly/static/output.css --watch
```

### Paso 8: Ejecutar la Aplicación

```bash
cd Connectly
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

---

## 🗄️ Base de Datos

### Esquema de Tablas

#### 1. **social_media_users** (Tabla principal)
```sql
- UserID (BIGINT, PK): ID único del usuario
- Name (VARCHAR): Nombre completo
- Gender (VARCHAR): Género
- DOB (DATE): Fecha de nacimiento
- Interests (TEXT): Lista de intereses separados por comas
- City (VARCHAR): Ciudad
- Country (VARCHAR): País
- username (VARCHAR): Usuario para login
- password (VARCHAR): Contraseña (⚠️ en texto plano - INSEGURO)
- profile_image (VARCHAR): URL de la imagen de perfil
```

#### 2. **posts**
```sql
- PostID (INT, PK, AUTO_INCREMENT): ID de la publicación
- UserID (BIGINT, FK): Usuario que creó el post
- Content (TEXT): Contenido del post
- Image (VARCHAR): Ruta de la imagen (opcional)
- PostDate (DATETIME): Fecha de creación
```

#### 3. **messages**
```sql
- message_id (INT, PK, AUTO_INCREMENT): ID del mensaje
- sender_id (BIGINT, FK): Usuario que envía
- receiver_id (BIGINT, FK): Usuario que recibe
- content (TEXT): Contenido del mensaje
- image (VARCHAR): Ruta de imagen (opcional)
- sent_at (DATETIME): Fecha de envío
```

#### 4. **user_follows**
```sql
- follower_id (BIGINT, FK, PK): Usuario que sigue
- followed_id (BIGINT, FK, PK): Usuario seguido
- follow_date (DATETIME): Fecha del seguimiento
```

#### 5. **comments**
```sql
- CommentID (INT, PK, AUTO_INCREMENT): ID del comentario
- PostID (INT, FK): Post comentado
- UserID (BIGINT, FK): Usuario que comenta
- Content (TEXT): Contenido del comentario
- CommentDate (DATETIME): Fecha del comentario
```

#### 6. **post_likes**
```sql
- PostID (INT, FK, PK): Post que se likea
- UserID (BIGINT, FK, PK): Usuario que da like
```

### Relaciones
- Un usuario puede tener muchos posts (1:N)
- Un usuario puede seguir a muchos usuarios (N:M)
- Un post puede tener muchos comentarios y likes (1:N)
- Dos usuarios pueden intercambiar muchos mensajes (N:M)

---

## 🎮 Funcionalidades Detalladas

### Archivo Principal: `app.py`

#### Rutas Principales:

1. **`/` (home)**: Redirecciona al login
2. **`/login`**: Autenticación de usuarios y admin
3. **`/admin_dashboard`**: Panel de administrador
4. **`/admin_graph`**: Visualización del grafo de usuarios con PyVis
5. **`/view_all_users`**: Lista de todos los usuarios con filtros
6. **`/profile/<user_id>`**: Perfil de usuario con usuarios similares
7. **`/home`**: Feed de publicaciones
8. **`/create_post`**: Crear nueva publicación
9. **`/chat`**: Sistema de mensajería en tiempo real
10. **`/search`**: Búsqueda por intereses
11. **`/follow/<user_id>`**: Seguir usuario (AJAX)
12. **`/unfollow/<user_id>`**: Dejar de seguir (AJAX)
13. **`/like_post/<post_id>`**: Dar like a un post
14. **`/add_comment/<post_id>`**: Agregar comentario
15. **`/send_message`**: Enviar mensaje de chat
16. **`/followers/<user_id>`**: Lista de seguidores
17. **`/following/<user_id>`**: Lista de seguidos

#### WebSocket Events (SocketIO):

```python
@socketio.on('join')
def on_join(data):
    # Usuario se une a sala de chat específica
    # Formato de sala: chat_{min_id}_{max_id}
```

```python
socketio.emit('receive_message', {...}, room='chat_1_2')
# Emite mensajes en tiempo real a usuarios en la sala
```

### Clase Principal: `CommunityData`

**Ubicación**: [`Connectly/community_connection/script/community_data.py`](Connectly/community_connection/script/community_data.py)

#### Métodos Principales:

```python
def _load_user_groups(self, limit=1500)
```
- Carga usuarios desde BD
- Crea grafo dirigido con NetworkX
- Ejecuta algoritmo de Kosaraju
- Retorna diccionario de usuarios con sus componentes

```python
def get_user_profile(self, user_id)
```
- Retorna datos del usuario y usuarios similares del mismo componente

```python
def get_user_recommendations(self, user_id)
```
- Usa tres estrategias:
  1. Amigos en común (seguidores de seguidores)
  2. Usuarios con coincidencia en segundo interés
  3. BFS para explorar red social

```python
def generate_pyvis_graph(self, file_path, max_nodes=300)
```
- Genera grafo interactivo en HTML
- Nodos coloreados por grupo de interés
- Incluye imágenes de perfil
- Física simulada para layout automático

```python
def follow_user(follower_id, followed_id)
def unfollow_user(follower_id, followed_id)
def is_following(follower_id, followed_id)
```
- Gestión del sistema de seguimiento

```python
def get_mutual_followers(user_id)
```
- Obtiene usuarios que son seguidores y seguidos mutuamente
- Usado para determinar con quién se puede chatear

```python
def get_messages_between_users(user_id_1, user_id_2)
```
- Recupera historial de mensajes entre dos usuarios

```python
def like_post(post_id, user_id)
def unlike_post(post_id, user_id)
def is_post_liked(post_id, user_id)
def get_like_count(post_id)
```
- Sistema de likes en publicaciones

```python
def add_comment(post_id, user_id, content)
def get_comments_for_post(post_id)
```
- Sistema de comentarios

---

## 🚀 Cómo Mejorar el Proyecto

### 🔴 CRÍTICO - Seguridad

1. **Hashing de Contraseñas**
   - **Problema**: Las contraseñas se almacenan en texto plano
   - **Solución**: Usar `bcrypt` o `werkzeug.security`
   ```python
   from werkzeug.security import generate_password_hash, check_password_hash
   
   # Al registrar:
   hashed = generate_password_hash(password)
   
   # Al login:
   if check_password_hash(stored_hash, password):
       # Login exitoso
   ```

2. **Variables de Entorno**
   - **Problema**: Credenciales hardcodeadas en código
   - **Solución**: Usar archivo `.env`
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   DB_URL = os.getenv('DATABASE_URL')
   app.secret_key = os.getenv('SECRET_KEY')
   ```

3. **Validación de Entrada**
   - Implementar validación de formularios con Flask-WTF
   - Sanitizar entradas de usuario para prevenir XSS
   - Validar tipos de archivo en uploads

4. **CSRF Protection**
   - Implementar tokens CSRF en formularios
   ```python
   from flask_wtf.csrf import CSRFProtect
   csrf = CSRFProtect(app)
   ```

5. **SQL Injection Protection**
   - Ya usa parámetros con SQLAlchemy ✅
   - Nunca construir queries con f-strings

### 🟡 Rendimiento

1. **Caché de Resultados**
   ```python
   from flask_caching import Cache
   
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   
   @cache.memoize(timeout=300)
   def get_user_recommendations(user_id):
       # Esta función será cacheada por 5 minutos
   ```

2. **Paginación**
   - Implementar paginación en feed de posts
   - Limitar usuarios similares mostrados
   ```python
   page = request.args.get('page', 1, type=int)
   posts = query.paginate(page=page, per_page=20)
   ```

3. **Índices de Base de Datos**
   - Ya tiene índices básicos ✅
   - Considerar índice compuesto en `messages (sender_id, receiver_id, sent_at)`
   ```sql
   CREATE INDEX idx_messages_conversation 
   ON messages(sender_id, receiver_id, sent_at);
   ```

4. **Carga Diferida de Imágenes**
   - Implementar lazy loading en frontend
   ```html
   <img loading="lazy" src="..." alt="...">
   ```

5. **Comprimir Imágenes**
   - Usar Pillow para redimensionar y comprimir uploads
   ```python
   from PIL import Image
   
   img = Image.open(image_file)
   img.thumbnail((800, 800))
   img.save(path, optimize=True, quality=85)
   ```

### 🟢 Características Nuevas

1. **Sistema de Notificaciones**
   - Notificar cuando alguien te sigue
   - Notificar nuevos likes/comentarios
   - Usar SocketIO para notificaciones en tiempo real

2. **Grupos/Comunidades**
   - Crear grupos basados en intereses
   - Usar los componentes de Kosaraju como grupos automáticos
   - Chat grupal

3. **Histórico de Actividad**
   - Registrar acciones de usuarios
   - Feed de actividad personalizado

4. **Algoritmo de Feed Inteligente**
   - Ordenar posts por relevancia (no solo cronológico)
   - Priorizar posts de usuarios similares
   ```python
   # Ranking score = recencia + likes + coincidencia_intereses
   score = (1 / hours_ago) * 10 + like_count + (100 if same_interest else 0)
   ```

5. **Stories/Estado Temporal**
   - Posts que desaparecen en 24 horas
   - Tabla con campo `expires_at`

6. **Menciones y Hashtags**
   - Parser de @usuario y #hashtag
   - Índice full-text para búsquedas eficientes

7. **Verificación de Usuarios**
   - Badge de verificado
   - Sistema de reputación

### 🔵 Arquitectura

1. **Migrar a ORM Completo**
   - Usar modelos de SQLAlchemy en vez de SQL directo
   ```python
   class User(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       name = db.Column(db.String(100))
       posts = db.relationship('Post', backref='author')
   ```

2. **Separar Lógica de Negocio**
   - Crear servicios separados (UserService, PostService)
   - Mantener app.py solo con rutas

3. **API REST**
   - Crear endpoints REST para ser consumidos por frontend SPA
   - Usar Flask-RESTful o FastAPI

4. **Migraciones de BD**
   - Implementar Alembic para control de versiones de schema
   ```bash
   alembic init alembic
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

5. **Testing**
   - Unit tests con pytest
   - Integration tests de rutas
   ```python
   def test_login(client):
       response = client.post('/login', data={'username': 'test'})
       assert response.status_code == 200
   ```

6. **Frontend Moderno**
   - Migrar a React/Vue para SPA
   - Mantener Flask como API backend

7. **Dockerización**
   ```dockerfile
   FROM python:3.10
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["python", "app.py"]
   ```

8. **CI/CD**
   - GitHub Actions para tests automáticos
   - Deploy automático a servidor

### 🟣 Algoritmos Adicionales

1. **PageRank para Usuarios Influyentes**
   ```python
   # Identificar usuarios más importantes de la red
   import networkx as nx
   pagerank = nx.pagerank(G)
   top_users = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
   ```

2. **Detección de Comunidades con Louvain**
   ```python
   import community as community_louvain
   communities = community_louvain.best_partition(G.to_undirected())
   ```

3. **Camino Más Corto**
   - Encontrar "grados de separación" entre usuarios
   ```python
   path = nx.shortest_path(G, source=user1, target=user2)
   degrees = len(path) - 1
   ```

4. **Centralidad de Intermediación**
   - Identificar "puentes" entre comunidades
   ```python
   betweenness = nx.betweenness_centrality(G)
   bridges = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)
   ```

5. **Sistema de Recomendación Colaborativo**
   - Filtrado colaborativo usuario-usuario
   - Matriz de similitud con scipy

### 🟤 UI/UX

1. **Modo Oscuro**
   - Toggle entre light/dark
   - Usar CSS variables

2. **Responsive Design Completo**
   - Probar en diferentes resoluciones
   - Hamburger menu para móvil

3. **Carga Infinita**
   - Eliminar paginación tradicional
   - Cargar posts al hacer scroll

4. **Drag & Drop para Imágenes**
   - Implementar en formulario de posts

5. **Preview de Enlaces**
   - Extraer metadata de URLs (Open Graph)
   - Mostrar preview card

6. **Emojis y Reacciones**
   - Sistema de reacciones múltiples (como Facebook)
   - Picker de emojis

### 🔵 Observabilidad

1. **Logging Estructurado**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   logger.info(f"User {user_id} logged in")
   ```

2. **Métricas**
   - Usuarios activos diarios/mensuales
   - Posts por día
   - Tiempo promedio de respuesta

3. **Monitoreo de Errores**
   - Integrar Sentry para error tracking
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn="your-dsn")
   ```

---

## 📊 Análisis de Complejidad

### Algoritmo de Kosaraju
- **Complejidad Temporal**: O(V + E)
  - V = número de usuarios
  - E = número de conexiones (aristas)
- **Complejidad Espacial**: O(V)
- **Escalabilidad**: Eficiente hasta ~100,000 usuarios

### BFS para Recomendaciones
- **Complejidad Temporal**: O(V + E) en peor caso
- **Limitado a**: 15 recomendaciones máximo
- **Escalabilidad**: Buena con límite de profundidad

### Queries de Base de Datos
- Mayoría son O(1) o O(log n) gracias a índices ✅
- Joins con user_follows pueden ser costosos a gran escala
- Considerar desnormalización para métricas (followers_count)

---

## 📝 Notas de Desarrollo

### Credenciales de Administrador
- **Usuario**: `admin`
- **Contraseña**: `admin`

### Usuarios de Prueba
Los usuarios se cargan desde [`data/SocialMediaUsersDataset.csv`](data/SocialMediaUsersDataset.csv)
- 1500 usuarios
- Username = Name (en minúsculas, sin espacios)
- Password = "password" + UserID

### Estructura de Salas de Chat
- Formato: `chat_{min_user_id}_{max_user_id}`
- Ejemplo: Usuario 1 y Usuario 50 → `chat_1_50`
- Garantiza sala única por pareja

### Almacenamiento de Archivos
- Posts: `/storage/user{id}_{timestamp}_{filename}`
- Mensajes: `/storage/user{id}_{timestamp}_{uuid}.png`
- Grafos: `/storage/admin_graph.html` (sobrescribe)

---

## 🤝 Contribuir

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

## 👨‍💻 Autor

Proyecto desarrollado como demostración de aplicación de algoritmos de grafos en redes sociales.

---

## 🙏 Agradecimientos

- **NetworkX**: Por la excelente librería de grafos
- **PyVis**: Por la visualización interactiva
- **Flask**: Por el framework minimalista y potente
- **Tailwind CSS**: Por el sistema de diseño utilitario

---

## 📞 Soporte

Si encuentras algún problema o tienes preguntas:
1. Revisa la sección de troubleshooting abajo
2. Abre un issue en el repositorio
3. Consulta la documentación de las herramientas usadas

---

## 🔧 Troubleshooting

### Error: "Can't connect to MySQL server"
- Verifica que MySQL esté corriendo: `mysql.server start`
- Comprueba credenciales en DB_URL
- Verifica que el puerto 3306 esté disponible

### Error: "Table doesn't exist"
- Ejecuta todos los scripts de creación de tablas en orden
- Verifica que la base de datos `connectly` exista

### Error: "ModuleNotFoundError"
- Activa el entorno virtual: `venv\Scripts\activate`
- Reinstala dependencias: `pip install -r requirements.txt`

### Chat no funciona
- Verifica que ambos usuarios se sigan mutuamente
- Revisa consola del navegador para errores de SocketIO
- Comprueba que puerto 5000 no esté bloqueado por firewall

### Grafo no se muestra
- Verifica que existe `/storage/admin_graph.html`
- Comprueba permisos de escritura en carpeta storage
- Reduce el límite de nodos si hay timeout

### Imágenes no cargan
- Verifica permisos de escritura en `/storage`
- Comprueba que la ruta sea accesible vía web
- Revisa que el tamaño de archivo no exceda límites de Flask

---

## 🎓 Conceptos Aprendidos

Este proyecto demuestra:
- ✅ Aplicación práctica del algoritmo de Kosaraju
- ✅ Uso de grafos dirigidos en aplicaciones reales
- ✅ Implementación de WebSockets para tiempo real
- ✅ Arquitectura MVC en Flask
- ✅ Integración de algoritmos de grafos con bases de datos relacionales
- ✅ Visualización de datos complejos con PyVis
- ✅ Sistema completo de autenticación y autorización
- ✅ Manejo de archivos y uploads en Flask
- ✅ Diseño responsive con Tailwind CSS

---

## 📚 Recursos Adicionales

### Documentación Oficial
- [Flask Documentation](https://flask.palletsprojects.com/)
- [NetworkX Documentation](https://networkx.org/documentation/stable/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Socket.IO Documentation](https://socket.io/docs/v4/)
- [Tailwind CSS](https://tailwindcss.com/docs)

### Algoritmos de Grafos
- [Kosaraju's Algorithm - GeeksforGeeks](https://www.geeksforgeeks.org/strongly-connected-components/)
- [Graph Algorithms - MIT OpenCourseWare](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/)

### Papers Relevantes
- "The Anatomy of a Large-Scale Social Search Engine" - Facebook Graph Search
- "Finding and evaluating community structure in networks" - Newman, 2004

---

**¡Gracias por revisar Connectly!** 🎉

Si este proyecto te fue útil, considera darle una ⭐ en GitHub.
