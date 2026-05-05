from .models import RailResult
from .llm_client import LLMClient
from .tracing import span
_client=LLMClient()
def detectar_toxicidade(text:str)->RailResult:
    with span("rail.TOX", mechanism="llm_rail"):
        out=_client.classify("TOX", {"text":text}); return RailResult(out["allowed"],out.get("reason",""),text,"TOX","llm_rail",out)
def detectar_out_of_scope(text:str)->RailResult:
    with span("rail.OOS", mechanism="llm_rail"):
        out=_client.classify("OOS", {"text":text}); return RailResult(out["allowed"],out.get("reason",""),text,"OOS","llm_rail",out)
def verbalizacao_prematura(text:str, context:dict)->RailResult:
    with span("rail.REVPREC", mechanism="llm_rail"):
        out=_client.classify("REVPREC", {"text":text,"context":context}); return RailResult(out["allowed"],out.get("reason",""),text,"REVPREC","llm_rail",out)

def validar_groundedness(resposta:str, context:dict)->RailResult:
    with span("rail.GND", mechanism="llm_rail"):
        out=_client.classify("GND", {"resposta":resposta,"context":context}); return RailResult(out["allowed"],out.get("reason",""),resposta,"GND","llm_rail",out)
def supervisor_vas_avulso(payload:dict)->RailResult:
    with span("supervisor.REVPREC_SUP", mechanism="llm_supervisor"):
        out=_client.classify("SUPERVISOR_VAS", payload); return RailResult(out["allowed"],out.get("reason",""),code="REVPREC_SUP",mechanism="llm_supervisor",data=out)

# =========================
# FILTROS ADICIONADOS DE SEGURANCA
# =========================

def detectar_prompt_injection_jailbreak(text:str, context:dict)->RailResult:
    with span("rail.PINJ", mechanism="llm_rail"):
        out=_client.classify("PINJ", {"text":text,"context":context}); return RailResult(out["allowed"],out.get("reason",""),text,"PINJ","llm_rail",out)

def detectar_rag_injection_context_poisoning(text:str, context:dict)->RailResult:
    with span("rail.RAGSEC", mechanism="llm_rail"):
        out=_client.classify("RAGSEC", {"text":text,"context":context}); return RailResult(out["allowed"],out.get("reason",""),text,"RAGSEC","llm_rail",out)

def detectar_data_leakage_input(text:str, context:dict)->RailResult:
    with span("rail.DLEX_IN", mechanism="llm_rail"):
        out=_client.classify("DLEX_IN", {"text":text,"context":context}); return RailResult(out["allowed"],out.get("reason",""),text,"DLEX_IN","llm_rail",out)

def detectar_data_leakage_output(text:str, context:dict)->RailResult:
    with span("rail.DLEX_OUT", mechanism="llm_rail"):
        out=_client.classify("DLEX_OUT", {"text":text,"context":context}); return RailResult(out["allowed"],out.get("reason",""),text,"DLEX_OUT","llm_rail",out)
