import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

## Cargar el dataset (ajustar path para estar en el directorio correcto)
csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'SocialMediaUsersDataset.csv')
df = pd.read_csv(csv_path).head(1500) 

## Conexión a la base de datos
db_url = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:smaSwtowYMBPIhjBknUlhBkGTAPJFSsn@shortline.proxy.rlwy.net:27854/railway')
engine = create_engine(db_url)

## Insertar el dataset en la base de datos
columns_to_store = ['UserID', 'Name', 'Gender', 'DOB', 'Interests', 'City', 'Country']

df[columns_to_store].to_sql('social_media_users', con=engine, if_exists='replace', index=False)

## Mensaje de confirmación
print("El dataset ha sido insertado correctamente en la base de datos MySQL.")