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

    create_table_sql = text("""
    CREATE TABLE IF NOT EXISTS messages (
      message_id   INT           NOT NULL AUTO_INCREMENT,
      sender_id    BIGINT        NOT NULL,
      receiver_id  BIGINT        NOT NULL,
      content      TEXT          NULL,
      image        VARCHAR(255)  NULL,
      sent_at      DATETIME      NOT NULL,
      PRIMARY KEY (message_id),
      INDEX idx_messages_sender (sender_id),
      INDEX idx_messages_receiver (receiver_id),
      CONSTRAINT fk_messages_sender
        FOREIGN KEY (sender_id)
        REFERENCES social_media_users(UserID)
        ON DELETE CASCADE,
      CONSTRAINT fk_messages_receiver
        FOREIGN KEY (receiver_id)
        REFERENCES social_media_users(UserID)
        ON DELETE CASCADE
    ) ENGINE=InnoDB
      DEFAULT CHARSET=utf8mb4
      COLLATE=utf8mb4_unicode_ci;
    """)

    try:
        with engine.connect() as conn:
            conn.execute(create_table_sql)
            print("✔ Tabla 'messages' creada o ya existía.")
    except ProgrammingError as pe:
        print(f"❌ Error de programación al crear la tabla messages: {pe}")
        sys.exit(1)
    except SQLAlchemyError as se:
        print(f"❌ Error al conectar o ejecutar DDL para messages: {se}")
        sys.exit(1)

    print("\n🎉 La tabla 'messages' está lista para usarse.")

if __name__ == '__main__':
    main()
