from Backend.core.llm_client import get_llm_client, LLMError

def run_example_agent():
    print("Initializing Example Agent...")
    try:
        client = get_llm_client()
        # Simple prompt to verify connectivity
        response = client.generate("Say hello to the FinanceAI Agent user!")
        print(f"Agent Response: {response}")
    except LLMError as e:
        print(f"Agent failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    run_example_agent()
