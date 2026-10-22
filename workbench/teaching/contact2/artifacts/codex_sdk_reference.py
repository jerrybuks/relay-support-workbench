"""Inspect-only SDK comparison; not installed or executed by the workshop.

Source: https://learn.chatgpt.com/docs/codex-sdk
The live prepared automation uses codex exec. This optional reference requires the
separate openai-codex package/account setup; it is not a Relay runtime dependency.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Explicitly authorize an SDK model call")
    args = parser.parse_args()
    if not args.run:
        print("Reference only. Inspect this file and the official SDK docs; no model call made.")
        return
    from openai_codex import Codex, Sandbox

    with Codex() as codex:
        thread = codex.thread_start(model="gpt-6-luna", sandbox=Sandbox.read_only)
        result = thread.run(
            "Read workbench/teaching/contact2/TASK.md and explain its acceptance criteria. "
            "Do not edit files, read credentials, run provider calls or publish anything."
        )
        print(result.final_response)


if __name__ == "__main__":
    main()
