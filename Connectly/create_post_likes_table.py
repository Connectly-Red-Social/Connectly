import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de conexión
DB_URL = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:Nicolas20@localhost:3306/connectly')

def main():
    engine = create_engine(DB_URL)

    # Crear tabla post_likes
    create_table_sql = text("""
    CREATE TABLE IF NOT EXISTS post_likes (
      PostID     INT           NOT NULL,
      UserID     BIGINT        NOT NULL,
      LikeDate   DATETIME      DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (PostID, UserID),
      INDEX idx_post_likes_post (PostID),
      INDEX idx_post_likes_user (UserID),
      CONSTRAINT fk_post_likes_post
        FOREIGN KEY (PostID)
        REFERENCES posts(PostID)
        ON DELETE CASCADE,
      CONSTRAINT fk_post_likes_user
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
            conn.commit()
            print("✔ Tabla 'post_likes' creada exitosamente.")
    except SQLAlchemyError as se:
        print(f"❌ Error al crear la tabla post_likes: {se}")
        sys.exit(1)

    print("\n✅ Proceso completado. La tabla post_likes está lista.")

if __name__ == "__main__":
    main()
