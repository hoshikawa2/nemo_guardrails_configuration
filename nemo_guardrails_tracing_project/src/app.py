from .deterministic_rails import mask_pii, validar_alcada, enforce_compliance_anatel
from .llm_rails import detectar_toxicidade, detectar_out_of_scope, validar_groundedness, verbalizacao_prematura, supervisor_vas_avulso
from .judges import avaliar_qualidade_resposta
import json


def executar_atendimento(user_input: str, context: dict):
    steps = []

    # INPUT RAILS
    r = mask_pii(user_input)
    steps.append(r)
    text = r.sanitized_text or user_input

    for rail in [detectar_toxicidade, detectar_out_of_scope]:
        r = rail(text)
        steps.append(r)
        if not r.allowed:
            return {
                "allowed": False,
                "blocked_by": r.code,
                "steps": steps
            }

    # PYTHON RULE
    if "ajuste_valor" in context:
        r = validar_alcada(context["ajuste_valor"])
        steps.append(r)
        if not r.allowed:
            return {
                "allowed": False,
                "blocked_by": r.code,
                "steps": steps
            }

    # LLM RESPONSE (simulada ou real)
    resposta = context.get("resposta_llm", "Resposta simulada do agente.")

    # OUTPUT + JUDGES + SUPERVISOR
    for r in [
        verbalizacao_prematura(resposta, context),
        enforce_compliance_anatel(resposta, context),
        validar_groundedness(resposta, context),
        avaliar_qualidade_resposta(user_input, resposta),
        supervisor_vas_avulso(context.get("supervisor_payload", {}))
    ]:
        steps.append(r)

    return {
        "allowed": all(s.allowed for s in steps if s.code != "RQLT"),
        "response": resposta,
        "steps": steps
    }


# =========================
# 🔥 EXECUÇÃO DIRETA
# =========================
def print_result(result):
    print("\n" + "=" * 80)
    print("📊 RESULTADO FINAL")
    print("=" * 80)

    print(f"✔ Allowed: {result['allowed']}")
    print(f"💬 Response: {result.get('response')}")

    if not result["allowed"]:
        print(f"🚫 Bloqueado por: {result.get('blocked_by')}")

    print("\n🔎 STEPS:")
    for s in result["steps"]:
        print("-" * 60)
        print(f"🧩 Code: {s.code}")
        print(f"⚙️  Mechanism: {s.mechanism}")
        print(f"✔ Allowed: {s.allowed}")
        print(f"📝 Reason: {s.reason}")
        if s.sanitized_text:
            print(f"🔐 Sanitized: {s.sanitized_text}")
        if s.data:
            print(f"📦 Data: {s.data}")

    print("=" * 80)

    # JSON final (para integração)
    print("\n📦 JSON OUTPUT:")
    print(json.dumps({
        "allowed": result["allowed"],
        "response": result.get("response"),
        "steps": [
            {
                "code": s.code,
                "allowed": s.allowed,
                "reason": s.reason,
                "mechanism": s.mechanism,
                "data": s.data
            }
            for s in result["steps"]
        ]
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # 🔧 EXEMPLO DE EXECUÇÃO

    user_input = "Meu CPF é 123.456.789-00 e quero ajuste de 20 reais"

    context = {
        "ajuste_valor": 20,
        "ajuste_validado": True,
        "tipo_fluxo": "ajuste",
        "requer_protocolo": True,
        "resposta_llm": "Ajuste realizado. Protocolo: 202604270001.",
        "chunks_rag": ["serviço fatura cobrança ajuste realizado protocolo"],
        "supervisor_payload": {
            "cancelamento_correto": True,
            "servico_cancelado": "VAS Avulso",
            "servico_solicitado": "VAS Avulso"
        }
    }

    result = executar_atendimento(user_input, context)
    print_result(result)