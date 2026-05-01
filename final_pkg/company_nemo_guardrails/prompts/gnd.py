def build_gnd_prompt(resposta, context):
    return f"""
Verifique se a resposta está fundamentada.

Resposta:
{resposta}

Base:
{context.get("chunks_rag", [])}

Responda:
{{
  "allowed": true/false,
  "label": "GROUNDED/UNGROUNDED"
}}
"""