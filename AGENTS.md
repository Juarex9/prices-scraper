# AGENTS.md - Argentine Supermarket Price Scraper

## Project Overview
Python FastAPI project that scrapes real-time product prices from Argentine supermarkets (Vea, Carrefour, ChangoMás, Dia, Jumbo) using Playwright and stores results in Supabase.

## Build & Runtime Commands

### Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### Run Application
```bash
# Start FastAPI server
python main.py

# Run scraper worker (populates Supabase database)
python scraper_worker.py
```

### Testing
- No formal test suite exists - manual testing only
- Test API: `curl http://127.0.0.1:8000/buscar?termino=leche`
- Test scraper: `python scraper_worker.py`

### Linting & Type Checking
```bash
pip install flake8 black mypy
flake8 . --max-line-length=100
black --check .
mypy .
```

## Code Style Guidelines

### General Conventions
- **Language**: Python 3.x
- **Async**: Use `async/await` for all I/O-bound operations (Playwright, database)
- **Encoding**: UTF-8
- **Comments**: Avoid adding comments unless explicitly requested

### Import Order
1. Standard library (`os`, `asyncio`, `datetime`, `urllib`)
2. Third-party (`playwright`, `fastapi`, `supabase`, `dotenv`)
3. Local imports (`from web_scrp import ...`)

```python
import os
import asyncio
import urllib.parse
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from playwright.async_api import async_playwright
from supabase import create_client, Client
```

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Functions | `snake_case` | `bloquear_recursos_pesados`, `buscar_en_vea` |
| Variables | `snake_case` | `termino_encodeado`, `resultados_vea` |
| Constants | `SCREAMING_SNAKE_CASE` | `TIMEOUT_MS = 60000`, `BATCH_SIZE = 10` |
| Classes | `PascalCase` | `Client` (from supabase) |
| Dictionary keys | `snake_case` | `producto_encontrado`, `precio_x_unidad` |

### Type Hints
- Add type hints for function parameters and return types
- Use simple types: `str`, `int`, `float`, `bool`, `list[dict]`
- Use `Optional[Type]` for nullable values
- Use `X | None` syntax for modern Python

```python
async def orquestador_de_busqueda(termino: str) -> list[dict]:
    ...

def limpiar_precio(precio_texto: str | None) -> float:
    ...

url: str | None = os.environ.get("SUPABASE_URL")
```

### Error Handling
- Use broad `try/except` blocks for I/O operations
- Always close pages in `except` blocks before returning
- Print contextual error messages with supermarket prefix

```python
try:
    await page.goto(url_busqueda, timeout=60000)
except Exception as e:
    print(f"[Vea] Error crítico: {e}")
    await page.close()
    return []
```

For critical failures (missing credentials), raise with clear message:
```python
if not url or not key:
    raise ValueError("Faltan credenciales de Supabase en el archivo .env")
```

### Formatting
- **Line length**: 100 characters maximum
- **Indentation**: 4 spaces
- **Trailing whitespace**: Avoid
- **Blank lines**: Two blank lines between top-level definitions

## Key Patterns

### Playwright Page Management
- Always close pages in `except` blocks or use `finally`
- Use `route()` for blocking heavy resources
- Handle timeouts gracefully with try/except

```python
async def buscar_en_vea(termino, context):
    page = await context.new_page()
    await page.route("**/*", bloquear_recursos_pesados)
    
    try:
        await page.goto(url_busqueda, timeout=TIMEOUT_GOTO)
        await page.wait_for_selector(selector, timeout=TIMEOUT_SELECTOR)
    except Exception as e:
        print(f"[Vea] ⚠ Timeout: {e}")
        await page.close()
        return []
    
    await page.close()
    return resultados
```

### Blocking Heavy Resources
```python
async def bloquear_recursos_pesados(route):
    if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
        await route.abort()
    else:
        await route.continue_()
```

### Price Cleaning
```python
def limpiar_precio(precio_texto: str | None) -> float:
    if not precio_texto:
        return 0.0
    texto = precio_texto.replace("$", "").replace(" ", "").replace("\xa0", "").replace("\n", "").strip()
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except:
        return 0.0
```

### Scraper Result Dictionary
```python
resultados_vea.append({
    "supermercado": "Vea",
    "producto_encontrado": titulo.strip(),
    "precio": precio_numero,
    "precio_x_unidad": precio_unidad_texto,
    "url": url_final,
    "estado": "ok"
})
```

### Environment Variables
```python
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL: str | None = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str | None = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan credenciales de Supabase en el archivo .env")
```

## Project Structure
```
.
├── main.py              # FastAPI entry point
├── web_scrp.py          # Playwright scraper engine (5 supermarket scrapers)
├── scraper_worker.py    # Supabase database population worker
├── templates/           # Jinja2 HTML templates
│   ├── index.html
│   └── resultados.html
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container configuration
├── .env                 # Environment variables (gitignored)
└── .env.example         # Template for .env
```

## Database Schema (Supabase)
- **productos_buscados**: Products to search for (`id`, `termino_busqueda`)
- **supermercados**: Supermarket definitions (`id`, `nombre`)
- **historial_precios**: Price history (`producto_id`, `supermercado_id`, `precio`, `titulo_encontrado`, `url_compra`, `precio_x_unidad`, `fecha_captura`)

## Environment Variables
```
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-key>
```

## Security Notes
- Never commit `.env` or credentials to the repository
- The scraper accesses external supermarket websites; be respectful of their terms of service
- Rate limiting is applied to the `/buscar` API endpoint
