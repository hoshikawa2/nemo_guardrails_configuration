from company_nemo_guardrails import create_rails
import pytest
from conftest import extract_return_values
def test_log_structure(rails):
    response = rails.generate(
        messages=[{"role": "user", "content": "teste"}],
        options={"log": {"activated_rails": True, "llm_calls": True}}
    )

    assert response.log is not None
    assert hasattr(response.log, "activated_rails")