# create_columns.py
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Configuración de conexión (ajusta usuario/contraseña si es necesario)
DB_URL = 'mysql+mysqlconnector://root:Nicolas20@localhost:3306/connectly'


def main():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        for col_name, col_def in [
            ('username',      'VARCHAR(100) NULL AFTER Country'),
            ('password',      'VARCHAR(100) NULL AFTER username'),
            ('profile_image', 'VARCHAR(255) NULL AFTER password')
        ]:
            try:
                conn.execute(text(f"ALTER TABLE social_media_users ADD COLUMN {col_name} {col_def};"))
                print(f"✔ Columna '{col_name}' creada.")
            except ProgrammingError as e:
                # Código 1060: Duplicate column name
                if 'Duplicate column name' in str(e):
                    print(f"ℹ Columna '{col_name}' ya existe, se omite.")
                else:
                    print(f"❌ Error al crear la columna '{col_name}': {e}")
                    sys.exit(1)

    print("\n🌟 Todas las columnas fueron procesadas.")


if __name__ == '__main__':
    main()
