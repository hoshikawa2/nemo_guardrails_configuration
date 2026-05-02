from company_nemo_guardrails import create_rails

def main():
    tests = []

    messages = [
        {
            "role": "context",
            "content": {"ajuste_valor": 1000, "limite": 50}
        },
        {
            "role": "user",
            "content": "quero um desconto de R$ 1000,00 no meu plano"
        }
    ]

    tests.append(messages)

    messages = [
            {
                "role": "context",
                "content": {"requer_protocolo": True}
            },
        {
            "role": "user",
            "content": "quero cancelar o plano"
        },
        {
            "role": "assistant",
            "content": "o plano foi cancelado sem protocolo"
        }
    ]
    tests.append(messages)

    rails = create_rails()

    response = rails.generate(
        messages=messages,
        options={
            "log": {"activated_rails": True}
        }
    )

    print(response)


if __name__ == "__main__":
    main()