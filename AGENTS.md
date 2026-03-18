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
```bash
# No formal test suite exists - manual testing only
# Test the API: curl http://127.0.0.1:8000/buscar?termino=leche
# Test the scraper: python scraper_worker.py
```

### Linting
```bash
# Install dev dependencies
pip install flake8 black mypy

# Run linters
flake8 . --max-line-length=100
black --check .
mypy .
```

## Code Style Guidelines

### General Conventions
- **Language**: Python 3.x
- **Async**: Use `async/await` for all I/O-bound operations (Playwright, database)
- **Encoding**: UTF-8

### Imports
- Standard library first, then third-party, then local
- Use explicit imports (`from module import name`)
- Group by: `asyncio` → `playwright` → `fastapi` → `supabase` → `dotenv` → local

```python
import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from playwright.async_api import async_playwright
from supabase import create_client, Client
```

### Naming Conventions
- **Functions**: `snake_case` (e.g., `bloquear_recursos_pesados`, `buscar_en_vea`)
- **Variables**: `snake_case` (e.g., `termino_encodeado`, `resultados_vea`)
- **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `TIMEOUT_MS = 60000`)
- **Classes**: `PascalCase` (rarely used in this project)
- **Dictionary keys**: `snake_case` (e.g., `producto_encontrado`, `precio_x_unidad`)

### Type Hints
- Add type hints for function parameters and return types where obvious
- Use `str`, `int`, `float`, `bool`, `list`, `dict` for simple types
- Use `Optional[Type]` for nullable values or `.get()` calls with defaults
- Current patterns in codebase:

```python
async def orquestador_de_busqueda(termino: str) -> list[dict]:
    # ...

def limpiar_precio(precio_texto: str | None) -> float:
    # ...

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
```

### Error Handling
- Use broad `try/except` blocks with specific exception handling where needed
- Print user-friendly error messages with context:

```python
try:
    await page.goto(url_busqueda, timeout=60000)
except Exception as e:
    print(f"[Vea] Error crítico: {e}")
    await page.close()
    return []
```

- For critical failures (missing credentials), raise with clear message:

```python
if not url or not key:
    raise ValueError("Faltan credenciales de Supabase en el archivo .env")
```

### Formatting
- **Line length**: ~100 characters maximum
- **Indentation**: 4 spaces
- **Trailing whitespace**: Avoid
- **Blank lines**: Two blank lines between top-level definitions

### Key Patterns

#### Playwright Page Management
- Always close pages in finally blocks or after use
- Use context managers where possible
- Handle timeouts gracefully:

```python
try:
    await page.wait_for_selector(selector, timeout=15000)
except:
    await page.close()
    return []
```

#### Dictionary Structure for Results
Follow this pattern for scraper results:

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

#### Environment Variables
- Load with `load_dotenv()` at module level
- Get values with `os.getenv()` or `os.environ.get()`
- Always validate required vars before use

## Project Structure
```
.
├── main.py              # FastAPI app entry point
├── web_scrp.py          # Playwright scraper engine
├── scraper_worker.py    # Supabase database population worker
├── templates/           # Jinja2 HTML templates
│   ├── index.html
│   └── resultados.html
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container configuration
├── .env                 # Environment variables (gitignored)
└── .env.example         # Template for .env
```

## Database (Supabase)
- **productos_buscados**: Products to search for
- **supermercados**: Supermarket definitions
- **historial_precios**: Price history records

## Environment Variables
```
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-key>
```
