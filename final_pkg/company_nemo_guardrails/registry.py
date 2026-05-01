from pathlib import Path
import yaml
def load_guardrail_registry(path=None):
    if path is None: path=Path(__file__).resolve().parent.parent/'config'/'guardrails.yaml'
    with open(path,'r',encoding='utf-8') as f: return yaml.safe_load(f)['guardrails']
