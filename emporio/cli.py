from __future__ import annotations

import argparse
import json
from getpass import getpass

from .config import Settings
from .service import AgentService


def main() -> None:
    parser = argparse.ArgumentParser(description="KONAET Music")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="Start the local web interface and API")
    serve.add_argument("--port", type=int, default=8000)
    chat = commands.add_parser("chat", help="Use the agent in a terminal")
    chat.add_argument("--language", choices=["en", "pt"], default="en")
    commands.add_parser("ingest", help="Validate and import source data")
    commands.add_parser("verify-audit", help="Verify the local evidence hash chain")
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.command == "serve":
        import os
        os.environ.setdefault("KONAET_PUBLIC_URL", f"http://127.0.0.1:{args.port}")
        settings = Settings.from_env()
        import uvicorn
        from .api import create_app
        uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port, access_log=False)
        return
    agent = AgentService(settings)
    if args.command == "ingest":
        print(json.dumps(agent.data_report, indent=2))
        return
    if args.command == "verify-audit":
        result = agent.store.verify_audit()
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["valid"] else 1)
    session = agent.store.session()
    print("KONAET Music. /verify, /reset, /quit. " + ("Respostas em português." if args.language == "pt" else "Answers are in English."))
    while True:
        try:
            text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text == "/quit":
            break
        if text == "/reset":
            agent.store.forget_session(session["id"])
            session = agent.store.session()
            print("Conversation cleared.")
            continue
        if text == "/verify":
            try:
                order_id = int(input("Order number: "))
                email = getpass("Purchase email (hidden): ")
                session = agent.store.session(session["id"])
                valid = agent.store.verify_order(session, order_id, email)
                print("Verified." if valid else "Could not verify those details.")
            except ValueError:
                print("Enter a numeric order number.")
            continue
        if not text:
            continue
        try:
            result = agent.turn(text, session["id"], locale=args.language)
            print("\nEmpório: " + result["message"])
            if result["sources"]:
                print("Sources: " + "; ".join(s["label"] for s in result["sources"]))
        except ValueError as exc:
            print(str(exc))


if __name__ == "__main__":
    main()
