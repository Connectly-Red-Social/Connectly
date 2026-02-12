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

    # Crear tabla comments
    create_table_sql = text("""
    CREATE TABLE IF NOT EXISTS comments (
      CommentID  INT           NOT NULL AUTO_INCREMENT,
      PostID     INT           NOT NULL,
      UserID     BIGINT        NOT NULL,
      Content    TEXT          NOT NULL,
      CommentDate DATETIME     DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (CommentID),
      INDEX idx_comments_post (PostID),
      INDEX idx_comments_user (UserID),
      CONSTRAINT fk_comments_post
        FOREIGN KEY (PostID)
        REFERENCES posts(PostID)
        ON DELETE CASCADE,
      CONSTRAINT fk_comments_user
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
            print("✔ Tabla 'comments' creada exitosamente.")
    except SQLAlchemyError as se:
        print(f"❌ Error al crear la tabla comments: {se}")
        sys.exit(1)

    print("\n✅ Proceso completado. La tabla comments está lista.")

if __name__ == "__main__":
    main()
