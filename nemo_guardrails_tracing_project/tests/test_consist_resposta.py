import pytest
from conftest import extract_return_values
def test_response_not_empty(rails):
    response = rails.generate(
        messages=[{"role": "user", "content": "Oi"}]
    )

    assert response is not None
    assert hasattr(response, "response")