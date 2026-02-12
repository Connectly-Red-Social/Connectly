"""
Script para inicializar todas las tablas de la base de datos Connectly.
Ejecuta este script una vez para crear todas las tablas necesarias.
"""
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar los módulos de creación de tablas
sys.path.append(os.path.dirname(__file__))

print("="*60)
print(" Inicializando Base de Datos Connectly")
print("="*60)

# Verificar que DATABASE_URL esté configurada
db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("❌ ERROR: DATABASE_URL no está configurada en .env")
    sys.exit(1)

print(f"\n📍 Conectando a: {db_url.split('@')[1] if '@' in db_url else 'base de datos local'}\n")

# Actualizar la URL en cada script
scripts = [
    'create_posts_table.py',
    'create_post_likes_table.py', 
    'create_comments_table.py',
    'create_user_follows_table.py',
    'create_messages_table.py'
]

for script in scripts:
    print(f"▶️  Ejecutando {script}...")
    try:
        # Leer el script
        with open(script, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Reemplazar la URL hardcodeada con la variable de entorno
        code = code.replace(
            "DB_URL = 'mysql+mysqlconnector://root:Nicolas20@localhost:3306/connectly'",
            f"DB_URL = '{db_url}'"
        )
        
        # Ejecutar el script
        exec(code)
        
    except Exception as e:
        print(f"❌ Error en {script}: {e}")
        sys.exit(1)

print("\n" + "="*60)
print(" ✅ Base de datos inicializada correctamente")
print("="*60)
print("\nAhora puedes ejecutar:")
print("  python generate_user_profiles.py  # Para crear usuarios de prueba")
print("  python app.py  # Para iniciar la aplicación")
