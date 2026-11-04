# 🚀 Guía Rápida de Despliegue en Render

## ✅ Archivos creados para el despliegue:

- ✅ `render.yaml` - Configuración automática de Render
- ✅ `.env.example` - Plantilla de variables de entorno
- ✅ `.env` - Variables locales (NO subir a Git)
- ✅ `.gitignore` - Excluye archivos sensibles
- ✅ `Connectly/services/` - Creación automática de tablas y carga inicial del dataset
- ✅ `requirements.txt` actualizado con gunicorn y pymysql
- ✅ `app.py` actualizado para usar variables de entorno

## 📝 PASOS PARA DESPLEGAR:

### 1️⃣ Crear Base de Datos MySQL en Railway (GRATIS)

```
1. Ve a https://railway.app/
2. Crea cuenta con GitHub
3. New Project → Add MySQL
4. Copia la "MySQL Connection URL"
5. IMPORTANTE: Cambia "mysql://" por "mysql+pymysql://"
   
   Ejemplo:
   De:   mysql://root:abc@mysql.railway.app:3306/railway
   A:    mysql+pymysql://root:abc@mysql.railway.app:3306/railway
```

### 2️⃣ Tablas y datos (automático)

No hay scripts que ejecutar: al arrancar, la app crea las tablas faltantes y carga el dataset
(`data/SocialMediaUsersDataset.csv`) si `social_media_users` está vacía. Solo configura `DATABASE_URL`.
Para desarrollo local, sin `DATABASE_URL` usa `mysql+pymysql://root:Nicolas20@localhost:3306/connectly`.

### 3️⃣ Subir a GitHub

```bash
# Asegúrate de tener un repositorio en GitHub
git add .
git commit -m "Preparado para Render"
git push origin main
```

### 4️⃣ Desplegar en Render

```
1. Ve a https://render.com/
2. Crea cuenta con GitHub
3. New + → Web Service
4. Conecta tu repositorio
5. Configuración:
   
   Build Command:
   pip install -r Connectly/requirements.txt
   
   Start Command:
   cd Connectly && gunicorn --worker-class gthread --threads 100 -w 1 --bind 0.0.0.0:$PORT app:app
   
6. Variables de Entorno (Add Environment Variable):
   - DATABASE_URL: (tu URL de Railway con mysql+pymysql://)
   - SECRET_KEY: (genera una en https://randomkeygen.com/)
   - PYTHON_VERSION: 3.11.0

7. Create Web Service
8. Espera 5-10 minutos
```

### 5️⃣ Acceder a tu App

```
Tu app estará en: https://tu-app.onrender.com

Usuario admin:
- Email: admin
- Password: admin
```

## ⚠️ IMPORTANTE - Plan Gratuito:

- 🛌 La app se DUERME después de 15 min sin uso
- ⏰ Tarda 30-60 segundos en despertar
- 💾 Las imágenes subidas se BORRAN al reiniciar
- 📊 Suficiente para portafolio y demos

## 🔄 Para actualizar la app:

```bash
git add .
git commit -m "Actualización"
git push origin main
# Render desplegará automáticamente
```

## 🆘 Solución de Problemas:

**Error: "Table doesn't exist"**
Revisa los logs de arranque: `bootstrap_database` crea las tablas solo si la conexión funciona.

**Error: "Can't connect to database"**
- Verifica que DATABASE_URL tenga el formato correcto
- Debe usar "mysql+pymysql://" no "mysql://"

**La app no despierta:**
- Revisa los logs en Render Dashboard
- Verifica que el Start Command sea correcto

## 💡 Mejoras Futuras:

Para producción real:
- ✅ Render Paid Plan ($7/mes) - Sin hibernación
- ✅ Cloudinary - Para almacenar imágenes permanentemente
- ✅ Custom domain - Tu propio dominio

## 📞 Recursos:

- Railway: https://railway.app/
- Render: https://render.com/
- Cloudinary: https://cloudinary.com/
- Documentación Render: https://render.com/docs
