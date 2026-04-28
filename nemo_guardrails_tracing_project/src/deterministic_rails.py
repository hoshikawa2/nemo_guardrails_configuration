import re
from collections import Counter
from .models import RailResult
from .tracing import span

def mask_pii(text:str)->RailResult:
    with span('rail.MSK', mechanism='regex'):
        original=text
        text=re.sub(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b','[CPF_MASCARADO]',text)
        text=re.sub(r'\b\d{16}\b','[CARTAO_MASCARADO]',text)
        text=re.sub(r'(?i)(senha\s*[:=]?\s*)\S+',r'\1[SENHA_MASCARADA]',text)
        return RailResult(True,'PII mascarada' if text!=original else 'Nenhuma PII detectada',text,'MSK','regex')

def enforce_compliance_anatel(text:str, context:dict)->RailResult:
    with span('rail.CMP', mechanism='regex'):
        requer=context.get('tipo_fluxo')=='ajuste' or context.get('requer_protocolo') is True
        if not requer: return RailResult(True,'Compliance Anatel não aplicável',text,'CMP','regex')
        has_protocol=bool(re.search(r'(?i)\bprotocolo\b[:\s-]*\d{6,}',text))
        if not has_protocol: return RailResult(False,'Resposta de ajuste sem número de protocolo',text,'CMP','regex')
        return RailResult(True,'Resposta contém protocolo obrigatório',text,'CMP','regex')

def validar_alcada(valor:float, limite:float=50.0)->RailResult:
    with span('rail.ADJ', mechanism='python'):
        if valor>limite: return RailResult(False,f'Valor R$ {valor:.2f} excede alçada de R$ {limite:.2f}; escalar para ATH',code='ADJ',mechanism='python')
        return RailResult(True,f'Valor R$ {valor:.2f} dentro da alçada',code='ADJ',mechanism='python')

def calcular_tcr(status:str)->RailResult:
    status=status.lower(); categoria='Indefinido'
    if status in ['concluido','concluído','resolvido']: categoria='Concluído'
    elif status in ['abandonado','timeout','desistencia']: categoria='Abandonado'
    elif status in ['escalado','ath','humano']: categoria='Escalado'
    return RailResult(True,f'TCR classificado como {categoria}',code='TCR',mechanism='python',data={'categoria':categoria})

def detectar_fallback(text:str)->RailResult:
    frases=['não entendi','não consegui entender','não tenho informação','não encontrei informação']; detected=any(f in text.lower() for f in frases)
    return RailResult(True,'Fallback detectado' if detected else 'Fallback não detectado',text,'FALLBACK','python',{'fallback':detected})

def registrar_violacao(agent_id:str, code:str)->RailResult:
    return RailResult(True,'Violação registrada para agregação',code='VIOL',mechanism='python',data={'agent_id':agent_id,'violation_code':code,'count':1})

def validar_consistencia_historica(context:dict)->RailResult:
    if context.get('contestacao_anterior')=='procedente_confirmada': return RailResult(False,'Fatura já confirmada como procedente anteriormente',code='HIST',mechanism='python')
    return RailResult(True,'Sem conflito histórico',code='HIST',mechanism='python')

def contabilizar_tokens(prompt_tokens:int, completion_tokens:int)->RailResult:
    total=prompt_tokens+completion_tokens; return RailResult(True,'Tokens contabilizados',code='PMPTK',mechanism='python',data={'prompt_tokens':prompt_tokens,'completion_tokens':completion_tokens,'total_tokens':total})

def calcular_eficiencia_nlu(chunks_retornados:int, chunks_utilizados:int)->RailResult:
    eficiencia=chunks_utilizados/chunks_retornados if chunks_retornados else 0; return RailResult(True,'Eficiência NLU calculada',code='EFIC',mechanism='python',data={'eficiencia':eficiencia})

def detectar_no_match_rag(chunks:list, resposta:str)->RailResult:
    no_match=not chunks or 'não encontrei' in resposta.lower(); return RailResult(True,'No-Match RAG detectado' if no_match else 'RAG retornou evidência útil',code='NO-M',mechanism='python',data={'no_match':no_match})

def detectar_loop(mensagens:list[str])->RailResult:
    counts=Counter(mensagens); loop=any(v>=2 for v in counts.values()); return RailResult(True,'Loop detectado' if loop else 'Sem loop',code='VLOOP',mechanism='python',data={'loop':loop})

def medir_tamanho_mensagem(text:str)->RailResult:
    return RailResult(True,'Tamanho de mensagem medido',text,'MSIZE','python',{'chars':len(text)})

def calcular_precisao_revocacao(y_true:list[str], y_pred:list[str])->RailResult:
    total=len(y_true); correct=sum(1 for a,b in zip(y_true,y_pred) if a==b); accuracy=correct/total if total else 0
    return RailResult(True,'Acurácia de roteamento calculada',code='REVPREC_METRIC',mechanism='python',data={'accuracy':accuracy})

def avaliar_acuracia_semantica(audio_transcrito:str, referencia_humana:str)->RailResult:
    a=set(audio_transcrito.lower().split()); b=set(referencia_humana.lower().split()); score=len(a & b)/len(b) if b else 0
    return RailResult(score>=0.85,f'Acurácia semântica STT: {score:.2f}',code='SEMAC',mechanism='python',data={'score':score})
