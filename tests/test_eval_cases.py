"""Offline sanity checks of the live evaluation cases against the example CV fixture."""

from pathlib import Path

import pytest

from eval_cases import CASES

CV = (Path(__file__).parent / "fixtures" / "example_cv.md").read_text(encoding="utf-8").lower()


def ids(case: dict) -> str:
    return f"{case['lang']}-{case['kind']}-{case['question'][:30]}"


@pytest.mark.parametrize("case", [c for c in CASES if c["kind"] == "known"], ids=ids)
def test_known_answers_are_in_the_document(case):
    assert any(s.lower() in CV for s in case["expect_any"])


@pytest.mark.parametrize("case", [c for c in CASES if c["kind"] == "unknown"], ids=ids)
def test_unknown_topics_are_absent_from_the_document(case):
    assert not [s for s in case["absent"] if s.lower() in CV]


def test_battery_covers_both_languages_and_unknowns():
    assert {c["lang"] for c in CASES} == {"sv", "en"}
    assert sum(c["kind"] == "unknown" for c in CASES) >= 3
