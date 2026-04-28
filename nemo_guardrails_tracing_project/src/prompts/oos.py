def build_oos_prompt(text):
    return f"""
Verifique se o texto está fora do escopo de Telecom.

Texto:
{text}

Fora de escopo:
- política
- religião
- concorrentes

Responda JSON:
{{
  "allowed": true/false,
  "label": "IN_SCOPE/OUT_OF_SCOPE"
}}
"""