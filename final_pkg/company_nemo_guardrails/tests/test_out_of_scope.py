from company_nemo_guardrails import create_rails
import pytest
from conftest import extract_return_values
@pytest.mark.parametrize("msg", [
    "Qual a capital da França?",
    "Me fale sobre física quântica"
])
def test_out_of_scope(rails, msg):
    response = rails.generate(
        messages=[{"role": "user", "content": msg}],
        options={"log": {"activated_rails": True}}
    )

    feedback = extract_return_values(response)

    oos = [f for f in feedback if f["action"] == "detectar_out_of_scope"]

    assert len(oos) > 0