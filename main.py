import sys
import asyncio

# --- PARCHE PARA WINDOWS + PLAYWRIGHT ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
# ----------------------------------------

from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from web_scrp import orquestador_de_busqueda

app = FastAPI(title="Buscador Precios en Vivo (v1.0)")

app = FastAPI(title="Buscador Precios en Vivo (v1.0)")

# Apuntamos a la carpeta de plantillas
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/buscar")
async def buscar_en_vivo(request: Request, termino: str):
    if not termino or len(termino.strip()) < 2:
        raise HTTPException(status_code=400, detail="Ingresá un término válido.")
    
    termino_limpio = termino.strip().lower()
    print(f"[API] Iniciando scraping en vivo para: '{termino_limpio}'")
    
    try:
        # Llamamos al scraper en vivo
        resultados_reales = await orquestador_de_busqueda(termino_limpio)
        
        # Renderizamos la vista con los resultados frescos
        return templates.TemplateResponse("resultados.html", {
            "request": request,
            "termino": termino_limpio,
            "resultados": resultados_reales
        })
        
    except Exception as e:
        print(f"[Error] {e}")
        raise HTTPException(status_code=500, detail="Error en el servidor.")