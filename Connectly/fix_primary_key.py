import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:smaSwtowYMBPIhjBknUlhBkGTAPJFSsn@shortline.proxy.rlwy.net:27854/railway')
engine = create_engine(db_url)

print("Agregando clave primaria a social_media_users...")

try:
    with engine.connect() as conn:
        # Primero verificar si ya existe
        check_query = text("""
            SELECT COUNT(*) 
            FROM information_schema.TABLE_CONSTRAINTS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'social_media_users' 
            AND CONSTRAINT_TYPE = 'PRIMARY KEY'
        """)
        
        result = conn.execute(check_query).scalar()
        
        if result == 0:
            # No existe, agregar primary key
            conn.execute(text("ALTER TABLE social_media_users ADD PRIMARY KEY (UserID)"))
            conn.commit()
            print("✅ Clave primaria agregada exitosamente")
        else:
            print("ℹ️  La clave primaria ya existe")
            
except Exception as e:
    print(f"❌ Error: {e}")
