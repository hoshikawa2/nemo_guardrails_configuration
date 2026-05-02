from importlib.resources import files
from nemoguardrails import LLMRails, RailsConfig

def get_config_path():
    return str(files("company_nemo_guardrails").joinpath("config"))

def create_rails():
    # 👇 IMPORT CRÍTICO (executa decorators @action)
    from company_nemo_guardrails import actions

    config = RailsConfig.from_path(get_config_path())

    rails = LLMRails(config)

    # 👇 opcional mas recomendado (garante registro)
    rails.register_action(actions)

    return rails