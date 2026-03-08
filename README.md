# 🛒 Argentine Supermarket Price Scraper (MVP v1.0)

A high-performance, asynchronous web scraper and price comparison API built with **Python, FastAPI, and Playwright**. 

This project extracts real-time product data and pricing from major retail supermarkets in Argentina (Vea, Carrefour, ChangoMás, Dia, and Jumbo) concurrently, standardizing the output into a clean, unified frontend.

## 🚀 Features

* **True Asynchronous Execution:** Utilizes `asyncio` and `async_playwright` to scrape 5 different e-commerce platforms in parallel, drastically reducing response times.
* **Lazy Loading & Popup Bypassing:** Custom wait logic and direct DOM text extraction (`text_content()`) to reliably capture data despite VTEX lazy-loaded prices, cookie banners, and location popups.
* **Data Standardization:** Cleans and parses heavily nested and inconsistent HTML price strings into standard float values.
* **Real-time Comparison:** Renders a clean UI using Jinja2 templates, automatically sorting products from cheapest to most expensive across all competitors.

## 🛠️ Tech Stack

* **Backend:** Python 3.x, FastAPI, Uvicorn
* **Scraping Engine:** Playwright (Async API)
* **Frontend:** HTML5, CSS3, Jinja2 Templates

## ⚙️ Installation & Usage

1. Clone the repository:
   ```bash
   git clone [https://github.com/your-username/salta-precios-scraper.git](https://github.com/your-username/salta-precios-scraper.git)
   cd salta-precios-scraper
   
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   
4. Run the FastAPI server:
   ```bash
   python main.py
   
The application will be available at http://127.0.0.1:8000

## Roadmap (v2.0 - Coming Soon)
The next iteration of this project will evolve from a real-time scraper into a persistent data oracle powered by AI:

- [ ] Database Integration: Implement PostgreSQL to track historical price changes and inflation metrics.

- [ ] Automated CRON Jobs: Background workers to periodically update the basket of essential goods.

- [ ] AI Smart Agents: Integration with LLMs to provide intelligent product substitutions, smart shopping lists, and budget optimization based on historical data.
