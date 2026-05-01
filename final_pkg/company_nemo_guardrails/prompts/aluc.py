def build_aluc_prompt(resposta, dados):
    return f"""
Você é um auditor de consistência de respostas.

Definição de ALUCINAÇÃO:

Marque como ALUCINACAO se:
- A resposta contém informação que NÃO está na base
- A resposta menciona algo que NÃO pode ser inferido da base

NÃO marcar como alucinação se:
- A resposta for uma simplificação da base
- A resposta for um subconjunto da informação

Base real:
{dados}

Resposta:
{resposta}

Pergunta:
A resposta contém informação NÃO suportada pela base?

Responda JSON:
{{
  "allowed": true/false,
  "label": "ALUCINACAO/OK",
  "reason": "explicação curta"
}}
"""