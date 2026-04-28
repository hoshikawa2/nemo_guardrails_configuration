#https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/actions/index.html
#https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/actions/registering-actions.html
#https://docs.nvidia.com/nemo/guardrails/latest/observability/logging/index.html

from nemoguardrails import LLMRails, RailsConfig

config = RailsConfig.from_path("./config")
rails = LLMRails(config)

def extract_return_values(response):
    results = []

    log = response.log

    for rail in log.activated_rails:
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

MESSAGE = "Meu CPF é 169.323.728-86"

response = rails.generate(
    messages=[{"role": "user", "content": MESSAGE}],
    options={
        "output_vars": ["triggered_input_rail", "relevant_chunks"],
        "log": {
            "activated_rails": True,
            "llm_calls": True
        }
    }
)

feedback = extract_return_values(response)

for f in feedback:
    print(f)
