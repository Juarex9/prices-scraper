import sys
import asyncio
from web_scrp import orquestador_de_busqueda


async def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <termino de busqueda>")
        print("Ejemplo: python main.py queso para rallar")
        return

    termino = " ".join(sys.argv[1:])
    print(f"Buscando: {termino}\n")

    resultados = await orquestador_de_busqueda(termino)

    if not resultados:
        print("No se encontraron resultados.")
        return

    print(f"\n{'='*60}")
    print(f"RESULTADOS ({len(resultados)} productos)")
    print(f"{'='*60}\n")

    for item in resultados:
        super = item.get("supermercado", "?")
        titulo = item.get("producto_encontrado", "?")
        precio = item.get("precio", 0)
        unidad = item.get("precio_x_unidad", "No informado")
        url = item.get("url", "")

        print(f"[{super}]")
        print(f"  {titulo}")
        print(f"  ${precio}  |  {unidad}")
        print(f"  {url}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
