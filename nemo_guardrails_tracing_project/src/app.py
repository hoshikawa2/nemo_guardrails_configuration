from .deterministic_rails import mask_pii, validar_alcada, enforce_compliance_anatel
from .llm_rails import (
    detectar_toxicidade,
    detectar_out_of_scope,
    validar_groundedness,
    verbalizacao_prematura,
    supervisor_vas_avulso
)
from .judges import avaliar_qualidade_resposta
import json


def executar_atendimento(user_input: str, context: dict):
    steps = []

    # =========================
    # 🔹 INPUT RAILS
    # =========================
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
                "response": None,
                "steps": steps
            }

    # =========================
    # 🔹 PYTHON RULE (CRÍTICA)
    # =========================
    if "ajuste_valor" in context:
        r = validar_alcada(context["ajuste_valor"])
        steps.append(r)

        if not r.allowed:
            return {
                "allowed": False,
                "blocked_by": r.code,
                "response": None,
                "steps": steps
            }

    # =========================
    # 🔹 LLM RESPONSE
    # =========================
    resposta = context.get(
        "resposta_llm",
        "Resposta simulada do agente."
    )

    # =========================
    # 🔹 OUTPUT RAILS (BLOQUEANTES)
    # =========================
    output_rails = [
        enforce_compliance_anatel(resposta, context),
        verbalizacao_prematura(resposta, context),
        validar_groundedness(resposta, context),
    ]

    for r in output_rails:
        steps.append(r)

        # 🔥 NÃO bloquear groundedness automaticamente
        if not r.allowed and r.code != "GND":
            return {
                "allowed": False,
                "blocked_by": r.code,
                "response": None,
                "steps": steps
            }

    # =========================
    # 🔹 JUDGE (NÃO BLOQUEIA)
    # =========================
    r_quality = avaliar_qualidade_resposta(user_input, resposta)
    steps.append(r_quality)

    # =========================
    # 🔹 SUPERVISOR (AUDITORIA)
    # =========================
    r_supervisor = supervisor_vas_avulso(
        context.get("supervisor_payload", {})
    )
    steps.append(r_supervisor)

    # =========================
    # 🔹 RESULTADO FINAL
    # =========================
    BLOCKING_CODES = {"CMP", "ADJ", "REVPREC"}

    allowed = all(
        s.allowed for s in steps
        if s.code in BLOCKING_CODES
    )


    return {
        "allowed": allowed,
        "response": resposta,
        "steps": steps
    }


# =========================
# 🔥 PRINT FORMATADO
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


# =========================
# 🔥 EXECUÇÃO DIRETA
# =========================
if __name__ == "__main__":

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