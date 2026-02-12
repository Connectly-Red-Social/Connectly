"""
Script para copiar los archivos JS necesarios de PyVis a la carpeta storage
"""
import os
import shutil
from pathlib import Path

# Definir rutas
current_dir = Path(__file__).parent
storage_dir = current_dir / 'storage'
lib_dir = current_dir.parent / 'lib'

# Crear directorios necesarios en storage
lib_storage = storage_dir / 'lib'
bindings_storage = lib_storage / 'bindings'
vis_storage = lib_storage / 'vis-9.1.2'

os.makedirs(bindings_storage, exist_ok=True)
os.makedirs(vis_storage, exist_ok=True)

print("📁 Copiando archivos JavaScript para PyVis...")

try:
    # Copiar utils.js
    utils_src = lib_dir / 'bindings' / 'utils.js'
    utils_dst = bindings_storage / 'utils.js'
    
    if utils_src.exists():
        shutil.copy2(utils_src, utils_dst)
        print(f"✅ {utils_src} → {utils_dst}")
    else:
        print(f"❌ No se encontró {utils_src}")
    
    # Copiar archivos vis-network
    for file_name in ['vis-network.min.js', 'vis-network.css']:
        vis_src = lib_dir / 'vis-9.1.2' / file_name
        vis_dst = vis_storage / file_name
        
        if vis_src.exists():
            shutil.copy2(vis_src, vis_dst)
            print(f"✅ {vis_src} → {vis_dst}")
        else:
            print(f"❌ No se encontró {vis_src}")
    
    print("\n🎉 Archivos copiados correctamente!")
    print("Ahora el admin graph debería funcionar sin errores de JavaScript.")
    
except Exception as e:
    print(f"❌ Error al copiar archivos: {e}")