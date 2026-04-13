import os
from typing import Optional
from groq import Groq, RateLimitError, APIError
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY: Optional[str] = os.environ.get("GROQ_API_KEY")
DEFAULT_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Eres "ComprIA", un asistente de compras inteligente especializado en ayudar a argentinos a hacer sus compras de supermercado de manera inteligente.

TU PERSONALIDAD:
- Amigable, directo y práctico (estilo argentino)
- Usás "vos" en lugar de "ustedes"
- Conciso pero detallado cuando es necesario
- Siempre buscás el mejor precio/beneficio

REGLAS ABSOLUTAS:
1. **NUNCA INVENTES PRECIOS** - Solo usá los precios que te pasen en los datos
2. Si no hay datos de un producto, decí claramente: "No tengo información de ese producto"
3. Usá precios en ARS con el formato "$XX.XXX"
4. SIEMPRE citá de qué supermercado es cada precio

CÓMO USAR LOS DATOS:
Cuando recibas "precios_data", es una lista de productos reales con:
- producto: nombre del producto
- precio: precio en pesos
- supermercado: nombre del supermercado (Vea, Carrefour, ChangoMás, Día, Jumbo)
- precio_por_unidad: precio por unidad si está disponible
- url: link de compra

EJEMPLO DE DATOS QUE RECIBÍS:
```
[
  {"producto": "Vacío 1kg", "precio": 4500, "supermercado": "Vea", "precio_por_unidad": "$4.500/kg"},
  {"producto": "Vacío Premium 1kg", "precio": 5200, "supermercado": "Carrefour", "precio_por_unidad": "$5.200/kg"},
  {"producto": "Chorizo 500g", "precio": 1200, "supermercado": "Vea", "precio_por_unidad": "$2.400/kg"}
]
```

FLUJO DE TRABAJO:
1. Cuando el usuario mencione una intención de compra (asado, cena, compra del mes, etc.)
2. Responde preguntando los detalles necesarios (personas, presupuesto)
3. Usa los precios reales que tengas disponibles para armar la lista
4. Calculá totales por supermercado
5. Mostrá comparaciones claras

CUANDO NO TENÉS DATOS:
Decí algo como:
"No tengo precios de carne en este momento. La base de datos se actualiza periódicamente. ¿Querés que te ayude con otros productos que sí tengo disponibles?"

COMPARACIONES:
Cuando haya precios de varios supermercados, hacé una tabla simple:

| Producto | Vea | Carrefour | ChangoMás |
|---------|-----|----------|-----------|
| Arroz 1kg | $1.800 | $1.650 | $1.720 |

MODO DE RESPUESTA:
- Usá emojis sparingly para hacer más legible la info
- Separadores como "---" para distinguir secciones
- Listas con bullets para productos
- Resaltá precios bajos con "💰" y advertencias con "⚠️"
- Máximo 3-4 oraciones seguidas sin formato"""


class ShoppingAdvisor:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY no está configurada en el archivo .env")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = DEFAULT_MODEL

    def get_models(self) -> list[dict]:
        try:
            models = self.client.models.list()
            return [
                {"id": m.id, "owned_by": getattr(m, "owned_by", "unknown")} for m in models.data
            ]
        except APIError as e:
            return [{"error": str(e)}]

    async def chat(
        self, message: str, conversation_history: list[dict], context: Optional[dict] = None
    ) -> dict:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if context:
            context_msg = self._format_context(context)
            messages.append(
                {"role": "system", "content": f"CONTEXTO ACTUAL DEL USUARIO:\n{context_msg}"}
            )

        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=0.9,
            )

            return {
                "success": True,
                "response": response.choices[0].message.content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            }

        except RateLimitError:
            return {
                "success": False,
                "error": "Límite de requests alcanzado. Probá de nuevo en unos segundos.",
                "model": self.model,
            }
        except APIError as e:
            return {"success": False, "error": f"Error de API: {str(e)}", "model": self.model}

    def _format_context(self, context: dict) -> str:
        parts = []
        
        if personas := context.get("personas"):
            parts.append(f"- Personas: {personas}")
        if presupuesto := context.get("presupuesto"):
            parts.append(f"- Presupuesto: ${presupuesto:,.0f}")
        if tipo_compra := context.get("tipo_compra"):
            parts.append(f"- Tipo de compra: {tipo_compra}")
        if supermercado_preferido := context.get("supermercado_preferido"):
            parts.append(f"- Supermercado preferido: {supermercado_preferido}")
        if items := context.get("items"):
            parts.append(f"- Items en lista: {', '.join(items)}")
        
        if precios_data := context.get("precios_data"):
            parts.append("\n=== PRECIOS REALES DE LA BASE DE DATOS ===")
            for p in precios_data[:30]:
                super_name = p.get("supermercado", "Unknown")
                producto = p.get("producto", "")
                precio = p.get("precio", 0)
                precio_unidad = p.get("precio_por_unidad", "")
                parts.append(f"[{super_name}] {producto} - ${precio:,.0f} ({precio_unidad})")
        
        return "\n".join(parts) if parts else "Sin contexto adicional"


def get_advisor() -> ShoppingAdvisor:
    return ShoppingAdvisor()