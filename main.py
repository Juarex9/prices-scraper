import os
import re
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL: Optional[str] = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan credenciales de Supabase en el archivo .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

limiter = Limiter(key_func=get_remote_address)

templates = Jinja2Templates(directory="templates")

playwright_context = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global playwright_context
    print("[Startup] Validando configuración...")
    print(f"[Startup] Supabase URL: {'✓ configurada' if SUPABASE_URL else '✗ missing'}")
    print(f"[Startup] Supabase KEY: {'✓ configurada' if SUPABASE_KEY else '✗ missing'}")
    print("[Startup] API lista para recibir requests")
    yield
    print("[Shutdown] Cerrando conexiones...")
    if playwright_context:
        await playwright_context.close()
    print("[Shutdown] Completado")


app = FastAPI(
    title="Supermercados API v2.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "supabase": "connected"
        }
    }


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/buscar")
@limiter.limit("10/minute")
async def buscar_producto(request: Request, termino: str, response: Response):
    client_ip = get_remote_address(request)
    
    if not termino or not termino.strip():
        raise HTTPException(status_code=400, detail="El término de búsqueda no puede estar vacío")
    
    termino = termino.strip()
    
    if len(termino) < 2:
        raise HTTPException(status_code=400, detail="El término de búsqueda debe tener al menos 2 caracteres")
    
    if len(termino) > 100:
        raise HTTPException(status_code=400, detail="El término de búsqueda es demasiado largo")
    
    if not re.match(r'^[\w\sáéíóúüñÁÉÍÓÚÜÑ]+$', termino):
        raise HTTPException(
            status_code=400,
            detail="El término de búsqueda contiene caracteres no permitidos"
        )
    
    res_prod = supabase.table("productos_buscados").select("id").ilike("termino_busqueda", f"%{termino}%").execute()
    
    if not res_prod.data:
        return templates.TemplateResponse(
            "resultados.html",
            {"request": request, "termino": termino, "resultados": []}
        )
        
    producto_id = res_prod.data[0]['id']

    res_precios = supabase.table("historial_precios") \
        .select("precio, titulo_encontrado, url_compra, fecha_captura, precio_x_unidad, supermercados(nombre)") \
        .eq("producto_id", producto_id) \
        .order("fecha_captura", desc=True) \
        .limit(10) \
        .execute()

    resultados_limpios = []
    for item in res_precios.data:
        resultados_limpios.append({
            "supermercado_id": item['supermercados']['nombre'],
            "titulo_encontrado": item['titulo_encontrado'],
            "precio": item['precio'],
            "url_compra": item['url_compra'],
            "precio_x_unidad": item.get('precio_x_unidad', 'No informado'),
            "fecha_actualizacion": item['fecha_captura']
        })

    return templates.TemplateResponse(
        "resultados.html",
        {
            "request": request,
            "termino": termino,
            "resultados": resultados_limpios
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 400:
        return templates.TemplateResponse(
            "resultados.html",
            {
                "request": request,
                "termino": request.query_params.get("termino", ""),
                "resultados": [],
                "error": exc.detail
            }
        )
    raise exc
