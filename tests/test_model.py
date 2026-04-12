import anthropic

from config import LLM_API_KEY, LLM_MODEL


if __name__ == "__main__":
    client = anthropic.Anthropic(api_key=LLM_API_KEY)

    print(f"model: {LLM_MODEL}")

    print("\n--- streaming response ---")
    with client.messages.stream(
        model=LLM_MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print()
