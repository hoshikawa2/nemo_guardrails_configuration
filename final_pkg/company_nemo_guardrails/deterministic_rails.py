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

def enforce_compliance_anatel(requer_protocolo, text:str, context:dict)->RailResult:
    with span('rail.CMP', mechanism='regex'):
        # requer=context.get('tipo_fluxo')=='ajuste' or context.get('requer_protocolo') is True
        requer=requer_protocolo
        if not requer: return RailResult(True,'Compliance Anatel não aplicável',text,'CMP','regex')
        has_protocol=bool(re.search(r'(?i)\bprotocolo\b[:\s-]*\d{6,}',text))
        if not has_protocol: return RailResult(False,'Resposta de ajuste sem número de protocolo',text,'CMP','regex')
        return RailResult(True,'Resposta contém protocolo obrigatório',text,'CMP','regex')

def validar_alcada(valor:float, limite:float=50.0)->RailResult:
    with span('rail.ADJ', mechanism='python'):
        if valor>limite: return RailResult(False,f'Valor R$ {valor} excede alçada de R$ {limite}; escalar para ATH',code='ADJ',mechanism='python')
        return RailResult(True,f'Valor R$ {valor} dentro da alçada',code='ADJ',mechanism='python')

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

# =========================
# FILTROS ADICIONADOS DE SEGURANCA
# =========================

INJECTION_PATTERNS=[
    r'(?i)\b(ignore|desconsidere|esque[cç]a|sobrescreva)\b.{0,80}\b(instru[cç][oõ]es|regras|pol[ií]ticas|prompt|sistema|guardrails?)\b',
    r'(?i)\b(aja|finja|atue|responda|se comporte)\b.{0,80}\b(admin|administrador|sistema|developer|desenvolvedor|root|superusu[aá]rio|gerente|diretor|ceo|supervisor|coordenador|gestor)\b',
    r'(?i)\b(revele|mostre|exiba|imprima|liste|repita)\b.{0,80}\b(system prompt|prompt interno|instru[cç][oõ]es internas|mensagem do sistema)\b',
    r'(?i)\b(burle|bypass|contorne|quebre)\b.{0,80}\b(regra|pol[ií]tica|seguran[cç]a|guardrail|valida[cç][aã]o|al[cç]ada|elegibilidade)\b',
    r'(?i)\b(fa[cç]a isso mesmo sendo proibido|sem seguir as regras|n[aã]o siga a pol[ií]tica)\b',
    r'(?i)\b(instru[cç][aã]o para o agente|nota para o modelo|comando oculto|mensagem oculta)\b',
    r'(?i)\bsempre\b.{0,80}\b(conceda|aprove|cancele|altere|isente|desconte)\b.{0,80}\b(sem valida[cç][aã]o|automaticamente|sem aprova[cç][aã]o|sem confirmar)\b',
    r'(?i)\bnunca\b.{0,80}\b(valide|pe[cç]a aprova[cç][aã]o|confirme|verifique|aplique al[cç]ada|siga a pol[ií]tica)\b'
]

def detectar_prompt_injection_jailbreak(text:str)->RailResult:
    with span('rail.PINJ', mechanism='regex'):
        detected=any(re.search(p,text or '') for p in INJECTION_PATTERNS)
        if detected: return RailResult(False,'Prompt injection/jailbreak detectado',text,'PINJ','regex')
        return RailResult(True,'Prompt injection/jailbreak não detectado',text,'PINJ','regex')

def detectar_rag_injection_context_poisoning(text:str)->RailResult:
    with span('rail.RAGSEC', mechanism='regex'):
        detected=any(re.search(p,text or '') for p in INJECTION_PATTERNS)
        if detected: return RailResult(False,'RAG injection/context poisoning detectado',text,'RAGSEC','regex')
        return RailResult(True,'RAG injection/context poisoning não detectado',text,'RAGSEC','regex')

def detectar_data_leakage_input(text:str)->RailResult:
    with span('rail.DLEX_IN', mechanism='regex'):
        patterns=[
            r'(?i)\b(system prompt|prompt interno|developer prompt|mensagem do sistema|instru[cç][oõ]es internas)\b',
            r'(?i)\b(api[_ -]?key|token|secret|segredo|credencial|senha interna|chave de acesso)\b',
            r'(?i)\b(endpoint interno|url interna|servi[cç]o interno|nome do servi[cç]o|cluster|namespace)\b',
            r'(?i)\b(schema de tools?|schema da ferramenta|fun[cç][aã]o interna|par[aâ]metros da api|api interna)\b',
            r'(?i)\b(regras internas|pol[ií]ticas internas|l[oó]gica de decis[aã]o|regras de al[cç]ada)\b',
            r'(?i)\b(mostre|me diga|acesse|consulte|revele|envie|liste|exiba)\b.{0,80}\b(dados|cpf|fatura|telefone|cadastro)\b.{0,80}\b(outro cliente|terceiro|outra pessoa)\b'
        ]
        detected=any(re.search(p,text or '') for p in patterns)
        if detected: return RailResult(False,'Tentativa de exfiltração detectada na entrada',text,'DLEX_IN','regex')
        return RailResult(True,'Exfiltração não detectada na entrada',text,'DLEX_IN','regex')

def detectar_data_leakage_output(text:str)->RailResult:
    with span('rail.DLEX_OUT', mechanism='regex'):
        patterns=[
            r'(?i)\b(meu|nosso|este|o)\s+(system prompt|prompt interno|developer prompt|mensagem do sistema)\b',
            r'(?i)\b(api[_ -]?key|token|secret|segredo|credencial|senha interna|chave de acesso)\b\s*[:=]\s*\S+',
            r'(?i)\b(endpoint interno|url interna|servi[cç]o interno|nome do servi[cç]o|cluster|namespace)\b\s*[:=]\s*\S+',
            r'(?i)\b(schema de tools?|schema da ferramenta|fun[cç][aã]o interna|par[aâ]metros da api|api interna)\b',
            r'(?i)\b(nossas|minhas|as)\s+(regras internas|pol[ií]ticas internas|l[oó]gica de decis[aã]o|regras de al[cç]ada)\b'
        ]
        detected=any(re.search(p,text or '') for p in patterns)
        if detected: return RailResult(False,'Vazamento detectado na saída',text,'DLEX_OUT','regex')
        return RailResult(True,'Vazamento não detectado na saída',text,'DLEX_OUT','regex')
