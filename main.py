import os
from fastapi import FastAPI, HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Supermercados API v2.0")

# Conectamos la API a Supabase en modo Solo-Lectura
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

@app.get("/buscar")
def buscar_producto(termino: str):
    # 1. Buscamos si el producto existe en nuestro catálogo
    res_prod = supabase.table("productos_buscados").select("id").ilike("termino_busqueda", f"%{termino}%").execute()
    
    if not res_prod.data:
         raise HTTPException(status_code=404, detail="Producto no trackeado en la base de datos actual.")
         
    producto_id = res_prod.data[0]['id']

    # 2. Traemos el historial más reciente de ese producto, cruzando datos con la tabla supermercados
    # Supabase nos permite hacer un "JOIN" implícito pidiendo supermercados(nombre)
    res_precios = supabase.table("historial_precios") \
        .select("precio, titulo_encontrado, url_compra, fecha_captura, supermercados(nombre)") \
        .eq("producto_id", producto_id) \
        .order("fecha_captura", desc=True) \
        .limit(10) \
        .execute()

    # 3. Formateamos la respuesta limpia para el frontend
    resultados_limpios = []
    for item in res_precios.data:
        resultados_limpios.append({
            "supermercado": item['supermercados']['nombre'],
            "titulo": item['titulo_encontrado'],
            "precio": item['precio'],
            "url": item['url_compra'],
            "fecha_actualizacion": item['fecha_captura']
        })

    return {"producto": termino, "resultados": resultados_limpios}