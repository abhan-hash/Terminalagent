from langchain_core.messages import HumanMessage
from langsmith import traceable
from langgraph.types import Command

from graph import graph

from tools import sandbox

@traceable(name="human_approval")
def record_approval(action: str, details: str, answer: str) -> str:
    """Record the terminal approval decision in LangSmith."""
    return answer

def invoke_until_complete(input_value, config):
    """Run the graph, handling approval interrupts until it finishes."""
    result = graph.invoke(input_value, config=config)

    while "__interrupt__" in result:
        interrupt_request = result["__interrupt__"][0].value

        print("\nPermission request")
        print(f"Action: {interrupt_request['action']}")
        print(interrupt_request["details"])
        print(interrupt_request["question"])

        answer = input("> ").strip().lower()

        while answer not in {"y", "yes", "n", "no"}:
            print("Please answer y or n.")
            answer = input("> ").strip().lower()

        answer = record_approval(
            interrupt_request["action"],
            interrupt_request["details"],
            answer,
        )

        result = graph.invoke(
            Command(resume=answer),
            config=config,
        )

    return result


def main():
    print("Terminal agent v1. Type 'exit' or 'quit' to stop.")

    config = {"configurable": {"thread_id": "main-session"}}

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if not user_input:
            continue

        result = invoke_until_complete(
            {"messages": [HumanMessage(content=user_input)]},
            config,
        )
        answer = result["messages"][-1].content
        print(f"\nAgent: {answer}")


if __name__ == "__main__":
    sandbox.start()
    try:
        main()
    finally:
        sandbox.stop()
