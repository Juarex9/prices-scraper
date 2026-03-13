import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# IMPORTANTE: Importamos tu motor real desde tu archivo web_scrp.py
from web_scrp import orquestador_de_busqueda

# 1. Cargar configuración de base de datos
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Faltan credenciales de Supabase en el archivo .env")

supabase: Client = create_client(url, key)

async def main():
    print("[Worker] Iniciando proceso de extracción automatizada...")
    
    # 2. Leer qué productos buscar (nuestra canasta básica)
    res_productos = supabase.table("productos_buscados").select("*").execute()
    productos = res_productos.data
    
    # 3. Leer los supermercados para mapear los IDs
    res_supers = supabase.table("supermercados").select("*").execute()
    supermercados_db = {s['nombre'].lower(): s['id'] for s in res_supers.data}

    # 4. Iterar sobre la canasta y ejecutar el motor real
    for producto in productos:
        termino = producto['termino_busqueda']
        prod_id = producto['id']
        
        print(f"\n=======================================")
        print(f"Buscando en tiempo real: {termino.upper()}")
        print(f"=======================================")
        
        # ACA OCURRE LA MAGIA: Llamamos a tu código asíncrono optimizado
        try:
            resultados_reales = await orquestador_de_busqueda(termino)
        except Exception as e:
            print(f"[Error] Falló la búsqueda de {termino}: {e}")
            continue # Si falla un producto, que siga con el próximo, no rompemos todo
        
        # 5. Guardar los resultados reales en el historial
        print(f"\n[Worker] Guardando {len(resultados_reales)} precios en la base de datos...")
        
        for res in resultados_reales:
            # Asegurate de que las keys ('supermercado', 'precio', 'titulo', 'url') 
            # coincidan con las que devuelve tu función buscar_en_...
            sup_nombre = res.get('supermercado', '').lower()
            
            if sup_nombre in supermercados_db:
                data_insert = {
                    "producto_id": prod_id,
                    "supermercado_id": supermercados_db[sup_nombre],
                    "precio": res.get('precio'),
                    "titulo_encontrado": res.get('titulo', 'Sin titulo'),
                    "url_compra": res.get('url', '')
                }
                
                # Insertamos fila por fila
                supabase.table("historial_precios").insert(data_insert).execute()
                print(f" -> OK: {res['supermercado']} - ${res['precio']}")

    print("\n[Worker] Tarea finalizada con éxito.")

if __name__ == "__main__":
    asyncio.run(main())