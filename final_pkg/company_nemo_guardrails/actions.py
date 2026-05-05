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
    # detectar_prompt_injection_jailbreak,
    # detectar_rag_injection_context_poisoning,
    # detectar_data_leakage_input,
    # detectar_data_leakage_output,
)
from .llm_rails import (
    detectar_toxicidade,
    detectar_out_of_scope,
    verbalizacao_prematura,
    validar_groundedness,
    supervisor_vas_avulso,
    detectar_prompt_injection_jailbreak,
    detectar_rag_injection_context_poisoning,
    detectar_data_leakage_input,
    detectar_data_leakage_output
)

# =========================
# HELPERS
# =========================

def get_payload(context: Optional[dict]) -> dict:
    return (context or {}).get("payload", {})



def get_ctx(context: Optional[dict]) -> dict:
    payload = get_payload(context)
    return payload.get("context", {}) or {}


def get_input_text(context: Optional[dict], **kwargs) -> str:
    payload = get_payload(context)
    ctx = payload.get("context", {}) or {}

    return (
            kwargs.get("text")
            or kwargs.get("user_message")
            or payload.get("input_text")
            or payload.get("user_message")
            or ctx.get("input_text")
            or ctx.get("user_message")
            or (context or {}).get("text")
            or (context or {}).get("user_message")
            or ""
    )


def get_output_text(context: Optional[dict], **kwargs) -> str:
    payload = get_payload(context)
    ctx = payload.get("context", {}) or {}

    return (
            kwargs.get("text")
            or kwargs.get("bot_message")
            or kwargs.get("assistant_message")
            or kwargs.get("llm_output")
            or payload.get("output_text")
            or payload.get("bot_message")
            or payload.get("assistant_message")
            or payload.get("llm_output")
            or ctx.get("last_bot_message")
            or ctx.get("resposta_llm")
            or ctx.get("assistant_message")
            or (context or {}).get("bot_message")
            or (context or {}).get("assistant_message")
            or (context or {}).get("llm_output")
            or (context or {}).get("text")
            or ""
    )


def chunks_to_text(chunks) -> str:
    if chunks is None:
        return ""
    if isinstance(chunks, str):
        return chunks
    if isinstance(chunks, list):
        parts = []
        for item in chunks:
            if isinstance(item, dict):
                parts.append(
                    str(
                        item.get("text")
                        or item.get("content")
                        or item.get("page_content")
                        or item.get("chunk")
                        or item
                    )
                )
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(chunks)

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

# =========================
# ACTIONS ADICIONADAS - SECURITY / SAFETY DETERMINISTIC RAILS
# =========================

@action(is_system_action=True)
async def detectar_prompt_injection_jailbreak_action(context: Optional[dict] = None, **kwargs):
    print("🔥 PINJ")

    text = context.get("text") or context.get("user_message", "")

    result = detectar_prompt_injection_jailbreak(text, context)

    return result


@action(is_system_action=True)
async def detectar_rag_injection_context_poisoning_action(context: Optional[dict] = None, **kwargs):
    print("🔥 RAGSEC")

    payload = get_payload(context)
    ctx = payload.get("context", {})

    # Preferência: validar explicitamente chunks/contexto recuperado.
    # Fallback: validar texto de entrada se a action for usada como input rail.
    chunks = (
            kwargs.get("chunks")
            or payload.get("chunks")
            or ctx.get("chunks")
            or ctx.get("retrieved_chunks")
            or ctx.get("rag_context")
            or ctx.get("documents")
    )

    text = chunks_to_text(chunks) or get_input_text(context, **kwargs)

    result = detectar_rag_injection_context_poisoning(text, context)

    return result


@action(is_system_action=True)
async def detectar_data_leakage_input_action(context: Optional[dict] = None, **kwargs):
    print("🔥 DLEX_IN")

    text = context.get("text") or context.get("user_message", "")

    result = detectar_data_leakage_input(text, context)

    return result


@action(is_system_action=True)
async def detectar_data_leakage_output_action(context: Optional[dict] = None, **kwargs):
    print("🔥 DLEX_OUT")

    payload = get_payload(context)
    ctx = payload.get("context", {})
    resposta = ctx.get("last_bot_message", "")

    result = detectar_data_leakage_output(resposta, context)

    return result
