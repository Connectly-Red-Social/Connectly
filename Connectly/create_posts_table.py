import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de conexión
DB_URL = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:smaSwtowYMBPIhjBknUlhBkGTAPJFSsn@shortline.proxy.rlwy.net:27854/railway')

def main():
    engine = create_engine(DB_URL)

    # Paso previo: asegurar índice sobre social_media_users(UserID)
    ensure_index_sql = text("""
        ALTER TABLE social_media_users
          ADD INDEX idx_sm_users_userid (UserID);
    """)
    try:
        with engine.connect() as conn:
            conn.execute(ensure_index_sql)
            print("✔ Índice idx_sm_users_userid creado en social_media_users.UserID.")
    except ProgrammingError as pe:
        # 1061 = duplicate key name OR 1022 duplicate key, ignóralo
        msg = str(pe)
        if 'Duplicate key name' in msg or 'errno: 1022' in msg:
            print("ℹ Índice idx_sm_users_userid ya existe, omitiendo.")
        else:
            print(f"❌ Error al crear índice en social_media_users: {pe}")
            sys.exit(1)
    except SQLAlchemyError as se:
        print(f"❌ Error al conectar o asegurar índice: {se}")
        sys.exit(1)

    # Crear tabla posts con FK después de asegurar índice
    create_table_sql = text("""
    CREATE TABLE IF NOT EXISTS posts (
      PostID     INT           NOT NULL AUTO_INCREMENT,
      UserID     BIGINT        NOT NULL,
      Content    TEXT          NULL,
      Image      VARCHAR(255)  NULL,
      PostDate   DATETIME      NOT NULL,
      PRIMARY KEY (PostID),
      INDEX idx_posts_user (UserID),
      CONSTRAINT fk_posts_user
        FOREIGN KEY (UserID)
        REFERENCES social_media_users(UserID)
        ON DELETE CASCADE
    ) ENGINE=InnoDB
      DEFAULT CHARSET=utf8mb4
      COLLATE=utf8mb4_unicode_ci;
    """)

    try:
        with engine.connect() as conn:
            conn.execute(create_table_sql)
            print("✔ Tabla 'posts' creada o ya existía.")
    except ProgrammingError as pe:
        print(f"❌ Error de programación al crear la tabla: {pe}")
        sys.exit(1)
    except SQLAlchemyError as se:
        print(f"❌ Error al conectar o ejecutar DDL: {se}")
        sys.exit(1)

    print("\n🎉 La tabla 'posts' está lista para usarse.")

if __name__ == '__main__':
    main()
