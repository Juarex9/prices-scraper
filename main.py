from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
import uvicorn

# Importamos el nuevo orquestador asíncrono
from web_scrp import orquestador_de_busqueda 

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def mostrar_inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "resultados": None})

# ATENCIÓN ACÁ: Agregamos "async def" a la ruta
@app.post("/buscar")
async def procesar_busqueda(request: Request, producto_ingresado: str = Form(...)):
    print(f"El usuario buscó: {producto_ingresado}")
    
    # Usamos "await" porque ahora es una función asíncrona
    datos_obtenidos = await orquestador_de_busqueda(producto_ingresado)
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "resultados": datos_obtenidos, "busqueda": producto_ingresado}
    )

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=puerto)