def build_csi_prompt(text):
    return f"""
Classifique o sentimento do cliente.

Texto:
{text}

Opções:
- Positivo
- Neutro
- Negativo

Responda JSON:
{{
  "sentimento": "Positivo/Neutro/Negativo",
  "score": 0-10
}}
"""