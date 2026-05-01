def build_supervisor_prompt(payload):
    return f"""
Você é um auditor de atendimento.

Verifique se o cancelamento foi correto.

Solicitado:
{payload.get("servico_solicitado")}

Cancelado:
{payload.get("servico_cancelado")}

Se forem diferentes → PROBLEMA

Responda JSON:
{{
  "allowed": true/false,
  "label": "CONFORME/PROBLEMA",
  "reason": "explicação"
}}
"""