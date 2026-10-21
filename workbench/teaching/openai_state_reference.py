"""Opt-in SDK comparison of application-managed and provider-managed conversation state.

Synthetic context only. Never imported by Relay. Two generation attempts per run;
provider-managed modes attempt bounded resource cleanup even when generation fails.
"""

import argparse
import json

from .provider_connection import provider_name
from .responses_reference import live_client

MODES = ("stateless", "manual", "previous", "conversation")
INSTRUCTIONS = "Use only facts explicitly present in this conversation. If missing, say unknown."
FIRST = "Synthetic teaching example: the parcel fee is NGN 8000. Acknowledge this fact."
FOLLOW_UP = "What parcel fee did I mention? If no fee is in your context, say unknown."


class StateComparisonFailure(RuntimeError):
    def __init__(self, report):
        super().__init__("State comparison failed; inspect configuration and provider resources.")
        self.report = report


def compare_state(client, model, mode):
    if mode not in MODES:
        raise ValueError("Unknown conversation strategy")
    if provider_name(client) == "openrouter" and mode in {"previous", "conversation"}:
        raise ValueError(
            "OpenRouter supports stateless/manual replay only; "
            "this mode requires native OpenAI access."
        )
    responses = []
    conversation = None
    report = {
        "mode": mode,
        "provider": provider_name(client),
        "generation_attempts": 0,
        "response_ids": [],
        "cleanup": [],
        "quality_review": "required",
    }
    try:
        if mode == "conversation":
            conversation = client.conversations.create()
            report["conversation_id"] = conversation.id
        options = {
            "model": model,
            "instructions": INSTRUCTIONS,
            "max_output_tokens": 500,
            "store": mode in {"previous", "conversation"},
        }
        if conversation:
            options["conversation"] = conversation.id
        if mode == "manual":
            options["include"] = ["reasoning.encrypted_content"]
        report["generation_attempts"] += 1
        first = client.responses.create(input=[{"role": "user", "content": FIRST}], **options)
        responses.append(first)
        report["response_ids"].append(first.id)
        if first.status != "completed" or not first.output_text.strip():
            raise ValueError("First turn did not complete a text answer")
        second_input = [{"role": "user", "content": FOLLOW_UP}]
        if mode == "manual":
            second_input = [
                {"role": "user", "content": FIRST},
                *[item.model_dump(exclude_none=True) for item in first.output],
                *second_input,
            ]
        elif mode == "previous":
            options["previous_response_id"] = first.id
        report["generation_attempts"] += 1
        second = client.responses.create(input=second_input, **options)
        responses.append(second)
        report["response_ids"].append(second.id)
        if second.status != "completed" or not second.output_text.strip():
            raise ValueError("Follow-up did not complete a text answer")
        report["turns"] = [
            {
                "id": r.id,
                "answer": r.output_text,
                "usage": r.usage.model_dump() if r.usage else None,
            }
            for r in responses
        ]
        return report
    except Exception as error:
        raise StateComparisonFailure(report) from error
    finally:
        # Deleting a conversation object alone does not delete its items. Inspect one
        # bounded page, then delete items individually before the conversation object.
        # Never claim erasure/zero retention: failures remain visible in this report.
        if conversation:
            try:
                page = client.conversations.items.list(conversation.id, limit=20)
                if page.has_more:
                    report["cleanup"].append("incomplete: more than 20 conversation items")
                for item in page.data:
                    client.conversations.items.delete(item.id, conversation_id=conversation.id)
                if not page.has_more:
                    client.conversations.delete(conversation.id)
                    report["cleanup"].append("conversation items and object delete acknowledged")
            except Exception:
                report["cleanup"].append("conversation cleanup failed; inspect provider resources")
        if mode in {"previous", "conversation"}:
            for response in reversed(responses):
                try:
                    client.responses.delete(response.id)
                    report["cleanup"].append("response delete acknowledged")
                except Exception:
                    report["cleanup"].append("response cleanup failed; inspect provider resources")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--live", action="store_true", help="Two billable Responses attempts")
    args = parser.parse_args()
    if not args.live:
        parser.error("Explicit --live and configured credentials/model are required")
    client = None
    try:
        client, model = live_client()
        report = compare_state(client, model, args.mode)
        print(json.dumps(report, indent=2))
        return 1 if any("failed" in s or "incomplete" in s for s in report["cleanup"]) else 0
    except ValueError as error:
        print(str(error))
        return 1
    except StateComparisonFailure as error:
        print(json.dumps(error.report, indent=2))
        print(str(error))
        return 1
    except Exception:
        print("State comparison unavailable; check live opt-in, credentials and model locally.")
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
