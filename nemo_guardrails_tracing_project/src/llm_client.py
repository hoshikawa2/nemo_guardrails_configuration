import os, json
from openai import OpenAI
from src.prompts.revprec import build_revprec_prompt
from src.prompts.csi import build_csi_prompt
from src.prompts.vctn import build_vctn_prompt
from src.prompts.tox import build_tox_prompt
from src.prompts.oos import build_oos_prompt
from src.prompts.gnd import build_gnd_prompt
from src.prompts.aluc import build_aluc_prompt
from src.prompts.rqlt import build_rqlt_prompt
from src.prompts.supervisor import build_supervisor_prompt

# Segurança
from src.prompts.dlex_in import build_dlex_in_prompt
from src.prompts.dlex_out import build_dlex_out_prompt
from src.prompts.pinj import build_pinj_prompt
from src.prompts.ragsec import build_ragsec_prompt

class LLMClient:
    def __init__(self):
        self.use_mock=os.getenv('USE_MOCK_LLM','true').lower()=='true'
        self.model=os.getenv('OPENAI_MODEL','gpt-4.1')
        self.client=None if self.use_mock else OpenAI(base_url=os.getenv('OPENAI_BASE_URL','http://localhost:8051/v1'), api_key=os.getenv('OPENAI_API_KEY','dummy'))

    def classify(self, task, payload):

        if self.use_mock:
            return self._mock_classify(task, payload)

        # ========================
        # ROUTING DE PROMPTS
        # ========================
        if task == "REVPREC":
            prompt = build_revprec_prompt(payload["text"], payload.get("context", {}))

        elif task == "CSI":
            prompt = build_csi_prompt(payload["text"])

        elif task == "VCTN":
            prompt = build_vctn_prompt(payload["text"])

        elif task == "TOX":
            prompt = build_tox_prompt(payload["text"])

        elif task == "OOS":
            prompt = build_oos_prompt(payload["text"])

        elif task == "GND":
            prompt = build_gnd_prompt(payload["resposta"], payload.get("context", {}))

        # ========================
        # 🔥 NOVOS (faltavam)
        # ========================
        elif task == "ALUC":
            prompt = build_aluc_prompt(payload["resposta"], payload["dados_reais"])

        elif task == "RQLT":
            prompt = build_rqlt_prompt(payload["pergunta"], payload["resposta"])

        elif task == "SUPERVISOR_VAS":
            prompt = build_supervisor_prompt(payload)


        # Segurança Extra
        elif task == "PINJ":
            prompt = build_pinj_prompt(payload["text"])
        elif task == "RAGSEC":
            prompt = build_ragsec_prompt(payload["text"])
        elif task == "DLEX_IN":
            prompt = build_dlex_in_prompt(payload["text"])
        elif task == "DLEX_OUT":
            prompt = build_dlex_out_prompt(payload["text"])

        else:
            raise ValueError(f"Task não suportada: {task}")

        # ========================
        # CALL LLM
        # ========================
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        import json
        text = response.choices[0].message.content

        try:
            return json.loads(text)
        except:
            return {
                "allowed": False,
                "label": "ERROR",
                "reason": text
            }

    def _mock(self, task, payload):
        text=(payload.get('text') or payload.get('resposta') or payload.get('answer') or '').lower()
        if task=='TOX':
            bad=any(w in text for w in ['idiota','burro','lixo','inútil','ofensivo']); return {'allowed':not bad,'label':'TOXICO' if bad else 'NORMAL','reason':'mock TOX','score':0 if bad else 10}
        if task=='OOS':
            bad=any(w in text for w in ['política','religião','presidente','concorrente','vivo','claro']); return {'allowed':not bad,'label':'OUT_OF_SCOPE' if bad else 'IN_SCOPE','reason':'mock OOS','score':0 if bad else 10}
        if task=='REVPREC':
            validated=payload.get('context',{}).get('ajuste_validado',False); premature=any(w in text for w in ['já fiz','já realizei','foi realizado','ajuste aplicado','cancelamento realizado'])
            return {'allowed':not(premature and not validated),'label':'PREMATURA' if premature and not validated else 'OK','reason':'mock REVPREC','score':0 if premature and not validated else 10}
        if task=='GND':
            chunks=' '.join(payload.get('context',{}).get('chunks_rag',[])).lower(); overlap=len(set(text.split()) & set(chunks.split())); ok=overlap>=3
            return {'allowed':ok,'label':'GROUNDED' if ok else 'UNGROUNDED','reason':f'mock GND overlap={overlap}','score':min(10,overlap)}
        if task=='CSI':
            if any(w in text for w in ['insatisfeito','raiva','péssimo','cancelar']): return {'allowed':True,'label':'Negativo','reason':'mock CSI','score':3}
            if any(w in text for w in ['obrigado','ótimo','resolvido','satisfeito']): return {'allowed':True,'label':'Positivo','reason':'mock CSI','score':9}
            return {'allowed':True,'label':'Neutro','reason':'mock CSI','score':6}
        if task=='ALUC':
            overlap=len(set(payload.get('resposta','').lower().split()) & set(payload.get('dados_reais','').lower().split())); hallucinated=overlap<2
            return {'allowed':not hallucinated,'label':'ALUCINACAO' if hallucinated else 'OK','reason':f'mock ALUC overlap={overlap}','score':0 if hallucinated else 8}
        if task=='RQLT':
            resposta=payload.get('resposta',''); score=8 if len(resposta)>30 else 3; return {'allowed':True,'label':'QUALIDADE','reason':'mock RQLT','score':score}
        if task=='VCTN':
            bad=any(w in text for w in ['se vira','problema seu','não posso fazer nada']); return {'allowed':not bad,'label':'TOM_INADEQUADO' if bad else 'TOM_OK','reason':'mock VCTN','score':0 if bad else 9}
        if task=='SUPERVISOR_VAS':
            ok=payload.get('cancelamento_correto',False) and payload.get('servico_cancelado')==payload.get('servico_solicitado'); return {'allowed':ok,'label':'CONFORME' if ok else 'PROBLEMA','reason':'mock supervisor','score':10 if ok else 0}
        return {'allowed':True,'label':'OK','reason':'mock default','score':5}
