import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Supermercados API v2.0")

templates = Jinja2Templates(directory="templates")

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Nueva ruta para renderizar tu frontend en la raíz (/)
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
    
# Conectamos la API a Supabase en modo Solo-Lectura
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

@app.get("/buscar")
def buscar_producto(request: Request, termino: str): # <-- Agregamos request
    # 1. Buscamos si el producto existe
    res_prod = supabase.table("productos_buscados").select("id").ilike("termino_busqueda", f"%{termino}%").execute()
    
    # Manejo de error visual: Si no existe, devolvemos la vista con lista vacía
    if not res_prod.data:
         return templates.TemplateResponse(
             "resultados.html", 
             {"request": request, "termino": termino, "resultados": []}
         )
         
    producto_id = res_prod.data[0]['id']

    # 2. Traemos el historial (asegurando traer precio_x_unidad si lo agregaste a la DB)
    res_precios = supabase.table("historial_precios") \
        .select("precio, titulo_encontrado, url_compra, fecha_captura, precio_x_unidad, supermercados(nombre)") \
        .eq("producto_id", producto_id) \
        .order("fecha_captura", desc=True) \
        .limit(10) \
        .execute()

    # 3. Formateamos alineando las llaves exactas que espera nuestro HTML
    resultados_limpios = []
    for item in res_precios.data:
        resultados_limpios.append({
            "supermercado_id": item['supermercados']['nombre'], # Inyectamos el nombre real
            "titulo_encontrado": item['titulo_encontrado'],
            "precio": item['precio'],
            "url_compra": item['url_compra'],
            "precio_x_unidad": item.get('precio_x_unidad', 'No informado'),
            "fecha_actualizacion": item['fecha_captura']
        })

    # 4. Renderizamos inyectando la variable correcta
    return templates.TemplateResponse(
        "resultados.html", 
        {
            "request": request, 
            "termino": termino, 
            "resultados": resultados_limpios # <-- Variable corregida
        }
    )