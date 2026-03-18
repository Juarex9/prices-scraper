# 🛒 Argentine Supermarket Price Scraper

A high-performance, asynchronous web scraper and price comparison API built with **Python, FastAPI, and Playwright**.

This project extracts real-time product data and pricing from major retail supermarkets in Argentina (Vea, Carrefour, ChangoMás, Dia, and Jumbo) concurrently, standardizing the output into a clean, unified frontend.

## 🚀 Features

* **True Asynchronous Execution:** Utilizes `asyncio` and `async_playwright` to scrape 5 different e-commerce platforms in parallel, drastically reducing response times.
* **Lazy Loading & Popup Bypassing:** Custom wait logic and direct DOM text extraction (`text_content()`) to reliably capture data despite VTEX lazy-loaded prices, cookie banners, and location popups.
* **Data Standardization:** Cleans and parses heavily nested and inconsistent HTML price strings into standard float values.
* **Price per Unit:** Extracts and displays price per unit (e.g., $/kg, $/lt) for better comparison.
* **Real-time Comparison:** Renders a clean UI using Jinja2 templates, automatically sorting products from cheapest to most expensive across all competitors.
* **Supabase Integration:** Stores historical price data in Supabase for persistent storage and analysis.
* **Production-Ready:** Includes health checks, rate limiting, input validation, and graceful shutdown.

## 🛠️ Tech Stack

* **Backend:** Python 3.x, FastAPI, Uvicorn
* **Scraping Engine:** Playwright (Async API)
* **Database:** Supabase (PostgreSQL)
* **Frontend:** HTML5, CSS3, Jinja2 Templates
* **Rate Limiting:** SlowAPI

## ⚙️ Installation & Usage

### Prerequisites

- Python 3.10+
- Chrome/Chromium browser (installed via Playwright)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Juarex9/prices-scraper.git
   cd prices-scraper
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your Supabase credentials:
   # SUPABASE_URL=your-supabase-url
   # SUPABASE_KEY=your-supabase-key
   ```

5. Run the FastAPI server:
   ```bash
   python main.py
   ```

The application will be available at http://127.0.0.1:8000

### Run the Scraper Worker

To populate the database with price data:

```bash
python scraper_worker.py
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page with search form |
| `/buscar?termino=<product>` | GET | Search for a product and display results |
| `/health` | GET | Health check endpoint for monitoring |

### Rate Limiting

The `/buscar` endpoint is rate-limited to **10 requests per minute** per IP address.

## 🗄️ Database Schema

The project uses Supabase with the following tables:

- **productos_buscados**: Products to search for
- **supermercados**: Supermarket definitions (Vea, Carrefour, ChangoMás, Dia, Jumbo)
- **historial_precios**: Historical price records with timestamps

## 📁 Project Structure

```
.
├── main.py              # FastAPI application entry point
├── web_scrp.py          # Playwright scraper engine
├── scraper_worker.py    # Database population worker
├── templates/           # Jinja2 HTML templates
│   ├── index.html
│   └── resultados.html
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (gitignored)
├── .env.example         # Template for .env
├── AGENTS.md            # Developer documentation
└── Dockerfile           # Container configuration
```

## 🔧 Development

### Linting

```bash
pip install flake8 black mypy
flake8 . --max-line-length=100
black --check .
mypy .
```

## 🚢 Deployment

The application is configured for deployment on Render.

### Environment Variables

Set the following in your Render dashboard:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase API key

### Health Check

Configure Render's health check to: `/health`

## 📜 License

MIT License
