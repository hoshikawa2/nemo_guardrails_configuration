from company_nemo_guardrails import create_rails
import pytest
from conftest import extract_return_values
def test_valor_acima_alcada(rails):
    response = rails.generate(
        messages=[{"role": "user", "content": "Quero dar desconto de 500 reais"}],
        context={"ajuste_valor": 500},
        options={"log": {"activated_rails": True}}
    )

    feedback = extract_return_values(response)

    alcada = [f for f in feedback if f["action"] == "validar_alcada"]

    assert len(alcada) > 0
    assert any(f["allowed"] is False for f in alcada)