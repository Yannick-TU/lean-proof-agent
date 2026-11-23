import anthropic
from dotenv import load_dotenv

MODEL = "claude-sonnet-5-5"

def main() -> None:
    #Load anthropic key
    load_dotenv()

    client = anthropic.Anthropic()

    response = client.messages.create(
        model = MODEL,
        max_tokens = 500, #~2000Words
        messages = [ #creates the input for the agent
            {
                "role" : "user",
                "content" : (
                    "Write a Lean 4 proof (using Mathlib) of:\n"
                    "theorem add_comm_test (a b : ℕ) : a + b = b + a\n"
                    "Answer with the Lean code only."
                ),   
            }
        ]
    )
    #answer is a list of content blocks, we expect one text block
    for block in response.content:
        if block.type == "text":
            print(block.text)
    print("---")
    print(f"Model:         {response.model}")
    print(f"Stop reason:   {response.stop_reason}")
    print(f"Input tokens:  {response.usage.input_tokens}")
    print(f"Output tokens: {response.usage.output_tokens}")


if __name__ == "__main__":
    main()    