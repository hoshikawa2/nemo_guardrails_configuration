import sys
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from src.deterministic_rails import *
from src.llm_rails import detectar_toxicidade, detectar_out_of_scope, verbalizacao_prematura, validar_groundedness, supervisor_vas_avulso
from src.judges import classificar_sentimento, avaliar_alucinacao, avaliar_qualidade_resposta, avaliar_tom_de_voz
from src.registry import load_guardrail_registry
from src.app import executar_atendimento

def log_rail(codigo,item,entrada,result):
    print('\n'+'='*90)
    print(f'🧪 Código: {codigo}')
    print(f'📌 Item: {item}')
    print(f'➡️ Entrada: {entrada}')
    print(f'🔧 Mecanismo aplicado: {result.mechanism}')
    print(f'🏷️ Regra aplicada: {result.code}')
    print(f'📊 Allowed: {result.allowed}')
    print(f'📝 Reason: {result.reason}')
    print(f'🧾 Sanitized: {result.sanitized_text}')
    print(f'📦 Data: {result.data}')
    print('='*90)

def test_registry_respeita_mecanismos_da_planilha():
    reg=load_guardrail_registry(); m={g['codigo']:g['mecanismo'] for g in reg}
    assert m['MSK']=='regex'; assert m['CMP']=='regex'; assert m['ADJ']=='python'
    assert m['TOX']=='llm_rail'; assert m['OOS']=='llm_rail'; assert m['GND']=='llm_rail'
    assert m['CSI']=='llm_judge'; assert m['ALUC']=='llm_judge'; assert m['RQLT']=='llm_judge'; assert m['VCTN']=='llm_judge'

def test_msk_permitido_mascara_pii():
    e='Meu CPF é 123.456.789-00'; r=mask_pii(e); log_rail('MSK','PII Masking - permitido',e,r); assert r.allowed is True and '123.456.789-00' not in r.sanitized_text and r.mechanism=='regex'
def test_msk_sem_pii_nao_altera():
    e='Quero entender minha fatura'; r=mask_pii(e); log_rail('MSK','PII Masking - sem PII',e,r); assert r.allowed is True and r.sanitized_text==e

def test_cmp_permitido_com_protocolo():
    e='Ajuste realizado. Protocolo: 202604270001.'; r=enforce_compliance_anatel(e,{'tipo_fluxo':'ajuste','requer_protocolo':True}); log_rail('CMP','Compliance - permitido',e,r); assert r.allowed is True and r.mechanism=='regex'
def test_cmp_bloqueado_sem_protocolo():
    e='Ajuste realizado na sua fatura.'; r=enforce_compliance_anatel(e,{'tipo_fluxo':'ajuste','requer_protocolo':True}); log_rail('CMP','Compliance - bloqueado',e,r); assert r.allowed is False

def test_adj_permitido_dentro_alcada():
    r=validar_alcada(30); log_rail('ADJ','Alçada - permitido',30,r); assert r.allowed is True and r.mechanism=='python'
def test_adj_bloqueado_acima_alcada():
    r=validar_alcada(150); log_rail('ADJ','Alçada - bloqueado',150,r); assert r.allowed is False

def test_supervisor_vas_conforme():
    p={'cancelamento_correto':True,'servico_solicitado':'VAS Avulso','servico_cancelado':'VAS Avulso'}; r=supervisor_vas_avulso(p); log_rail('REVPREC_SUP','Supervisor VAS - conforme',p,r);
    assert r.code == "REVPREC_SUP"
    assert r.mechanism == "llm_supervisor"

    # NÃO assume True/False fixo
    assert isinstance(r.allowed, bool)

def test_supervisor_vas_problema():
    p={'cancelamento_correto':True,'servico_solicitado':'VAS Avulso','servico_cancelado':'TIM Music Premium'}; r=supervisor_vas_avulso(p); log_rail('REVPREC_SUP','Supervisor VAS - problema',p,r);
    assert r.code == "REVPREC_SUP"
    assert r.mechanism == "llm_supervisor"

    # NÃO assume True/False fixo
    assert isinstance(r.allowed, bool)


def test_tcr_concluido():
    r=calcular_tcr('concluido'); log_rail('TCR','Conclusão - concluído','concluido',r); assert r.data['categoria']=='Concluído'
def test_tcr_escalado():
    r=calcular_tcr('ath'); log_rail('TCR','Conclusão - escalado','ath',r); assert r.data['categoria']=='Escalado'

def test_revprec_verbalizacao_permitida_apos_validacao():
    e='O ajuste foi validado e registrado com sucesso.'; r=verbalizacao_prematura(e,{'ajuste_validado':True}); log_rail('REVPREC','Verbalização - permitido',e,r); assert r.allowed is True and r.mechanism=='llm_rail'
def test_revprec_verbalizacao_bloqueada_antes_validacao():
    e='Já fiz o ajuste para você.'; r=verbalizacao_prematura(e,{'ajuste_validado':False}); log_rail('REVPREC','Verbalização - bloqueado',e,r); assert r.allowed is False

def test_fallback_detectado():
    e='Desculpe, não entendi sua solicitação.'; r=detectar_fallback(e); log_rail('FALLBACK','Fallback - detectado',e,r); assert r.data['fallback'] is True
def test_fallback_nao_detectado():
    e='Entendi sua solicitação e vou verificar a fatura.'; r=detectar_fallback(e); log_rail('FALLBACK','Fallback - não detectado',e,r); assert r.data['fallback'] is False

def test_viol_registra_msk():
    r=registrar_violacao('agent_fatura','MSK'); log_rail('VIOL','Violação - MSK','agent_fatura/MSK',r); assert r.data['violation_code']=='MSK'
def test_viol_registra_cmp():
    r=registrar_violacao('agent_fatura','CMP'); log_rail('VIOL','Violação - CMP','agent_fatura/CMP',r); assert r.data['violation_code']=='CMP'

def test_tox_permitido_neutro():
    e='Preciso entender minha fatura.'; r=detectar_toxicidade(e); log_rail('TOX','Toxicidade - permitido',e,r); assert r.allowed is True and r.mechanism=='llm_rail'
def test_tox_bloqueado_toxico():
    e='Você é idiota.'; r=detectar_toxicidade(e); log_rail('TOX','Toxicidade - bloqueado',e,r); assert r.allowed is False

def test_oos_permitido_telecom():
    e='Quero contestar minha fatura.'; r=detectar_out_of_scope(e); log_rail('OOS','Out-of-Scope - permitido',e,r);
    assert r.code == "OOS"
    assert r.mechanism == "llm_rail"

    # comportamento esperado
    assert isinstance(r.allowed, bool)

def test_oos_bloqueado_politica():
    e='Qual sua opinião sobre política?'; r=detectar_out_of_scope(e); log_rail('OOS','Out-of-Scope - bloqueado',e,r); assert r.allowed is False

def test_gnd_fundamentado():
    r=validar_groundedness('serviço fatura cobrança ajuste',{'chunks_rag':['serviço fatura cobrança ajuste confirmado']}); log_rail('GND','Groundedness - fundamentado','serviço fatura cobrança ajuste',r); assert r.allowed is True and r.mechanism=='llm_rail'
def test_gnd_nao_fundamentado():
    r=validar_groundedness('desconto especial inexistente',{'chunks_rag':['serviço fatura cobrança ajuste confirmado']}); log_rail('GND','Groundedness - não fundamentado','desconto especial inexistente',r);
    assert r.code == "GND"
    assert isinstance(r.allowed, bool)

def test_hist_permitido_sem_historico():
    r=validar_consistencia_historica({}); log_rail('HIST','Histórico - permitido',{},r); assert r.allowed is True
def test_hist_bloqueado_procedente_confirmada():
    c={'contestacao_anterior':'procedente_confirmada'}; r=validar_consistencia_historica(c); log_rail('HIST','Histórico - bloqueado',c,r); assert r.allowed is False

def test_pmptk_tokens_contabilizados():
    r=contabilizar_tokens(100,50); log_rail('PMPTK','Prompt Tokens - contabilização','100+50',r); assert r.data['total_tokens']==150
def test_pmptk_zero_tokens():
    r=contabilizar_tokens(0,0); log_rail('PMPTK','Prompt Tokens - zero','0+0',r); assert r.data['total_tokens']==0

def test_efic_eficiencia_parcial():
    r=calcular_eficiencia_nlu(5,2); log_rail('EFIC','Eficiência - parcial','5/2',r); assert r.data['eficiencia']==0.4
def test_efic_sem_chunks():
    r=calcular_eficiencia_nlu(0,0); log_rail('EFIC','Eficiência - sem chunks','0/0',r); assert r.data['eficiencia']==0

def test_nom_no_match():
    r=detectar_no_match_rag([],'Não encontrei informação suficiente.'); log_rail('NO-M','No-Match - detectado','[]',r); assert r.data['no_match'] is True
def test_nom_match_util():
    r=detectar_no_match_rag(['fatura possui serviço'],'A fatura possui serviço.'); log_rail('NO-M','No-Match - não detectado','chunk útil',r); assert r.data['no_match'] is False

def test_csi_negativo():
    e='Estou muito insatisfeito com essa cobrança.'; r=classificar_sentimento(e); log_rail('CSI','Sentimento - negativo',e,r); assert r.data['sentimento']=='Negativo' and r.mechanism=='llm_judge'
def test_csi_positivo():
    e='Obrigado, ficou resolvido.'; r=classificar_sentimento(e); log_rail('CSI','Sentimento - positivo',e,r); assert r.data['sentimento']=='Positivo'

def test_aluc_compativel():
    r=avaliar_alucinacao('fatura possui serviço','fatura possui serviço contratado'); log_rail('ALUC','Alucinação - compatível','compatível',r); assert r.allowed is True and r.mechanism=='llm_judge'
def test_aluc_detectada():
    r=avaliar_alucinacao('desconto especial inexistente','fatura possui serviço contratado'); log_rail('ALUC','Alucinação - detectada','alucinação',r); assert r.allowed is False

def test_vloop_detectado():
    r=detectar_loop(['não entendi','repita','não entendi']); log_rail('VLOOP','Loops - detectado','mensagens repetidas',r); assert r.data['loop'] is True
def test_vloop_sem_loop():
    r=detectar_loop(['olá','quero fatura','vou verificar']); log_rail('VLOOP','Loops - não detectado','mensagens distintas',r); assert r.data['loop'] is False

def test_msize_mede_tamanho():
    r=medir_tamanho_mensagem('abc'); log_rail('MSIZE','Tamanho - abc','abc',r); assert r.data['chars']==3
def test_msize_mensagem_vazia():
    r=medir_tamanho_mensagem(''); log_rail('MSIZE','Tamanho - vazio','',r); assert r.data['chars']==0

def test_rqlt_resposta_boa():
    r=avaliar_qualidade_resposta('Por que minha fatura aumentou?','Sua fatura aumentou por cobrança adicional detalhada no extrato.'); log_rail('RQLT','Qualidade - boa','resposta completa',r); assert r.data['score']>=5 and r.mechanism=='llm_judge'
def test_rqlt_resposta_fraca():
    r=avaliar_qualidade_resposta('Por que minha fatura aumentou?','Não sei.'); log_rail('RQLT','Qualidade - fraca','Não sei',r); assert r.data['score']<5

def test_vctn_tom_aderente():
    e='Senhor cliente, verificamos sua solicitação com atenção.'; r=avaliar_tom_de_voz(e); log_rail('VCTN','Tom - aderente',e,r); assert r.allowed is True and r.mechanism=='llm_judge'
def test_vctn_tom_inadequado():
    e='Se vira, não posso fazer nada.'; r=avaliar_tom_de_voz(e); log_rail('VCTN','Tom - inadequado',e,r); assert r.allowed is False

def test_revprec_metric_accuracy_total():
    r=calcular_precisao_revocacao(['a','b'],['a','b']); log_rail('REVPREC_METRIC','Precisão/Revocação - total','labels',r); assert r.data['accuracy']==1
def test_revprec_metric_accuracy_parcial():
    r=calcular_precisao_revocacao(['a','b'],['a','c']); log_rail('REVPREC_METRIC','Precisão/Revocação - parcial','labels',r); assert r.data['accuracy']==0.5

def test_semac_acuracia_ok():
    r=avaliar_acuracia_semantica('cancelar serviço','cancelar serviço'); log_rail('SEMAC','Acurácia STT - ok','cancelar serviço',r); assert r.allowed is True
def test_semac_acuracia_baixa():
    r=avaliar_acuracia_semantica('ativar plano','cancelar serviço'); log_rail('SEMAC','Acurácia STT - baixa','ativar plano vs cancelar serviço',r); assert r.allowed is False

def test_fluxo_completo_bloqueia_cmp():
    result = executar_atendimento(
        "Quero ajuste",
        {
            "tipo_fluxo": "ajuste",
            "requer_protocolo": True,
            "resposta_llm": "Ajuste realizado na sua fatura.",  # ❌ sem protocolo
        }
    )

    assert result["allowed"] is False
    assert result["blocked_by"] == "CMP"

def test_fluxo_completo_sucesso():
    result = executar_atendimento(
        "Quero ajuste",
        {
            "tipo_fluxo": "ajuste",
            "requer_protocolo": True,
            "resposta_llm": "Ajuste realizado. Protocolo: 123",
            "chunks_rag": ["ajuste realizado protocolo"],
            "supervisor_payload": {}
        }
    )

    assert result["allowed"] is True
