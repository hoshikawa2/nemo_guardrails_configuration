
from company_nemo_guardrails import create_rails

def main():
    rails = create_rails()
    response = rails.generate(
        messages=[{"role": "user", "content": "Meu CPF é 123.456.789-00"}],
        options={"log": {"activated_rails": True}}
    )
    print(response)

if __name__ == "__main__":
    main()
