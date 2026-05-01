from .models import RailResult
from .llm_client import LLMClient
from .tracing import span
_client=LLMClient()
def classificar_sentimento(text:str)->RailResult:
    with span("judge.CSI", mechanism="llm_judge"):
        out=_client.classify("CSI", {"text":text}); return RailResult(True,out.get("reason",""),text,"CSI","llm_judge",{"sentimento":out.get("label"),**out})
def avaliar_alucinacao(resposta:str, dados_reais:str)->RailResult:
    with span("judge.ALUC", mechanism="llm_judge"):
        out=_client.classify("ALUC", {"resposta":resposta,"dados_reais":dados_reais}); return RailResult(out["allowed"],out.get("reason",""),resposta,"ALUC","llm_judge",{"alucinacao":out.get("label")=="ALUCINACAO",**out})
def avaliar_qualidade_resposta(pergunta:str, resposta:str)->RailResult:
    with span("judge.RQLT", mechanism="llm_judge"):
        out=_client.classify("RQLT", {"pergunta":pergunta,"resposta":resposta}); return RailResult(True,out.get("reason",""),resposta,"RQLT","llm_judge",out)
def avaliar_tom_de_voz(text:str)->RailResult:
    with span("judge.VCTN", mechanism="llm_judge"):
        out=_client.classify("VCTN", {"text":text}); return RailResult(out["allowed"],out.get("reason",""),text,"VCTN","llm_judge",{"aderente":out["allowed"],**out})
