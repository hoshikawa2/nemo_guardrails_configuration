# src/actions.py

import json
import uuid

from .llm_rails import (
    detectar_toxicidade,
    detectar_out_of_scope,
    verbalizacao_prematura,
    validar_groundedness,
)

from .deterministic_rails import validar_alcada

try:
    from .judges import avaliar_qualidade_resposta
except Exception:
    avaliar_qualidade_resposta = None


PIPELINE_RESULTS = {}


def extrair_payload(context: dict) -> dict:
    try:
        messages = context.get("messages", [])
        content = messages[-1]["content"]
        return json.loads(content)
    except Exception:
        return {}


def add_trace(trace, label, result):
    trace.append({
        "rail": label,
        "allowed": result.allowed,
        "reason": result.reason,
        "code": getattr(result, "code", label),
        "mechanism": getattr(result, "mechanism", ""),
        "data": getattr(result, "data", {}),
    })


def executar_pipeline_validacoes(context: dict):
    print("🔥🔥🔥 ACTION FOI EXECUTADA")
    payload = extrair_payload(context)

    request_id = payload.get("request_id") or str(uuid.uuid4())
    input_text = payload.get("input_text", "")
    ctx = payload.get("context", {}) or {}

    trace = []
    failures = []

    # =========================
    # INPUT RAILS - LLM
    # =========================

    r_tox = detectar_toxicidade(input_text)
    add_trace(trace, "TOX", r_tox)
    if not r_tox.allowed:
        failures.append(("TOX", r_tox.reason))

    r_oos = detectar_out_of_scope(input_text)
    add_trace(trace, "OOS", r_oos)
    if not r_oos.allowed:
        failures.append(("OOS", r_oos.reason))

    # =========================
    # BUSINESS RAIL - DETERMINISTIC
    # =========================

    valor = ctx.get("ajuste_valor")
    r_adj = validar_alcada(valor)
    add_trace(trace, "ADJ", r_adj)
    if not r_adj.allowed:
        failures.append(("ADJ", r_adj.reason))

    # =========================
    # LLM RESPONSE
    # =========================

    final_response = ctx.get("resposta_llm", "")

    trace.append({
        "step": "LLM",
        "allowed": True,
        "input": input_text,
        "output_preview": final_response[:200],
        "mechanism": "provided_response_or_proxy",
    })

    # =========================
    # OUTPUT RAILS - LLM
    # =========================

    r_revprec = verbalizacao_prematura(final_response, ctx)
    add_trace(trace, "REVPREC", r_revprec)
    if not r_revprec.allowed:
        failures.append(("REVPREC", r_revprec.reason))

    r_gnd = validar_groundedness(final_response, ctx)
    add_trace(trace, "GND", r_gnd)
    if not r_gnd.allowed:
        failures.append(("GND", r_gnd.reason))

    # =========================
    # OPTIONAL JUDGE / CMP
    # =========================

    if avaliar_qualidade_resposta is not None:
        r_cmp = avaliar_qualidade_resposta(input_text, final_response)
        add_trace(trace, "CMP", r_cmp)
        if not r_cmp.allowed:
            failures.append(("CMP", r_cmp.reason))
    else:
        trace.append({
            "rail": "CMP",
            "allowed": True,
            "reason": "CMP não configurado",
            "mechanism": "skipped",
            "data": {},
        })

    # =========================
    # FINAL DECISION
    # =========================

    blocked = len(failures) > 0

    if blocked:
        first_code, first_reason = failures[0]
        nemo_response = f"BLOCKED:{first_code} - {first_reason}"
    else:
        nemo_response = final_response

    result = {
        "allowed": not blocked,
        "label": "CONFORME" if not blocked else "PROBLEMA",
        "response": final_response,
        "reason": nemo_response if blocked else "",
        "failures": failures,
        "trace": trace,
    }

    PIPELINE_RESULTS[request_id] = result

    return {
        "nemo_response": nemo_response
    }