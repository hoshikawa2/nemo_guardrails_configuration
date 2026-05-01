import pytest
from nemoguardrails import LLMRails, RailsConfig

from pathlib import Path

@pytest.fixture(scope="session")
def rails():
    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / "config"

    config = RailsConfig.from_path(str(config_path))
    return LLMRails(config)


def extract_return_values(response):
    results = []

    assert response.log is not None

    for rail in response.log.activated_rails:
        for action in rail.executed_actions:
            rv = action.return_value
            if rv is not None:
                results.append({
                    "action": action.action_name,
                    "allowed": getattr(rv, "allowed", None),
                    "reason": getattr(rv, "reason", None),
                    "sanitized_text": getattr(rv, "sanitized_text", None),
                    "code": getattr(rv, "code", None),
                    "mechanism": getattr(rv, "mechanism", None),
                    "data": getattr(rv, "data", None)
                })

    return results