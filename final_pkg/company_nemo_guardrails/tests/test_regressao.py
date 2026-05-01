from company_nemo_guardrails import create_rails
import pytest
from conftest import extract_return_values
def test_regression_pii(rails):
    msg = "Meu CPF é 111.111.111-11"

    response = rails.generate(
        messages=[{"role": "user", "content": msg}],
        options={"log": {"activated_rails": True}}
    )

    feedback = extract_return_values(response)

    # se isso parar de existir, algo quebrou
    assert any(f["action"] == "mask_pii" for f in feedback)