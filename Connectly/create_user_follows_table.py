import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError

# Configuración de conexión
DB_URL = 'mysql+mysqlconnector://root:Nicolas20@localhost:3306/connectly'

def main():
    engine = create_engine(DB_URL)

    # Crear tabla user_follows si no existe
    create_table_sql = text("""
    CREATE TABLE IF NOT EXISTS user_follows (
      follower_id  BIGINT       NOT NULL,
      followed_id  BIGINT       NOT NULL,
      follow_date  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (follower_id, followed_id),
      INDEX idx_follows_follower (follower_id),
      INDEX idx_follows_followed (followed_id),
      CONSTRAINT fk_follows_follower
        FOREIGN KEY (follower_id)
        REFERENCES social_media_users(UserID)
        ON DELETE CASCADE,
      CONSTRAINT fk_follows_followed
        FOREIGN KEY (followed_id)
        REFERENCES social_media_users(UserID)
        ON DELETE CASCADE
    ) ENGINE=InnoDB
      DEFAULT CHARSET=utf8mb4
      COLLATE=utf8mb4_unicode_ci;
    """)

    try:
        with engine.connect() as conn:
            conn.execute(create_table_sql)
            print("✔ Tabla 'user_follows' creada o ya existía.")
    except ProgrammingError as pe:
        print(f"❌ Error de programación al crear la tabla user_follows: {pe}")
        sys.exit(1)
    except SQLAlchemyError as se:
        print(f"❌ Error al conectar o ejecutar DDL para user_follows: {se}")
        sys.exit(1)

    print("\n🎉 La tabla 'user_follows' está lista para usarse.")

if __name__ == '__main__':
    main()
