"""Entry point for the Becoming Itumeleng agent."""

import sys
from agent import agent


def main():
    """Run the Becoming Itumeleng agent."""
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        response = agent(user_input)
        print(response)
    else:
        print("=" * 60)
        print("  Becoming Itumeleng")
        print("  Your AI powered stylist, life coach, and")
        print("  accountability partner.")
        print("  Type 'quit' or 'exit' to end the session.")
        print("=" * 60)
        print()
        print("Hey girl! What are we working on today? 💜")
        print()

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("quit", "exit", "bye"):
                    print("
Remember: learning is the lifestyle. Go be great! 🚀")
                    break
                response = agent(user_input)
                print(f"
Becoming Itumeleng: {response}
")
            except KeyboardInterrupt:
                print("

Session ended. You're doing amazing. Keep going! 💜")
                break


if __name__ == "__main__":
    main()

