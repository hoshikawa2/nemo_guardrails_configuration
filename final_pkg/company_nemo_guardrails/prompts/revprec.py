def build_revprec_prompt(text, context):
    return f"""
Você é um auditor de atendimento ao cliente.

Regra:
- O agente NÃO pode afirmar que executou uma ação
- SE essa ação NÃO foi validada previamente

Contexto:
ajuste_validado = {context.get("ajuste_validado")}

Texto do agente:
{text}

Pergunta:
O agente cometeu verbalização prematura?

Responda JSON:
{{
  "allowed": true/false,
  "label": "OK" ou "PREMATURA",
  "reason": "explicação curta"
}}
"""