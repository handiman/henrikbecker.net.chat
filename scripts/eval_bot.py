"""Run the CV bot question battery against a running worker (real model, costs neurons).

    uv run python scripts/eval_bot.py http://localhost:8787
    INGEST_TOKEN=... uv run python scripts/eval_bot.py http://localhost:8787 --ingest

--ingest first replaces the "henrik" document with tests/fixtures/example_cv.md. Do that only
against `pywrangler dev` or a staging worker, never against production.
Exits 1 if any case fails.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent / "tests"
sys.path.insert(0, str(TESTS))

from eval_cases import CASES  # noqa: E402


def post(url: str, body: bytes, headers: dict[str, str]) -> tuple[int, str]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.status, response.read().decode()
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 2:
                return error.code, error.read().decode()
            # /ask allows 10 questions a minute per IP; wait for the window to reset.
            wait = int(error.headers.get("Retry-After", "60"))
            print(f"   rate limited, waiting {wait} s ...", flush=True)
            time.sleep(wait)
    raise AssertionError("unreachable")


def check(case: dict, answer: str) -> str | None:
    """Return why the answer fails the case, or None if it passes."""
    text = answer.lower()
    if case["kind"] in ("known", "unknown") and not any(
        s.lower() in text for s in case["expect_any"]
    ):
        return f"expected one of {case['expect_any']}"
    for forbidden in case.get("forbid", []):
        if forbidden.lower() in text:
            return f"must not contain {forbidden!r}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("base_url")
    parser.add_argument("--ingest", action="store_true")
    parser.add_argument("--collection", default="henrik")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    if args.ingest:
        token = os.environ.get("INGEST_TOKEN")
        if not token:
            sys.exit("INGEST_TOKEN must be set for --ingest")
        document = (TESTS / "fixtures" / "example_cv.md").read_bytes()
        status, _ = post(
            f"{base}/ingest/{args.collection}", document, {"Authorization": f"Bearer {token}"}
        )
        if status != 200:
            sys.exit(f"ingest failed with status {status}")

    failures = 0
    for case in CASES:
        status, body = post(
            f"{base}/ask/{args.collection}",
            json.dumps(case["question"]).encode(),
            {"Content-Type": "application/json"},
        )
        answer = ""
        if status == 200:
            answer = json.loads(body).get("answer", "")
            reason = check(case, answer)
        else:
            reason = f"status {status}"
        failures += reason is not None
        print(f"{'FAIL' if reason else 'ok  '} [{case['lang']}/{case['kind']}] {case['question']}")
        if reason:
            print(f"       {reason}\n       answer: {answer!r}")
    print(f"\n{len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
