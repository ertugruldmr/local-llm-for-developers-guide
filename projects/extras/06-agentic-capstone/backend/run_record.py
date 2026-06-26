"""P6 · Agentic Capstone — run-record contract + evaluation stub.

SKELETON ONLY. This package's deliverable is a *documented agent run*, not new
runtime code. The schema below captures that run; `evaluate()` will run the
agent-generated backend's offline pytest and report pass/fail. Body raises
NotImplementedError. See ../.docs/001.spec-context.md and ../../p6-agentic-capstone.md.

Note: typing.Optional / explicit list[...] kept 3.9-importable per repo convention.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class SteeringMoment(BaseModel):
    step: str
    issue: str
    human_action: str  # what the human did to unblock
    autonomous: Literal[False] = False  # steering = not autonomous, by definition


class AgentRunRecord(BaseModel):
    path: Literal["claude-code", "opencode"]
    model: str
    steps_total: int
    steps_autonomous: int
    steering_moments: list[SteeringMoment]
    backend_tests_pass: bool


def evaluate(generated_dir: Path) -> AgentRunRecord:
    """Run the agent-generated backend's offline pytest and fill the run record.

    `generated_dir` points at the agent's output (a regenerated P1 backend).
    """
    raise NotImplementedError(
        "run the generated backend's pytest and assemble the AgentRunRecord"
    )
