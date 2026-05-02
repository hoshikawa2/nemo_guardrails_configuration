from typing import Optional
from nemoguardrails.actions import action
from .deterministic_rails import (
    mask_pii,
    validar_alcada,
    enforce_compliance_anatel,
    calcular_tcr,
    detectar_fallback,
    registrar_violacao,
    validar_consistencia_historica,
    contabilizar_tokens,
    calcular_eficiencia_nlu,
    detectar_no_match_rag,
    detectar_loop,
    medir_tamanho_mensagem,
    calcular_precisao_revocacao,
    avaliar_acuracia_semantica,
)
from .llm_rails import (
    detectar_toxicidade,
    detectar_out_of_scope,
    verbalizacao_prematura,
    validar_groundedness,
    supervisor_vas_avulso,
)

# =========================
# HELPERS
# =========================

def get_payload(context: Optional[dict]) -> dict:
    return (context or {}).get("payload", {})

# =========================
# ACTIONS
# =========================

@action(is_system_action=True)
async def mask_pii_action(context: Optional[dict] = None, **kwargs):
    print("🔥 MSK")

    payload = get_payload(context)
    input_text = payload.get("input_text") or context.get("user_message", "")

    result = mask_pii(input_text)

    if context is not None:
        context["text"] = getattr(result, "sanitized_text", input_text)

    return result


# -------------------------

@action(is_system_action=True)
async def detectar_toxicidade_action(context: Optional[dict] = None, **kwargs):
    print("🔥 TOX")

    text = context.get("text") or context.get("user_message", "")

    result = detectar_toxicidade(text)

    return result


# -------------------------

@action(is_system_action=True)
async def detectar_out_of_scope_action(context: Optional[dict] = None, **kwargs):
    print("🔥 OOS")

    text = context.get("text") or context.get("user_message", "")

    result = detectar_out_of_scope(text)

    return result


# -------------------------

@action(is_system_action=True)
async def validar_alcada_action(ajuste_valor, limite, context: Optional[dict] = None, **kwargs):
    print("🔥 ADJ")

    result = validar_alcada(valor=ajuste_valor, limite=limite)

    return result


# -------------------------

@action(is_system_action=True)
async def verbalizacao_prematura_action(context: Optional[dict] = None, **kwargs):
    print("🔥 REVPREC")

    payload = get_payload(context)
    ctx = payload.get("context", {})

    resposta = ctx.get("last_bot_message", "")

    result = verbalizacao_prematura(resposta, ctx)

    return result


# -------------------------

@action(is_system_action=True)
async def validar_groundedness_action(context: Optional[dict] = None, **kwargs):
    print("🔥 GND")

    payload = get_payload(context)
    ctx = payload.get("context", {})

    resposta = ctx.get("last_bot_message", "")

    result = validar_groundedness(resposta, ctx)

    return result

# -------------------------

@action(is_system_action=True)
async def supervisor_vas_avulso_action(context: Optional[dict] = None, **kwargs):
    print("🔥 REVPREC_SUP")

    payload = get_payload(context)

    result = supervisor_vas_avulso(payload)

    return result

@action(is_system_action=True)
async def enforce_compliance_anatel_action(requer_protocolo, context=None, **kwargs):
    print("🔥 CMP")

    text = context.get("text") or context.get("user_message", "")
    payload = get_payload(context)
    ctx = payload.get("context", {})

    result = enforce_compliance_anatel(requer_protocolo, text, ctx)

    return result

@action(is_system_action=True)
async def calcular_tcr_action(context=None, **kwargs):
    print("🔥 TCR")

    payload = get_payload(context)
    status = payload.get("context", {}).get("status", "")

    result = calcular_tcr(status)

    return result

@action(is_system_action=True)
async def detectar_fallback_action(context=None, **kwargs):
    print("🔥 FALLBACK")

    text = context.get("text") or context.get("user_message", "")

    result = detectar_fallback(text)

    return result

@action(is_system_action=True)
async def registrar_violacao_action(context=None, **kwargs):
    print("🔥 VIOL")

    payload = get_payload(context)
    agent_id = payload.get("agent_id", "unknown")
    code = payload.get("violation_code", "UNKNOWN")

    result = registrar_violacao(agent_id, code)

    return result

@action(is_system_action=True)
async def validar_consistencia_historica_action(context=None, **kwargs):
    print("🔥 HIST")

    payload = get_payload(context)
    ctx = payload.get("context", {})

    result = validar_consistencia_historica(ctx)

    return result

@action(is_system_action=True)
async def contabilizar_tokens_action(context=None, **kwargs):
    print("🔥 PMPTK")

    payload = get_payload(context)
    prompt = payload.get("prompt_tokens", 0)
    completion = payload.get("completion_tokens", 0)

    result = contabilizar_tokens(prompt, completion)

    return result

@action(is_system_action=True)
async def calcular_eficiencia_nlu_action(context=None, **kwargs):
    print("🔥 EFIC")

    payload = get_payload(context)
    ctx = payload.get("context", {})

    result = calcular_eficiencia_nlu(
        ctx.get("chunks_retornados", 0),
        ctx.get("chunks_utilizados", 0)
    )

    return result

@action(is_system_action=True)
async def detectar_no_match_rag_action(context=None, **kwargs):
    print("🔥 NO-M")

    payload = get_payload(context)
    ctx = payload.get("context", {})

    result = detectar_no_match_rag(
        ctx.get("chunks", []),
        ctx.get("resposta_llm", "")
    )

    return result

@action(is_system_action=True)
async def detectar_loop_action(context=None, **kwargs):
    print("🔥 VLOOP")

    payload = get_payload(context)
    mensagens = payload.get("context", {}).get("mensagens", [])

    result = detectar_loop(mensagens)

    return result

@action(is_system_action=True)
async def medir_tamanho_mensagem_action(context=None, **kwargs):
    print("🔥 MSIZE")

    text = context.get("text") or context.get("user_message", "")

    result = medir_tamanho_mensagem(text)

    return result

@action(is_system_action=True)
async def calcular_precisao_revocacao_action(context=None, **kwargs):
    print("🔥 REVPREC_METRIC")

    payload = get_payload(context)
    ctx = payload.get("context", {})

    result = calcular_precisao_revocacao(
        ctx.get("y_true", []),
        ctx.get("y_pred", [])
    )

    return result

@action(is_system_action=True)
async def avaliar_acuracia_semantica_action(context=None, **kwargs):
    print("🔥 SEMAC")

    payload = get_payload(context)
    ctx = payload.get("context", {})

    result = avaliar_acuracia_semantica(
        ctx.get("audio_transcrito", ""),
        ctx.get("referencia_humana", "")
    )

    return result



