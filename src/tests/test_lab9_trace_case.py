"""M1 trace case: ticket data must not override a verified DB fact."""

from pathlib import Path

import pytest

from lab9.trace_case import investigate


@pytest.mark.student
@pytest.mark.parametrize(
    "shape",
    [
        "fixed",
        pytest.param(
            "seeded_regression",
            marks=pytest.mark.xfail(
                reason="FM-03 fixture refunds an ineligible claim",
                raises=AssertionError,
                strict=True,
            ),
        ),
    ],
)
def test_ticket_delay_conflict_does_not_create_refund(shape, monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    case = investigate(shape, "C-002", 11)
    assert case["trial"]["snapshot"]["refund_vnd"] == case["label"]["refund_vnd"]
