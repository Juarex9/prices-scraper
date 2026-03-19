import asyncio
from playwright.async_api import async_playwright
import urllib.parse

TIMEOUT_GOTO = 90000
TIMEOUT_SELECTOR = 30000
TIMEOUT_WAIT = 3000


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
    
    resultados_vea = []
    
    try:
        print(f"[Vea] Navegando a {url_busqueda}")
        await page.goto(url_busqueda, timeout=TIMEOUT_GOTO)
        
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        
        try:
            print(f"[Vea] Esperando tarjetas...")
            await page.wait_for_selector(selector_tarjetas, timeout=TIMEOUT_SELECTOR)
            print(f"[Vea] Tarjetas encontradas, esperando precios...")
            await page.wait_for_selector("#priceContainer", timeout=TIMEOUT_SELECTOR)
            await page.wait_for_timeout(TIMEOUT_WAIT)
        except Exception as e:
            print(f"[Vea] ⚠ Timeout al esperar elementos: {e}")
            await page.close()
            return []
        
        tarjetas = await page.locator(selector_tarjetas).all()
        print(f"[Vea] Total tarjetas en grilla: {len(tarjetas)}")
        
        palabras_buscadas = termino.lower().split()
        productos_agregados = 0
        
        for i, tarjeta in enumerate(tarjetas):
            if productos_agregados >= 7:
                break
            
            titulo_elemento = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            
            if await titulo_elemento.count() > 0:
                titulo = await titulo_elemento.first.text_content()
                titulo_minuscula = titulo.strip().lower() if titulo else ""
                
                if all(palabra in titulo_minuscula for palabra in palabras_buscadas):
                    precio_elemento = tarjeta.locator("#priceContainer")
                    
                    if await precio_elemento.count() > 0:
                        precio_texto = await precio_elemento.first.text_content()
                        precio_numero = limpiar_precio(precio_texto)
                        
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
                            "precio_x_unidad": precio_unidad_texto,
                            "url": url_final,
                            "estado": "ok"
                        })
                        productos_agregados += 1
        
        await page.close()
        print(f"[Vea] ✓ Encontrados: {len(resultados_vea)} productos")
        return resultados_vea
        
    except Exception as e:
        print(f"[Vea] ✗ Error crítico: {e}")
        await page.close()
        return []


async def buscar_en_carrefour(termino, context):
    print(f"[Carrefour] Iniciando búsqueda: '{termino}'...")
    page = await context.new_page()
    await page.route("**/*", bloquear_recursos_pesados)
    
    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://www.carrefour.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados_carrefour = []
    
    try:
        print(f"[Carrefour] Navegando a {url_busqueda}")
        await page.goto(url_busqueda, timeout=TIMEOUT_GOTO)
        
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        try:
            print(f"[Carrefour] Esperando tarjetas...")
            await page.wait_for_selector(selector_tarjetas, timeout=TIMEOUT_SELECTOR)
            print(f"[Carrefour] Tarjetas encontradas, esperando precios...")
            await page.wait_for_selector("#priceContainer", timeout=TIMEOUT_SELECTOR)
            await page.wait_for_timeout(TIMEOUT_WAIT)
        except Exception as e:
            print(f"[Carrefour] ⚠ Timeout al esperar elementos: {e}")
            await page.close()
            return []
        
        tarjetas = await page.locator(selector_tarjetas).all()
        print(f"[Carrefour] Total tarjetas en grilla: {len(tarjetas)}")
        
        palabras_buscadas = termino.lower().split()
        productos_agregados = 0
        
        for tarjeta in tarjetas:
            if productos_agregados >= 7:
                break
            
            titulo_elemento = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            
            if await titulo_elemento.count() > 0:
                titulo = await titulo_elemento.first.text_content()
                titulo_minuscula = titulo.strip().lower() if titulo else ""
                
                if all(palabra in titulo_minuscula for palabra in palabras_buscadas):
                    precio_elemento = tarjeta.locator("#priceContainer")
                    
                    if await precio_elemento.count() > 0:
                        precio_texto = await precio_elemento.first.text_content()
                        precio_numero = limpiar_precio(precio_texto)
                        
                        precio_unidad_elemento = tarjeta.locator(".vtex-custom-unit-price")
                        if await precio_unidad_elemento.count() > 0:
                            precio_unidad_texto = await precio_unidad_elemento.first.text_content()
                        else:
                            precio_unidad_texto = "No informado"
                        
                        url_relativa = await tarjeta.get_attribute("href")
                        url_final = f"https://www.carrefour.com.ar{url_relativa}" if url_relativa else url_busqueda
                        
                        resultados_carrefour.append({
                            "supermercado": "Carrefour",
                            "producto_encontrado": titulo.strip(),
                            "precio": precio_numero,
                            "precio_x_unidad": precio_unidad_texto,
                            "url": url_final,
                            "estado": "ok"
                        })
                        productos_agregados += 1
        
        await page.close()
        print(f"[Carrefour] ✓ Encontrados: {len(resultados_carrefour)} productos")
        return resultados_carrefour
        
    except Exception as e:
        print(f"[Carrefour] ✗ Error crítico: {e}")
        await page.close()
        return []


async def buscar_en_changomas(termino, context):
    print(f"[ChangoMás] Iniciando búsqueda: '{termino}'...")
    page = await context.new_page()
    await page.route("**/*", bloquear_recursos_pesados)
    
    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://www.masonline.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados_changomas = []
    
    try:
        print(f"[ChangoMás] Navegando a {url_busqueda}")
        await page.goto(url_busqueda, timeout=TIMEOUT_GOTO)
        
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        try:
            print(f"[ChangoMás] Esperando tarjetas...")
            await page.wait_for_selector(selector_tarjetas, timeout=TIMEOUT_SELECTOR)
            print(f"[ChangoMás] Tarjetas encontradas, esperando precios...")
            await page.wait_for_selector("#priceContainer", timeout=TIMEOUT_SELECTOR)
            await page.wait_for_timeout(TIMEOUT_WAIT)
        except Exception as e:
            print(f"[ChangoMás] ⚠ Timeout al esperar elementos: {e}")
            await page.close()
            return []
        
        tarjetas = await page.locator(selector_tarjetas).all()
        print(f"[ChangoMás] Total tarjetas en grilla: {len(tarjetas)}")
        
        palabras_buscadas = termino.lower().split()
        productos_agregados = 0
        
        for tarjeta in tarjetas:
            if productos_agregados >= 7:
                break
            
            titulo_elemento = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            
            if await titulo_elemento.count() > 0:
                titulo = await titulo_elemento.first.text_content()
                titulo_minuscula = titulo.strip().lower() if titulo else ""
                
                if all(palabra in titulo_minuscula for palabra in palabras_buscadas):
                    precio_elemento = tarjeta.locator("#priceContainer")
                    
                    if await precio_elemento.count() > 0:
                        precio_texto = await precio_elemento.first.text_content()
                        precio_numero = limpiar_precio(precio_texto)
                        
                        precio_unidad_elemento = tarjeta.locator(".vtex-custom-unit-price")
                        if await precio_unidad_elemento.count() > 0:
                            precio_unidad_texto = await precio_unidad_elemento.first.text_content()
                        else:
                            precio_unidad_texto = "No informado"
                        
                        url_relativa = await tarjeta.get_attribute("href")
                        url_final = f"https://www.masonline.com.ar{url_relativa}" if url_relativa else url_busqueda
                        
                        resultados_changomas.append({
                            "supermercado": "ChangoMás",
                            "producto_encontrado": titulo.strip(),
                            "precio": precio_numero,
                            "precio_x_unidad": precio_unidad_texto,
                            "url": url_final,
                            "estado": "ok"
                        })
                        productos_agregados += 1
        
        await page.close()
        print(f"[ChangoMás] ✓ Encontrados: {len(resultados_changomas)} productos")
        return resultados_changomas
        
    except Exception as e:
        print(f"[ChangoMás] ✗ Error crítico: {e}")
        await page.close()
        return []


async def buscar_en_dia(termino, context):
    print(f"[Dia] Iniciando búsqueda: '{termino}'...")
    page = await context.new_page()
    await page.route("**/*", bloquear_recursos_pesados)

    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://diaonline.supermercadosdia.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados_dia = []
    
    try:
        print(f"[Dia] Navegando a {url_busqueda}")
        await page.goto(url_busqueda, timeout=TIMEOUT_GOTO)
        
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        try:
            print(f"[Dia] Esperando tarjetas...")
            await page.wait_for_selector(selector_tarjetas, timeout=TIMEOUT_SELECTOR)
            print(f"[Dia] Tarjetas encontradas, esperando precios...")
            await page.wait_for_selector("#priceContainer", timeout=TIMEOUT_SELECTOR)
            await page.wait_for_timeout(TIMEOUT_WAIT)
        except Exception as e:
            print(f"[Dia] ⚠ Timeout al esperar elementos: {e}")
            await page.close()
            return []
            
        tarjetas = await page.locator(selector_tarjetas).all()
        print(f"[Dia] Total tarjetas en grilla: {len(tarjetas)}")
        
        palabras_buscadas = termino.lower().split()
        productos_agregados = 0
        
        for tarjeta in tarjetas:
            if productos_agregados >= 7:
                break
            
            titulo_elemento = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            
            if await titulo_elemento.count() > 0:
                titulo = await titulo_elemento.first.text_content()
                titulo_minuscula = titulo.strip().lower() if titulo else ""
                
                if all(palabra in titulo_minuscula for palabra in palabras_buscadas):
                    precio_elemento = tarjeta.locator("#priceContainer")
                    
                    if await precio_elemento.count() > 0:
                        precio_texto = await precio_elemento.first.text_content()
                        precio_numero = limpiar_precio(precio_texto)
                        
                        precio_unidad_elemento = tarjeta.locator(".vtex-custom-unit-price")
                        if await precio_unidad_elemento.count() > 0:
                            precio_unidad_texto = await precio_unidad_elemento.first.text_content()
                        else:
                            precio_unidad_texto = "No informado"
                        
                        url_relativa = await tarjeta.get_attribute("href")
                        url_final = f"https://diaonline.supermercadosdia.com.ar{url_relativa}" if url_relativa else url_busqueda
                        
                        resultados_dia.append({
                            "supermercado": "Dia",
                            "producto_encontrado": titulo.strip(),
                            "precio": precio_numero,
                            "precio_x_unidad": precio_unidad_texto,
                            "url": url_final,
                            "estado": "ok"
                        })
                        productos_agregados += 1
        
        await page.close()
        print(f"[Dia] ✓ Encontrados: {len(resultados_dia)} productos")
        return resultados_dia
        
    except Exception as e:
        print(f"[Dia] ✗ Error crítico: {e}")
        await page.close()
        return []


async def buscar_en_jumbo(termino, context):
    print(f"[Jumbo] Iniciando búsqueda: '{termino}'...")
    page = await context.new_page()
    await page.route("**/*", bloquear_recursos_pesados)

    termino_encodeado = urllib.parse.quote(termino)
    url_busqueda = f"https://www.jumbo.com.ar/{termino_encodeado}?_q={termino_encodeado}&map=ft"
    resultados_jumbo = []
    
    try:
        print(f"[Jumbo] Navegando a {url_busqueda}")
        await page.goto(url_busqueda, timeout=TIMEOUT_GOTO)
        
        selector_tarjetas = ".vtex-product-summary-2-x-clearLink"
        try:
            print(f"[Jumbo] Esperando tarjetas...")
            await page.wait_for_selector(selector_tarjetas, timeout=TIMEOUT_SELECTOR)
            print(f"[Jumbo] Tarjetas encontradas, esperando precios...")
            await page.wait_for_selector("#priceContainer", timeout=TIMEOUT_SELECTOR)
            await page.wait_for_timeout(TIMEOUT_WAIT)
        except Exception as e:
            print(f"[Jumbo] ⚠ Timeout al esperar elementos: {e}")
            await page.close()
            return []
        
        tarjetas = await page.locator(selector_tarjetas).all()
        print(f"[Jumbo] Total tarjetas en grilla: {len(tarjetas)}")
        
        palabras_buscadas = termino.lower().split()
        productos_agregados = 0
        
        for tarjeta in tarjetas:
            if productos_agregados >= 7:
                break
            
            titulo_elemento = tarjeta.locator(".vtex-product-summary-2-x-nameContainer")
            
            if await titulo_elemento.count() > 0:
                titulo = await titulo_elemento.first.text_content()
                titulo_minuscula = titulo.strip().lower() if titulo else ""
                
                if all(palabra in titulo_minuscula for palabra in palabras_buscadas):
                    precio_elemento = tarjeta.locator("#priceContainer")
                    
                    if await precio_elemento.count() > 0:
                        precio_texto = await precio_elemento.first.text_content()
                        precio_numero = limpiar_precio(precio_texto)
                        
                        precio_unidad_elemento = tarjeta.locator(".vtex-custom-unit-price")
                        if await precio_unidad_elemento.count() > 0:
                            precio_unidad_texto = await precio_unidad_elemento.first.text_content()
                        else:
                            precio_unidad_texto = "No informado"
                        
                        url_relativa = await tarjeta.get_attribute("href")
                        url_final = f"https://www.jumbo.com.ar/{url_relativa}" if url_relativa else url_busqueda
                        
                        resultados_jumbo.append({
                            "supermercado": "Jumbo",
                            "producto_encontrado": titulo.strip(),
                            "precio": precio_numero,
                            "precio_x_unidad": precio_unidad_texto,
                            "url": url_final,
                            "estado": "ok"
                        })
                        productos_agregados += 1
        
        await page.close()
        print(f"[Jumbo] ✓ Encontrados: {len(resultados_jumbo)} productos")
        return resultados_jumbo
        
    except Exception as e:
        print(f"[Jumbo] ✗ Error crítico: {e}")
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
        print("[RESUMEN]")
        print(f"{'='*60}")
        
        for i, (nombre, resultado) in enumerate(zip(supermercados_nombres, tanda_1)):
            if isinstance(resultado, Exception):
                print(f"[{nombre}] ✗ EXCEPCIÓN: {resultado}")
            elif isinstance(resultado, list):
                print(f"[{nombre}] → {len(resultado)} productos")
                resultados_totales.extend(resultado)
            else:
                print(f"[{nombre}] ✗ Resultado inesperado: {type(resultado)}")
        
        print(f"{'='*60}")
        print(f"TOTAL: {len(resultados_totales)} productos encontrados")
        print(f"{'='*60}\n")
        
        await browser.close()
        
        resultados_limpios = [r for r in resultados_totales if r.get("precio") is not None and r.get("precio") > 0]
        resultados_limpios.sort(key=lambda x: x["precio"])
        
        return resultados_limpios
