# 1. Usamos una versión de Python liviana
FROM python:3.11-slim

# 2. Le decimos a Docker dónde vamos a trabajar adentro del contenedor
WORKDIR /app

# 3. Copiamos tus requerimientos y los instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Instalamos Playwright y SÓLO el navegador Chromium con sus dependencias
RUN playwright install chromium
RUN playwright install-deps chromium

# 5. Copiamos todo el resto de tu código (main.py, web_scrp.py, templates, etc.)
COPY . .

# 6. El comando final para prender el motor
CMD ["python", "main.py"]