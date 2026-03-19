import os
import re
import time
import hashlib
from collections import OrderedDict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
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


class TTLCache:
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[dict]:
        if key in self.cache:
            entry = self.cache[key]
            if datetime.utcnow() < entry["expires"]:
                self.cache.move_to_end(key)
                return entry["data"]
            else:
                del self.cache[key]
        return None

    def set(self, key: str, data: dict) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
        self.cache[key] = {
            "data": data,
            "expires": datetime.utcnow() + timedelta(seconds=self.ttl)
        }

    def clear(self) -> None:
        self.cache.clear()


cache = TTLCache(max_size=100, ttl_seconds=300)


playwright_context = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global playwright_context
    print("[Startup] Validando configuración...")
    print(f"[Startup] Supabase URL: {'✓ configurada' if SUPABASE_URL else '✗ missing'}")
    print(f"[Startup] Supabase KEY: {'✓ configurada' if SUPABASE_KEY else '✗ missing'}")
    print("[Startup] Cache TTL: 5 minutos")
    print("[Startup] API lista para recibir requests")
    yield
    print("[Shutdown] Cerrando conexiones...")
    if playwright_context:
        await playwright_context.close()
    cache.clear()
    print("[Shutdown] Completado")


app = FastAPI(
    title="Supermercados API v2.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def get_cache_key(termino: str) -> str:
    return hashlib.md5(termino.lower().strip().encode()).hexdigest()


@app.get("/health")
async def health_check(response: Response):
    response.headers["Cache-Control"] = "no-cache"
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cache_size": len(cache.cache),
        "services": {
            "supabase": "connected"
        }
    }


@app.get("/")
def home(request: Request, response: Response):
    response.headers["Cache-Control"] = "public, max-age=3600"
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/buscar", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def buscar_producto(request: Request, termino: str, response: Response):
    if not termino or not termino.strip():
        raise HTTPException(status_code=400, detail="El término de búsqueda no puede estar vacío")
    
    termino = termino.strip().lower()
    
    if len(termino) < 2:
        raise HTTPException(status_code=400, detail="El término de búsqueda debe tener al menos 2 caracteres")
    
    if len(termino) > 100:
        raise HTTPException(status_code=400, detail="El término de búsqueda es demasiado largo")
    
    if not re.match(r'^[\w\sáéíóúüñÁÉÍÓÚÜÑ]+$', termino):
        raise HTTPException(
            status_code=400,
            detail="El término de búsqueda contiene caracteres no permitidos"
        )
    
    cache_key = get_cache_key(termino)
    cached_result = cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["Cache-Control"] = "public, max-age=300"
        return templates.TemplateResponse(
            "resultados.html",
            {
                "request": request,
                "termino": termino,
                "resultados": cached_result["resultados"],
                "cached": True
            }
        )
    
    response.headers["X-Cache"] = "MISS"
    response.headers["Cache-Control"] = "public, max-age=300"
    
    producto = supabase.table("productos_buscados").select("id").ilike("termino_busqueda", f"%{termino}%").maybe_single().execute()
    
    if not producto.data:
        cache.set(cache_key, {"resultados": []})
        return templates.TemplateResponse(
            "resultados.html",
            {"request": request, "termino": termino, "resultados": []}
        )
    
    producto_id = producto.data['id']
    
    precios_data = supabase.table("historial_precios").select(
        "precio, titulo_encontrado, url_compra, fecha_captura, precio_x_unidad, supermercados(nombre)"
    ).eq("producto_id", producto_id).order("fecha_captura", desc=True).limit(10).execute()
    
    resultados_limpios = []
    for item in precios_data.data or []:
        resultados_limpios.append({
            "supermercado_id": item.get('supermercados', {}).get('nombre', 'Unknown'),
            "titulo_encontrado": item.get('titulo_encontrado', ''),
            "precio": item.get('precio', 0),
            "url_compra": item.get('url_compra', ''),
            "precio_x_unidad": item.get('precio_x_unidad', 'No informado'),
            "fecha_actualizacion": item.get('fecha_captura', '')
        })
    
    cache.set(cache_key, {"resultados": resultados_limpios})
    
    return templates.TemplateResponse(
        "resultados.html",
        {
            "request": request,
            "termino": termino,
            "resultados": resultados_limpios
        }
    )


@app.delete("/cache")
async def clear_cache(response: Response):
    cache.clear()
    return {"status": "ok", "message": "Cache cleared"}


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
