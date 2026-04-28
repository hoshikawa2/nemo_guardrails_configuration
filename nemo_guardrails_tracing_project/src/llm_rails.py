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
