import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # optional

from bot import FinanceBot

BANNER = """\
FinanceDesk - finance & business expert (LangChain + Gemini)
Type a question. Commands: /reset  /exit
------------------------------------------------------------"""


def main() -> int:
    try:
        bot = FinanceBot()
    except Exception as exc:
        print(f"Failed to start: {exc}", file=sys.stderr)
        print("Set GOOGLE_API_KEY (or GEMINI_API_KEY) and install requirements.", file=sys.stderr)
        return 1

    print(BANNER)
    while True:
        try:
            user = input("\nyou > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return 0

        if not user:
            continue
        if user == "/exit":
            print("bye")
            return 0
        if user == "/reset":
            bot.reset()
            print("(conversation reset)")
            continue

        print("\nbot > ", end="", flush=True)
        try:
            for chunk in bot.stream(user):
                print(chunk, end="", flush=True)
            print()
        except Exception as exc:
            print(f"\n[error] {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())