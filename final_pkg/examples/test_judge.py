import os

from company_nemo_guardrails.judges import (
    classificar_sentimento,
    avaliar_alucinacao,
    avaliar_qualidade_resposta,
    avaliar_tom_de_voz
)

# ==========================================
# CONFIGURAÇÃO
# ==========================================

# MOCK = true -> usa mock local
# MOCK = false -> usa OCI/OpenAI real

os.environ["USE_MOCK_LLM"] = "false"

# Se quiser usar o proxy real:
#
# os.environ["USE_MOCK_LLM"] = "false"
# os.environ["OPENAI_BASE_URL"] = "http://localhost:8051/v1"
# os.environ["OPENAI_API_KEY"] = "dummy"
# os.environ["OPENAI_MODEL"] = "gpt-5"


# ==========================================
# HELPER
# ==========================================

def print_result(title, result):

    print("\n" + "=" * 80)
    print(f"🧪 TESTE: {title}")
    print("=" * 80)

    print(f"CODE           : {result.code}")
    print(f"ALLOWED        : {result.allowed}")
    print(f"REASON         : {result.reason}")
    print(f"MECHANISM      : {result.mechanism}")
    print(f"SANITIZED_TEXT : {result.sanitized_text}")

    print("\nDATA:")
    print(result.data)

    print("=" * 80)

# ==========================================
# TESTE CSI
# ==========================================

def test_csi():

    result = classificar_sentimento(
        """
        Estou muito insatisfeito com o atendimento.
        Quero cancelar meu plano imediatamente.
        """
    )

    print_result("CSI - Sentimento Negativo", result)


# ==========================================
# TESTE ALUCINAÇÃO
# ==========================================

def test_alucinacao():

    result = avaliar_alucinacao(
        resposta="""
        O cliente pode cancelar em até 30 dias sem multa.
        """,

        dados_reais="""
        O cliente pode cancelar em até 7 dias sem multa.
        """
    )

    print_result("ALUC - Alucinação Detectada", result)


# ==========================================
# TESTE QUALIDADE
# ==========================================

def test_qualidade():

    result = avaliar_qualidade_resposta(
        pergunta="""
        Como faço para cancelar meu plano?
        """,

        resposta="""
        Para cancelar seu plano,
        acesse o portal do cliente,
        vá até a seção Financeiro
        e clique em Cancelamento.
        """
    )

    print_result("RQLT - Qualidade Resposta", result)


# ==========================================
# TESTE TOM DE VOZ
# ==========================================

def test_tom_voz():

    result = avaliar_tom_de_voz(
        """
        Se vira. Não posso fazer nada por você.
        """
    )

    print_result("VCTN - Tom Inadequado", result)


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    test_csi()

    test_alucinacao()

    test_qualidade()

    test_tom_voz()
