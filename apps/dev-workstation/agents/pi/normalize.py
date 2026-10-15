#!/usr/bin/env python3
"""Normalize one Pi JSON invocation, never replayed session-history totals."""
import json
import math
import sys


def normalize(lines, process_rc=0):
    session_id = None
    settled = False
    aborted = False
    total = 0.0
    turns = 0
    last = {}
    invalid = None
    denials = []
    try:
        # File iteration splits only on LF, unlike str.splitlines (U+2028 is content).
        for line in lines:
            if not line.strip():
                continue
            event = json.loads(line)
            kind = event.get("type")
            if kind == "session":
                session_id = event.get("id")
            elif kind == "agent_start":
                settled = False
            elif kind == "agent_settled":
                settled = True
                aborted = event.get("aborted") is True
            elif kind == "message_end" and event.get("message", {}).get("role") == "assistant":
                last = event["message"]
                turns += 1
                cost = last.get("usage", {}).get("cost", {}).get("total")
                if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
                    invalid = "Pi final assistant message lacks a valid priced usage total"
                else:
                    total += cost
            elif kind == "tool_execution_end":
                result = event.get("result", {})
                text = json.dumps(result)
                if event.get("isError") and ("blocked by hook" in text.lower() or "policy blocked" in text.lower()):
                    denials.append({"tool_name": event.get("toolName", "unknown")})
    except (ValueError, TypeError, AttributeError):
        invalid = "Pi emitted malformed JSON events"
    failed = bool(process_rc or invalid or not settled or aborted or not session_id or not turns
                  or last.get("stopReason") in ("error", "aborted", "length"))
    error = invalid or last.get("errorMessage")
    if failed and not error:
        error = "Pi invocation did not settle successfully"
    text = "\n".join(b.get("text", "") for b in last.get("content", []) if b.get("type") == "text")
    return {"session_id": session_id, "cost_mode": "incremental", "total_cost_usd": total,
            "num_turns": turns, "permission_denials": denials, "is_error": failed,
            "subtype": "error" if failed else "success", "result": error if failed else text}


if __name__ == "__main__":
    result = normalize(sys.stdin)
    print(json.dumps(result, allow_nan=False))
    sys.exit(1 if result["is_error"] else 0)
