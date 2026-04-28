# Tutorial: NeMo Guardrails com Python, Proxy OpenAI-Compatible e Tracing

## 1. Objetivo

Este tutorial orienta um time de desenvolvimento a implementar guardrails usando **NVIDIA NeMo Guardrails como biblioteca Python**, sem depender inicialmente do NeMo Server. A proposta é permitir uma adoção incremental: começar com rails determinísticos, rails LLM e regras Python dentro da aplicação, mantendo uma estrutura que possa evoluir futuramente para servidor, supervisor, judges batch e observabilidade completa.

O projeto entregue junto com este tutorial foi gerado com base na planilha `Guardrails e Curadoria v3 - Consolidado.xlsx`, que define guardrails, curadoria, supervisores e LLM-as-a-judge.

## 2. Conceitos principais

### 2.1 Guardrail

Guardrail é uma proteção aplicada ao fluxo de IA. Pode bloquear, mascarar, rejeitar, reescrever, auditar ou medir uma interação.

Neste projeto, os guardrails foram separados em quatro famílias:

| Família | Uso | Exemplo da planilha |
|---|---|---|
| NeMo / LLM rail | Avaliação semântica com LLM | Toxicidade, Out-of-Scope, Groundedness |
| Regex rail | Regra determinística rápida | PII Masking |
| Python rail | Regra de negócio determinística | Alçada de Ajuste, Histórico |
| Supervisor / Judge | Auditoria pós-fluxo ou batch | Supervisor VAS Avulso, Qualidade, Alucinação |

### 2.2 Input Rail

Executa antes do LLM. Serve para proteger o modelo contra entrada tóxica, fora de escopo, dados sensíveis, jailbreak ou pedidos indevidos.

Na planilha:

- PII Masking
- Toxicidade
- Out-of-Scope

### 2.3 Output Rail

Executa depois que o LLM gera uma resposta, mas antes de devolver ao usuário ou executar uma ação.

Na planilha:

- Compliance Anatel
- Verbalização Prematura
- Groundedness

### 2.4 Python pré-execução

Nem toda regra deve ir para o LLM. Regras financeiras, alçada, duplicidade de crédito e consistência histórica devem ficar em Python ou em serviço de negócio.

Exemplo:

```python
if valor_ajuste > limite:
    escalar_para_ath()
```

### 2.5 Supervisor

Supervisor é uma camada independente que audita o fluxo já executado. Ele não substitui guardrails. Ele verifica se a jornada foi correta.

Na planilha:

- Supervisor VAS Avulso
- Avalia se o cancelamento foi feito corretamente
- Retorna `CONFORME`, `SUSPEITO` ou `PROBLEMA`

### 2.6 LLM-as-a-judge

É uma avaliação normalmente batch, pós-sessão, para medir qualidade, tom, alucinação, satisfação e aderência à rubrica.

Na planilha:

- Sentimento CSI
- Taxa de Alucinação
- Qualidade da Resposta
- Tom de Voz

## 3. Arquitetura recomendada

```text
User Input
  ↓
Input Rails
  ├─ Regex: PII Masking
  ├─ LLM: Toxicidade
  └─ LLM: Out-of-Scope
  ↓
LLM principal via NeMo Guardrails
  ↓
Output Rails
  ├─ Compliance Anatel
  ├─ Verbalização Prematura
  └─ Groundedness
  ↓
Python Rules
  ├─ Alçada de Ajuste
  └─ Consistência Histórica
  ↓
Execução de API / Backend
  ↓
Supervisor VAS Avulso
  ↓
Curadoria / Métricas
  ├─ TCR
  ├─ Fallback
  ├─ Tokens
  ├─ Tamanho de mensagem
  └─ Eficiência RAG
  ↓
Resposta final
```

## 4. Estrutura do projeto 

```text
nemo_guardrails_tracing_project/
├── config/
│   ├── config.yml
│   ├── rails.co
│   └── guardrails_catalog.json
├── src/
│   ├── app.py
│   ├── deterministic_rails.py
│   ├── supervisor.py
│   ├── curadoria.py
│   ├── tracing.py
│   └── settings.py
├── tests/
│   └── test_guardrails.py
├── scripts/
│   ├── run_demo.sh
│   └── run_tests.sh
├── requirements.txt
├── .env.example
└── README.md
```

## 5. Preparação do ambiente

### 5.1 Criar ambiente Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5.2 Configurar variáveis

```bash
cp .env.example .env
```

Variáveis principais:

```bash
OPENAI_API_BASE=http://127.0.0.1:8051/v1
OPENAI_BASE_URL=http://127.0.0.1:8051/v1
OPENAI_API_KEY=dummy
OPENAI_MODEL=gpt-4.1
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006/v1/traces
ENABLE_TRACING=true
USE_MOCK_LLM=false
ALCADA_MAX_AJUSTE=50
```

>**Nota Importante:** O Nemo Guardrails possui compatibilidade apenas com a API da OpenAI. É possível utilizar-se de modelos que não tenham compatibilidade com API OpenAI, bastando para isso utilizar-se do proxy OCI OpenAI desta documentação: [https://github.com/hoshikawa2/nemo_guardrails_oci_generative_ai](https://github.com/hoshikawa2/nemo_guardrails_oci_generative_ai)

## 6. Configuração do NeMo Guardrails

Arquivo: `config/config.yml`

```yaml
models:
  - type: main
    engine: openai
    model: ${OPENAI_MODEL}

instructions:
  - type: general
    content: |
      Você é um assistente de atendimento de telecom. Responda em português, com clareza,
      sem prometer ajustes antes de validação, sem expor dados sensíveis e sem tratar temas fora do escopo.

rails:
  input:
    flows:
      - self check input
  output:
    flows:
      - self check output
```

## 7. Rails criados a partir da planilha

### 7.1 MSK — PII Masking

Implementação: `src/deterministic_rails.py`

```python
CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
PASSWORD_RE = re.compile(r"(?i)(senha|password|token|api[_-]?key)\s*[:=]\s*\S+")
```

Objetivo: mascarar CPF, cartão, senha, token e credenciais antes de enviar ao LLM e antes de logar.

### 7.2 CMP — Compliance Anatel

Implementação: `enforce_compliance_anatel()`

Regra: respostas de ajuste precisam conter número de protocolo.

### 7.3 ADJ — Alçada de Ajuste

Implementação: `validar_alcada()`

Regra: se o valor do ajuste exceder `ALCADA_MAX_AJUSTE`, o fluxo é bloqueado e escalado para atendimento humano.

### 7.4 REVPREC — Verbalização Prematura

Implementação: `verbalizacao_prematura()`

Regra: o agente não pode prometer ajuste, crédito ou cancelamento antes de validação.

### 7.5 Supervisor VAS Avulso

Implementação: `src/supervisor.py`

Avalia cinco regras:

1. O VAS cancelado corresponde ao item solicitado.
2. Não houve promessa antes da validação.
3. Resposta de ajuste contém protocolo.
4. Não houve exposição de PII.
5. A decisão está coerente com os dados de contexto.

## 8. Integração com proxy OpenAI-Compatible

O projeto usa o cliente `openai` apontando para seu proxy:

```python
client = OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_api_base
)
```

Configuração:

```bash
export OPENAI_API_BASE=http://127.0.0.1:8051/v1
export OPENAI_BASE_URL=http://127.0.0.1:8051/v1
export OPENAI_API_KEY=dummy
export OPENAI_MODEL=gpt-4.1
```

## 9. Tracing com OpenTelemetry / Phoenix

Arquivo: `src/tracing.py`

Cada etapa cria spans:

- `rail.input.msk`
- `rail.python.alcada`
- `llm.nemo.generate`
- `rail.output.verbalizacao_prematura`
- `rail.output.compliance_anatel`
- `supervisor.vas_avulso`

Configuração:

```bash
export ENABLE_TRACING=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006/v1/traces
```

## 10. Como executar o projeto

### 10.1 Teste demonstrável sem proxy

```bash
export USE_MOCK_LLM=true
export ENABLE_TRACING=false
python -m src.app
```

Resultado esperado:

```json
{
  "allowed": true,
  "input_sanitized": "Cancelar VAS. CPF [CPF_MASCARADO]",
  "output": "Cancelamento analisado. Ajuste elegível conforme validação. Protocolo nº 123456789.",
  "metrics": {
    "tcr": "CONCLUIDO"
  }
}
```

### 10.2 Executar testes automatizados

```bash
pytest -q
```

Os testes comprovam:

- CPF é mascarado.
- Alçada bloqueia valor acima do limite.
- Compliance Anatel bloqueia ajuste sem protocolo.
- Verbalização prematura é bloqueada.
- Fluxo completo funciona em modo mock.

### 10.3 Executar com proxy real

```bash
export USE_MOCK_LLM=false
export OPENAI_API_BASE=http://127.0.0.1:8051/v1
export OPENAI_BASE_URL=http://127.0.0.1:8051/v1
export OPENAI_API_KEY=dummy
export OPENAI_MODEL=gpt-4.1
python -m src.app
```

![img.png](img.png)

```bash
bash scripts/run_tests.sh
```

![img_1.png](img_1.png)

## 11. Mapeamento da planilha para implementação

| Código | Item | Mecanismo | Implementação entregue |
|---|---|---|---|
| MSK | PII Masking | NeMo regex rail | Regex Python + pré-LLM |
| CMP | Compliance Anatel | NeMo output rail | Output rail determinístico |
| ADJ | Alçada de Ajuste | Python | Pré-execução Python |
| REVPREC | Supervisor VAS Avulso | LLM Supervisor | `src/supervisor.py` |
| TCR | Conclusão de Tarefa | Python | `src/curadoria.py` |
| REVPREC | Verbalização Prematura | NeMo LLM rail | Output rail determinístico + expansível |
| TOX | Toxicidade | NeMo LLM rail | `self_check_input` |
| OOS | Out-of-Scope | NeMo LLM rail | `self_check_input` |
| GND | Groundedness | NeMo LLM rail | `self_check_output`, com dependência de chunks RAG |
| HIST | Consistência Histórica | Python | previsto como regra pré-execução |
| CSI | Sentimento | LLM-as-a-judge | previsto como batch D-1 |
| ALUC | Taxa de Alucinação | LLM-as-a-judge | previsto como batch D-1 |
| RQLT | Qualidade da Resposta | LLM-as-a-judge | previsto como batch D-1 |
| VCTN | Tom de Voz | LLM-as-a-judge | previsto como batch D-1 |

## 12. Recomendações para o time

### 12.1 Não colocar tudo no LLM

Use Python para regras determinísticas e financeiras. Use LLM rails para semântica, linguagem, escopo e groundedness.

### 12.2 Separar bloqueio de medição

Guardrail bloqueia. Curadoria mede. Supervisor audita. Judge avalia em lote.

### 12.3 Começar por P0

Primeira entrega sugerida:

1. PII Masking
2. Compliance Anatel
3. Alçada de Ajuste
4. Supervisor VAS Avulso
5. TCR
6. Verbalização Prematura

### 12.4 Evoluir para P1

Depois:

1. Toxicidade
2. Out-of-Scope
3. Groundedness
4. Histórico
5. Tokens
6. Eficiência NLU
7. No-Match RAG

## 13. Critérios de aceite

O time deve comprovar:

- Dados sensíveis não chegam ao LLM sem máscara.
- Ajuste acima da alçada não é executado.
- Resposta de ajuste sem protocolo é bloqueada.
- Promessa antes da validação é bloqueada.
- Supervisor retorna status estruturado.
- Métricas de curadoria são geradas.
- Spans aparecem no backend de tracing.

## 14. Evolução futura

A estrutura permite evoluir para:

- NeMo Server.
- LangGraph.
- MCP tools.
- RAG com groundedness por chunk.
- Batch judges D-1.
- Phoenix / Langfuse / OpenTelemetry.
- Governança por catálogo de guardrails.

## 15. Referências

- NVIDIA NeMo Guardrails: documentação oficial.
- Python SDK: `RailsConfig.from_path()` e `LLMRails.generate()`.
- Colang: linguagem para definir fluxos de guardrails.
- OpenTelemetry: tracing distribuído por spans.
