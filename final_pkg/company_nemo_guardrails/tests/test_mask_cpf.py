from company_nemo_guardrails import create_rails
import pytest
def test_mask_cpf(rails):
    msg = "Meu CPF é 169.323.728-86"

    response = rails.generate(
        messages=[{"role": "user", "content": msg}],
        options={"log": {"activated_rails": True}}
    )

    feedback = extract_return_values(response)

    pii = [f for f in feedback if f["action"] == "mask_pii"]

    assert len(pii) > 0

    for item in pii:
        assert item["sanitized_text"] is not None
        assert "169.323.728-86" not in item["sanitized_text"]