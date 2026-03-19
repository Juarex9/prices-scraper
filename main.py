import os
import re
import sys
import asyncio
import hashlib
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
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

load_dotenv()

limiter = Limiter(key_func=get_remote_address)
templates = Jinja2Templates(directory="templates")
executor = ThreadPoolExecutor(max_workers=2)


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


def ejecutar_scraper(termino: str) -> list:
    from web_scrp import orquestador_de_busqueda
    if sys.platform == "win32":
        loop = asyncio.SelectorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(orquestador_de_busqueda(termino))
    finally:
        loop.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Startup] Cache TTL: 5 minutos")
    print("[Startup] API lista para recibir requests")
    yield
    print("[Shutdown] Cerrando conexiones...")
    cache.clear()
    executor.shutdown(wait=False)


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
        "cache_size": len(cache.cache)
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

    loop = asyncio.get_event_loop()
    resultados_raw = await loop.run_in_executor(executor, ejecutar_scraper, termino)

    resultados = []
    if resultados_raw:
        for item in resultados_raw:
            resultados.append({
                "supermercado_id": item.get('supermercado', 'Unknown'),
                "titulo_encontrado": item.get('producto_encontrado', ''),
                "precio": item.get('precio', 0),
                "url_compra": item.get('url', ''),
                "precio_x_unidad": item.get('precio_x_unidad', 'No informado'),
                "fecha_actualizacion": datetime.utcnow().isoformat()
            })

    cache.set(cache_key, {"resultados": resultados})

    return templates.TemplateResponse(
        "resultados.html",
        {
            "request": request,
            "termino": termino,
            "resultados": resultados
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
