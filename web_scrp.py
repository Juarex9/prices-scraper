import asyncio
import sys
import urllib.parse
from playwright.async_api import async_playwright

# Parche para Windows + Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

TIMEOUT_GOTO = 40000
TIMEOUT_SELECTOR = 15000

async def bloquear_recursos_pesados(route):
    if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
        await route.abort()
    else:
        await route.continue_()

def limpiar_precio(precio_texto):
    if not precio_texto:
        return 0.0
    texto = precio_texto.replace("$", "").replace(" ", "").replace("\xa0", "").replace("\n", "").strip()
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except:
        return 0.0

async def buscar_en_vea(termino, context):
    print(f"[Vea] Iniciando búsqueda: '{termino}'...")
    page = await context.new_page()
    await page.route("**/*", bloquear_recursos_pesados)
    
    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://www.vea.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados = []
    
    try:
        await page.goto(url_busqueda, timeout=TIMEOUT_GOTO)
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        
        await page.wait_for_selector(selector_tarjetas, timeout=TIMEOUT_SELECTOR)
        tarjetas = await page.locator(selector_tarjetas).all()
        
        for tarjeta in tarjetas[:5]: # Límite de 5 para que la demo vuele
            titulo_el = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            precio_el = tarjeta.locator(".vtex-product-price-1-x-currencyContainer, #priceContainer").first
            
            if await titulo_el.count() > 0 and await precio_el.count() > 0:
                titulo = await titulo_el.first.text_content()
                precio_texto = await precio_el.text_content()
                
                try:
                    unidad_el = tarjeta.locator(".vtex-custom-unit-price")
                    precio_unidad = await unidad_el.first.text_content() if await unidad_el.count() > 0 else "No informado"
                except:
                    precio_unidad = "No informado"
                
                url_relativa = await tarjeta.get_attribute("href")
                url_final = f"https://www.vea.com.ar{url_relativa}" if url_relativa else url_busqueda
                
                resultados.append({
                    "supermercado": "Vea",
                    "titulo": titulo.strip(), # Llave corregida para Jinja2
                    "precio": limpiar_precio(precio_texto),
                    "precio_x_unidad": precio_unidad.replace("\n", " ").strip(),
                    "url": url_final
                })
                
        await page.close()
        return resultados
    except Exception as e:
        print(f"[Vea] ⚠ Error o Timeout: {e}")
        await page.close()
        return []

async def buscar_en_carrefour(termino, context):
    print(f"[Carrefour] Iniciando búsqueda: '{termino}'...")
    page = await context.new_page()
    await page.route("**/*", bloquear_recursos_pesados)
    
    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://www.carrefour.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados = []
    
    try:
        await page.goto(url_busqueda, timeout=TIMEOUT_GOTO)
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        
        await page.wait_for_selector(selector_tarjetas, timeout=TIMEOUT_SELECTOR)
        tarjetas = await page.locator(selector_tarjetas).all()
        
        for tarjeta in tarjetas[:5]:
            titulo_el = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            precio_el = tarjeta.locator(".valtech-carrefourar-product-price-0-x-currencyContainer")
            
            if await titulo_el.count() > 0 and await precio_el.count() > 0:
                titulo = await titulo_el.first.text_content()
                precio_texto = await precio_el.first.text_content()
                
                try:
                    unidad_el = tarjeta.locator(".valtech-carrefourar-dynamic-weight-price-0-x-currencyContainer")
                    precio_unidad = await unidad_el.first.text_content() if await unidad_el.count() > 0 else "No informado"
                except:
                    precio_unidad = "No informado"
                
                url_relativa = await tarjeta.get_attribute("href")
                url_final = f"https://www.carrefour.com.ar{url_relativa}" if url_relativa else url_busqueda
                
                resultados.append({
                    "supermercado": "Carrefour",
                    "titulo": titulo.strip(),
                    "precio": limpiar_precio(precio_texto),
                    "precio_x_unidad": precio_unidad.replace("\n", " ").strip(),
                    "url": url_final
                })
                
        await page.close()
        return resultados
    except Exception as e:
        print(f"[Carrefour] ⚠ Error o Timeout: {e}")
        await page.close()
        return []

async def buscar_en_changomas(termino, context):
    print(f"[ChangoMás] Iniciando búsqueda: '{termino}'...")
    page = await context.new_page()
    await page.route("**/*", bloquear_recursos_pesados)
    
    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://www.masonline.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados = []
    
    try:
        await page.goto(url_busqueda, timeout=TIMEOUT_GOTO)
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        
        await page.wait_for_selector(selector_tarjetas, timeout=TIMEOUT_SELECTOR)
        tarjetas = await page.locator(selector_tarjetas).all()
        
        for tarjeta in tarjetas[:5]:
            titulo_el = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            precio_el = tarjeta.locator(".valtech-gdn-dynamic-product-1-x-currencyContainer")
            
            if await titulo_el.count() > 0 and await precio_el.count() > 0:
                titulo = await titulo_el.first.text_content()
                precio_texto = await precio_el.first.text_content()
                
                url_relativa = await tarjeta.get_attribute("href")
                url_final = f"https://www.masonline.com.ar{url_relativa}" if url_relativa else url_busqueda
                
                resultados.append({
                    "supermercado": "ChangoMás",
                    "titulo": titulo.strip(),
                    "precio": limpiar_precio(precio_texto),
                    "precio_x_unidad": "No informado",
                    "url": url_final
                })
                
        await page.close()
        return resultados
    except Exception as e:
        print(f"[ChangoMás] ⚠ Error o Timeout: {e}")
        await page.close()
        return []

async def buscar_en_dia(termino, context):
    print(f"[Dia] Iniciando búsqueda: '{termino}'...")
    page = await context.new_page()
    await page.route("**/*", bloquear_recursos_pesados)

    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://diaonline.supermercadosdia.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados = []
    
    try:
        await page.goto(url_busqueda, timeout=TIMEOUT_GOTO)
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        
        await page.wait_for_selector(selector_tarjetas, timeout=TIMEOUT_SELECTOR)
        tarjetas = await page.locator(selector_tarjetas).all()
        
        for tarjeta in tarjetas[:5]:
            titulo_el = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            precio_el = tarjeta.locator(".diaio-store-5-x-sellingPriceValue")
            
            if await titulo_el.count() > 0 and await precio_el.count() > 0:
                titulo = await titulo_el.first.text_content()
                precio_texto = await precio_el.first.text_content()
                
                url_relativa = await tarjeta.get_attribute("href")
                url_final = f"https://diaonline.supermercadosdia.com.ar{url_relativa}" if url_relativa else url_busqueda
                
                resultados.append({
                    "supermercado": "Dia",
                    "titulo": titulo.strip(),
                    "precio": limpiar_precio(precio_texto),
                    "precio_x_unidad": "No informado",
                    "url": url_final
                })
                
        await page.close()
        return resultados
    except Exception as e:
        print(f"[Dia] ⚠ Error o Timeout: {e}")
        await page.close()
        return []

async def buscar_en_jumbo(termino, context):
    print(f"[Jumbo] Iniciando búsqueda: '{termino}'...")
    page = await context.new_page()
    await page.route("**/*", bloquear_recursos_pesados)

    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://www.jumbo.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados = []
    
    try:
        await page.goto(url_busqueda, timeout=TIMEOUT_GOTO)
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        
        await page.wait_for_selector(selector_tarjetas, timeout=TIMEOUT_SELECTOR)
        tarjetas = await page.locator(selector_tarjetas).all()
        
        for tarjeta in tarjetas[:5]:
            titulo_el = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            precio_el = tarjeta.locator(".vtex-price-format-gallery")
            
            if await titulo_el.count() > 0 and await precio_el.count() > 0:
                titulo = await titulo_el.first.text_content()
                precio_texto = await precio_el.first.text_content()
                
                try:
                    unidad_el = tarjeta.locator(".vtex-custom-unit-price")
                    precio_unidad = await unidad_el.first.text_content() if await unidad_el.count() > 0 else "No informado"
                except:
                    precio_unidad = "No informado"
                
                url_relativa = await tarjeta.get_attribute("href")
                url_final = f"https://www.jumbo.com.ar{url_relativa}" if url_relativa else url_busqueda
                
                resultados.append({
                    "supermercado": "Jumbo",
                    "titulo": titulo.strip(),
                    "precio": limpiar_precio(precio_texto),
                    "precio_x_unidad": precio_unidad.replace("\n", " ").strip(),
                    "url": url_final
                })
                
        await page.close()
        return resultados
    except Exception as e:
        print(f"[Jumbo] ⚠ Error o Timeout: {e}")
        await page.close()
        return []

async def orquestador_de_busqueda(termino):
    print(f"\n{'='*60}")
    print(f"[ORQUESTADOR] Buscando: '{termino.upper()}'")
    print(f"{'='*60}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        print("[ORQUESTADOR] Iniciando búsquedas en paralelo...")
        
        tanda_1 = await asyncio.gather(
            buscar_en_carrefour(termino, context),
            buscar_en_changomas(termino, context),
            buscar_en_vea(termino, context),
            buscar_en_dia(termino, context),
            buscar_en_jumbo(termino, context),
            return_exceptions=True
        )
        
        supermercados_nombres = ["Carrefour", "ChangoMás", "Vea", "Dia", "Jumbo"]
        resultados_totales = []
        
        print(f"\n{'='*60}")
        print("[RESUMEN DE EXTRACCIÓN]")
        print(f"{'='*60}")
        
        for i, (nombre, resultado) in enumerate(zip(supermercados_nombres, tanda_1)):
            if isinstance(resultado, Exception):
                print(f"[{nombre}] ✗ EXCEPCIÓN: {resultado}")
            elif isinstance(resultado, list):
                print(f"[{nombre}] ✓ {len(resultado)} productos")
                resultados_totales.extend(resultado)
            else:
                print(f"[{nombre}] ✗ Resultado inesperado: {type(resultado)}")
        
        print(f"{'='*60}")
        print(f"TOTAL: {len(resultados_totales)} productos encontrados")
        print(f"{'='*60}\n")
        
        await browser.close()
        
        # Filtramos precios en 0 y ordenamos por el más barato
        resultados_limpios = [r for r in resultados_totales if r.get("precio") is not None and r.get("precio") > 0]
        resultados_limpios.sort(key=lambda x: x["precio"])
        
        return resultados_limpios