import json
import uuid

from nemoguardrails import LLMRails, RailsConfig

from src.actions import executar_pipeline_validacoes, PIPELINE_RESULTS


def build_rails():
    config = RailsConfig.from_path("./config")
    rails = LLMRails(config)

    rails.register_action(
        executar_pipeline_validacoes,
        "executar_pipeline_validacoes"
    )

    return rails


rails = build_rails()


def executar_atendimento(user_input: str, context: dict):
    request_id = str(uuid.uuid4())

    payload = {
        "request_id": request_id,
        "input_text": user_input,
        "context": context or {},
    }

    response = rails.generate(
        messages=[
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False),
            }
        ]
    )

    result = PIPELINE_RESULTS.pop(request_id, None)

    if result:
        return result

    return {
        "allowed": False,
        "label": "PROBLEMA",
        "reason": "Pipeline não retornou resultado estruturado",
        "response": response,
        "trace": [],
    }


if __name__ == "__main__":
    user_input = "quero cancelar VAS"

    context = {
        "ajuste_valor": 2000,
        "resposta_llm": "Cancelamento realizado",
    }

    print(executar_atendimento(user_input, context))