import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client

from web_scrp import orquestador_de_busqueda

load_dotenv()

SUPABASE_URL: Optional[str] = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan credenciales de Supabase en el archivo .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BATCH_SIZE: int = 10


async def main():
    print(f"[Worker] Iniciando proceso de extracción - {datetime.now().isoformat()}")
    start_time = asyncio.get_event_loop().time()
    
    res_productos = supabase.table("productos_buscados").select("id, termino_busqueda").execute()
    productos = res_productos.data
    
    if not productos:
        print("[Worker] No hay productos para buscar")
        return
    
    print(f"[Worker] Productos a procesar: {len(productos)}")
    
    res_supers = supabase.table("supermercados").select("id, nombre").execute()
    supermercados_db = {s['nombre'].lower(): s['id'] for s in res_supers.data}
    
    for producto in productos:
        termino = producto['termino_busqueda']
        prod_id = producto['id']
        
        print(f"\n[Worker] Procesando: {termino.upper()}")
        
        try:
            resultados_reales = await orquestador_de_busqueda(termino)
        except Exception as e:
            print(f"[Worker] Error en {termino}: {e}")
            continue
        
        if not resultados_reales:
            print(f"[Worker] Sin resultados para: {termino}")
            continue
        
        data_batch = []
        for res in resultados_reales:
            sup_nombre = res.get('supermercado', '').lower()
            
            if sup_nombre in supermercados_db:
                data_batch.append({
                    "producto_id": prod_id,
                    "supermercado_id": supermercados_db[sup_nombre],
                    "precio": res.get('precio'),
                    "titulo_encontrado": res.get('titulo', 'Sin titulo'),
                    "url_compra": res.get('url', ''),
                    "precio_x_unidad": res.get('precio_x_unidad', 'No informado'),
                    "fecha_captura": datetime.utcnow().isoformat()
                })
        
        if data_batch:
            for i in range(0, len(data_batch), BATCH_SIZE):
                batch = data_batch[i:i + BATCH_SIZE]
                supabase.table("historial_precios").insert(batch).execute()
                print(f"[Worker] Insertados {len(batch)} registros")
    
    # --- RUTINA DE LIMPIEZA ---
    dias_retencion = 3
    limite_borrado = (datetime.utcnow() - timedelta(days=dias_retencion)).isoformat()

    try:
        print(f"\n[Worker] Iniciando limpieza de registros anteriores a {dias_retencion} días...")
        # Ejecutamos el DELETE en Supabase
        respuesta = supabase.table("historial_precios").delete().lt("fecha_captura", limite_borrado).execute()
        print(f"[Worker] Limpieza completada con éxito. Registros antiguos eliminados.")
    except Exception as e:
        print(f"[Worker] Error durante la limpieza: {e}")

    # --- FINALIZACIÓN ---
    elapsed = asyncio.get_event_loop().time() - start_time
    print(f"\n[Worker] Finalizado en {elapsed:.1f} segundos")


if __name__ == "__main__":
    asyncio.run(main())