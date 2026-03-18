import asyncio
from playwright.async_api import async_playwright
import urllib.parse

async def bloquear_recursos_pesados(route):
    # Si lo que intenta descargar es una imagen, estilo, fuente de texto o video, lo bloqueamos
    if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
        await route.abort()
    else:
        # Si es HTML o datos de la API, lo dejamos pasar
        await route.continue_()

def limpiar_precio(precio_texto):
    if not precio_texto: return 0.0
    # Sumamos replace("\n", "") por si text_content() trae saltos de línea
    texto = precio_texto.replace("$", "").replace(" ", "").replace("\xa0", "").replace("\n", "").strip()
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except:
        return 0.0

async def buscar_en_vea(termino, context):
    print(f"[Vea] Buscando en grilla: '{termino}'...")
    page = await context.new_page() 
    await page.route("**/*", bloquear_recursos_pesados)
    
    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://www.vea.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    
    resultados_vea = []
    
    try:
        await page.goto(url_busqueda, timeout=60000)
        
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        
        try:
            await page.wait_for_selector(selector_tarjetas, timeout=15000)
            await page.wait_for_selector("#priceContainer", timeout=15000)
            await page.wait_for_timeout(2000) 
        except:
            print(f"[Vea] No cargaron las tarjetas o los precios a tiempo.")
            await page.close()
            return []
        
        tarjetas = await page.locator(selector_tarjetas).all()
        palabras_buscadas = termino.lower().split()
        
        # --- CAMBIO CLAVE 1: Limitamos a procesar solo 7 tarjetas ---
        productos_agregados = 0
        
        for tarjeta in tarjetas:
            if productos_agregados >= 7:
                break # Si ya tenemos 7, salimos del bucle
            
            titulo_elemento = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            
            if await titulo_elemento.count() > 0:
                titulo = await titulo_elemento.first.text_content()
                titulo_minuscula = titulo.strip().lower() if titulo else ""
                
                if all(palabra in titulo_minuscula for palabra in palabras_buscadas):
                    
                    precio_elemento = tarjeta.locator("#priceContainer")
                    
                    if await precio_elemento.count() > 0:
                        precio_texto = await precio_elemento.first.text_content()
                        precio_numero = limpiar_precio(precio_texto)
                        
                        # --- CAMBIO CLAVE 2: Buscar el precio por unidad ---
                        # Usamos la clase general de VTEX para el precio por medida.
                        # Vas a tener que confirmar si esta es la clase correcta en Vea.
                        precio_unidad_elemento = tarjeta.locator(".vtex-custom-unit-price")
                        if await precio_unidad_elemento.count() > 0:
                            precio_unidad_texto = await precio_unidad_elemento.first.text_content()
                        else:
                            precio_unidad_texto = "No informado"
                        
                        url_relativa = await tarjeta.get_attribute("href")
                        url_final = f"https://www.vea.com.ar{url_relativa}" if url_relativa else url_busqueda
                        
                        resultados_vea.append({
                            "supermercado": "Vea",
                            "producto_encontrado": titulo.strip(),
                            "precio": precio_numero,
                            "precio_x_unidad": precio_unidad_texto, # Guardamos el nuevo dato
                            "url": url_final,
                            "estado": "ok"
                        })
                        
                        # Incrementamos el contador solo si encontramos un precio válido
                        productos_agregados += 1 
        
        await page.close()
        
        if not resultados_vea:
            print(f"[Vea] DESCARTADO: Ningún producto en la grilla coincidió.")
            
        return resultados_vea
        
    except Exception as e:
        print(f"[Vea] Error crítico: {e}")
        await page.close()
        return []
            

async def buscar_en_carrefour(termino, context):
    print(f"[Carrefour] Buscando en grilla: '{termino}'...")
    page = await context.new_page() 
    await page.route("**/*", bloquear_recursos_pesados)
    
    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://www.carrefour.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados_carrefour = []
    
    try:
        await page.goto(url_busqueda, timeout=60000)
        await page.wait_for_timeout(3000) 
        
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        await page.wait_for_selector(selector_tarjetas, timeout=15000)
        tarjetas = await page.locator(selector_tarjetas).all()
        palabras_buscadas = termino.lower().split()
        
        for tarjeta in tarjetas:
            titulo_elemento = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            if await titulo_elemento.count() > 0:
                # LA MAGIA NUEVA: text_content() ignora los popups que tapan la pantalla
                titulo = await titulo_elemento.first.text_content()
                titulo_minuscula = titulo.strip().lower() if titulo else ""
                
                if all(palabra in titulo_minuscula for palabra in palabras_buscadas):
                    # Usamos la clase exacta que descubriste en la captura
                    precio_elemento = tarjeta.locator(".valtech-carrefourar-product-price-0-x-currencyContainer")
                    
                    if await precio_elemento.count() > 0:
                        precio_texto = await precio_elemento.first.text_content()
                        precio_numero = limpiar_precio(precio_texto)
                        
                        url_relativa = await tarjeta.get_attribute("href")
                        url_final = f"https://www.carrefour.com.ar{url_relativa}" if url_relativa else url_busqueda
                        
                        resultados_carrefour.append({
                            "supermercado": "Carrefour",
                            "producto_encontrado": titulo.strip(),
                            "precio": precio_numero,
                            "url": url_final,
                            "estado": "ok"
                        })
        await page.close()
        if not resultados_carrefour:
            print(f"[Carrefour] DESCARTADO: Ningún producto en la grilla coincidió.")
        return resultados_carrefour
    except Exception as e:
        print(f"[Carrefour] Error o timeout: {e}")
        await page.close()
        return []


async def buscar_en_changomas(termino, context):
    print(f"[ChangoMás] Buscando en grilla: '{termino}'...")
    page = await context.new_page()
    await page.route("**/*", bloquear_recursos_pesados)
    
    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://www.masonline.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados_changomas = []
    
    try:
        await page.goto(url_busqueda, timeout=60000)
        
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        try:
            # Esperamos que cargue la tarjeta
            await page.wait_for_selector(selector_tarjetas, timeout=20000)
            
            # EL TRUCO: Esperamos también que aparezca AL MENOS UN PRECIO antes de avanzar
            await page.wait_for_selector(".valtech-gdn-dynamic-product-1-x-currencyContainer", timeout=15000)
            
            # Un descansito extra por las dudas
            await page.wait_for_timeout(3000)
        except:
            await page.close()
            return []
            
        tarjetas = await page.locator(selector_tarjetas).all()
        palabras_buscadas = termino.lower().split()
                
        for tarjeta in tarjetas:
            titulo_elemento = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            if await titulo_elemento.count() > 0:
                titulo = await titulo_elemento.first.text_content()
                titulo_minuscula = titulo.strip().lower() if titulo else ""
                
                if all(palabra in titulo_minuscula for palabra in palabras_buscadas):
                    precio_elemento = tarjeta.locator(".valtech-gdn-dynamic-product-1-x-currencyContainer")
                    
                    if await precio_elemento.count() > 0:
                        precio_texto = await precio_elemento.first.text_content()
                        precio_numero = limpiar_precio(precio_texto)
                        url_relativa = await tarjeta.get_attribute("href")
                        url_final = f"https://www.masonline.com.ar{url_relativa}" if url_relativa else url_busqueda
                        
                        resultados_changomas.append({
                            "supermercado": "ChangoMás",
                            "producto_encontrado": titulo.strip(),
                            "precio": precio_numero,
                            "url": url_final,
                            "estado": "ok"
                        })
                    else:
                        print(f"     ❌ Coincidió el nombre, pero NO encontró el precio HTML.")
        
        await page.close()
        if not resultados_changomas:
            print(f"[ChangoMás] DESCARTADO: Ningún producto terminó en la lista final.")
        return resultados_changomas
    except Exception as e:
        print(f"[ChangoMás] Error crítico: {e}")
        await page.close()
        return []

async def buscar_en_dia(termino, context):
    print(f"[Dia] Buscando en grilla: '{termino}'...")
    page = await context.new_page() 
    await page.route("**/*", bloquear_recursos_pesados)

    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://diaonline.supermercadosdia.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados_dia = []
    
    try:
        await page.goto(url_busqueda, timeout=60000)
        
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        try:
            await page.wait_for_selector(selector_tarjetas, timeout=15000)
            # Esperamos la clase estándar de precios de VTEX
            await page.wait_for_selector(".diaio-store-5-x-sellingPriceValue", timeout=15000)
            await page.wait_for_timeout(2000)
        except:
            print(f"[Dia] No cargaron las tarjetas o los precios a tiempo.")
            await page.close()
            return []
            
        tarjetas = await page.locator(selector_tarjetas).all()
        palabras_buscadas = termino.lower().split()
        
        for tarjeta in tarjetas:
            titulo_elemento = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            if await titulo_elemento.count() > 0:
                titulo = await titulo_elemento.first.text_content()
                titulo_minuscula = titulo.strip().lower() if titulo else ""
                
                if all(palabra in titulo_minuscula for palabra in palabras_buscadas):
                    precio_elemento = tarjeta.locator(".diaio-store-5-x-sellingPriceValue")
                    
                    if await precio_elemento.count() > 0:
                        precio_texto = await precio_elemento.first.text_content()
                        precio_numero = limpiar_precio(precio_texto)
                        
                        url_relativa = await tarjeta.get_attribute("href")
                        url_final = f"https://diaonline.supermercadosdia.com.ar{url_relativa}" if url_relativa else url_busqueda
                        
                        resultados_dia.append({
                            "supermercado": "Dia",
                            "producto_encontrado": titulo.strip(),
                            "precio": precio_numero,
                            "url": url_final,
                            "estado": "ok"
                        })
        
        await page.close()
        if not resultados_dia:
            print(f"[Dia] DESCARTADO: Ningún producto coincidió.")
        return resultados_dia
    except Exception as e:
        print(f"[Dia] Error crítico: {e}")
        await page.close()
        return []

async def buscar_en_jumbo(termino, context):
    print(f"[Jumbo] Buscando en grilla: '{termino}'...")
    page = await context.new_page() 
    await page.route("**/*", bloquear_recursos_pesados)

    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://www.jumbo.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"

    resultados_jumbo = []
    
    
    try:
        await page.goto(url_busqueda, timeout=60000)
        
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        
        try:
            await page.wait_for_selector(selector_tarjetas, timeout=15000)
            await page.wait_for_selector("#priceContainer", timeout=15000)
            await page.wait_for_timeout(2000) 
        except:
            print(f"[Jumbo] No cargaron las tarjetas o los precios a tiempo.")
            await page.close()
            return []
        
        tarjetas = await page.locator(selector_tarjetas).all()
        palabras_buscadas = termino.lower().split()
        
        # --- CAMBIO CLAVE 1: Limitamos a procesar solo 7 tarjetas ---
        productos_agregados = 0
        
        for tarjeta in tarjetas:
            if productos_agregados >= 7:
                break # Si ya tenemos 7, salimos del bucle
            
            titulo_elemento = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            
            if await titulo_elemento.count() > 0:
                titulo = await titulo_elemento.first.text_content()
                titulo_minuscula = titulo.strip().lower() if titulo else ""
                
                if all(palabra in titulo_minuscula for palabra in palabras_buscadas):
                    
                    precio_elemento = tarjeta.locator("#priceContainer")
                    
                    if await precio_elemento.count() > 0:
                        precio_texto = await precio_elemento.first.text_content()
                        precio_numero = limpiar_precio(precio_texto)
                        
                        # --- CAMBIO CLAVE 2: Buscar el precio por unidad ---
                        # Usamos la clase general de VTEX para el precio por medida.
                        # Vas a tener que confirmar si esta es la clase correcta en Vea.
                        precio_unidad_elemento = tarjeta.locator(".vtex-custom-unit-price")
                        if await precio_unidad_elemento.count() > 0:
                            precio_unidad_texto = await precio_unidad_elemento.first.text_content()
                        else:
                            precio_unidad_texto = "No informado"
                        
                        url_relativa = await tarjeta.get_attribute("href")
                        url_final = f"https://www.jumbo.com.ar/{url_relativa}" if url_relativa else url_busqueda
                        
                        resultados_jumbo.append({
                            "supermercado": "Vea",
                            "producto_encontrado": titulo.strip(),
                            "precio": precio_numero,
                            "precio_x_unidad": precio_unidad_texto, # Guardamos el nuevo dato
                            "url": url_final,
                            "estado": "ok"
                        })
                        
                        # Incrementamos el contador solo si encontramos un precio válido
                        productos_agregados += 1 
        
        await page.close()
        
        if not resultados_jumbo:
            print(f"[Vea] DESCARTADO: Ningún producto en la grilla coincidió.")
            
        return resultados_jumbo
        
    except Exception as e:
        print(f"[Jumbo] Error crítico: {e}")
        await page.close()
        return []

# EL ORQUESTADOR
async def orquestador_de_busqueda(termino):
    print("Iniciando motor asíncrono Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context()
        
        print("[Orquestador] Iniciando Tanda 1 (Carrefour y ChangoMás)...")
        tanda_1 = await asyncio.gather(
            buscar_en_carrefour(termino, context),
            buscar_en_changomas(termino, context)
        )
    
        print("[Orquestador] Iniciando Tanda 2 (Vea, Dia y Jumbo)...")
        tanda_2 = await asyncio.gather(
            buscar_en_vea(termino, context),
            buscar_en_dia(termino, context),
            buscar_en_jumbo(termino, context)
        )   
    
        # Unificamos todos los resultados de ambas tandas en una sola lista
        # tanda_1[0] -> Carrefour | tanda_1[1] -> ChangoMás
        # tanda_2[0] -> Vea       | tanda_2[1] -> Dia        | tanda_2[2] -> Jumbo
        resultados_totales = tanda_1[0] + tanda_1[1] + tanda_2[0] + tanda_2[1] + tanda_2[2]
    
        await browser.close()
            
        resultados_limpios = [r for r in resultados_totales if r["precio"] is not None]
        resultados_limpios.sort(key=lambda x: x["precio"])
    
        return resultados_limpios