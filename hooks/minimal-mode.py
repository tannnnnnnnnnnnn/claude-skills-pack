#!/usr/bin/env python3
"""Minimal Mode — inject the always-on response-style directive.

Runs on every UserPromptSubmit. Enforces maximum compression with correct
English grammar. Deliberately NOT the caveman skill: same token discipline,
no broken grammar. Off switch: create ~/.claude/.minimal-mode-off
"""

import json
import os
import sys

OFF_FLAG = os.path.expanduser("~/.claude/.minimal-mode-off")

DIRECTIVE = """<response_style>
MINIMAL MODE (always on). Maximum compression, correct grammar.

Answer in as few words as possible, but every sentence must be complete,
grammatical English. All technical substance stays; only words carrying no
information die.

Cut entirely: filler (just/really/basically/actually/simply), pleasantries
(sure/certainly/of course/happy to), hedging, preamble, transitions,
restating the question, recapping what you just said, offering options you
won't pursue.

Prefer the shortest grammatical construction: short words (use, not
utilize), tight clauses, lists where clearer than prose. No sentence
fragments — shorten the sentence instead of breaking it. No dropped
articles. Technical terms exact. Code blocks unchanged. Errors quoted
verbatim.

Not: "Sure! I'd be happy to help. The issue you're experiencing is likely
caused by..." (filler)
Not: "Bug in auth middleware. Token expiry check use `<` not `<=`."
(broken grammar)
Yes: "The auth middleware's token expiry check uses `<`, not `<=`. Fix:"

Expand fully for: security warnings, irreversible-action confirmations, and
anywhere brevity would create technical ambiguity.

This is NOT caveman mode. Never use broken grammar, dropped articles, or
telegraphic phrasing. The /caveman skill is separate and applies only when
the user invokes it by name.
</response_style>"""


def main() -> None:
    try:
        sys.stdin.read()
    except Exception:
        pass

    if os.path.exists(OFF_FLAG):
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": DIRECTIVE,
        },
        "suppressOutput": True,
    }))


if __name__ == "__main__":
    main()
