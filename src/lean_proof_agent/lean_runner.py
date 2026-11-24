"""Run Lean on a piece of code and return its messages in structured form."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

# Every checked file starts with this header, followed by the caller's code.
HEADER = "import Mathlib\n\n"
# Number of header lines. Subtracted from Lean's line numbers
HEADER_LINES = HEADER.count("\n")

# src/lean_proof_agent/lean_runner.py -> project root -> lean_workspace
DEFAULT_PROJECT_DIR = Path(__file__).resolve().parents[2] / "lean_workspace"


# Run the provided Lean code and return its output.
# frozen=True prevents attributes from being reassigned after initialization.
# -> protects Lean's results from accidental modification (e.g. a removed sorry warning).


# Message reported by lean: error, warning or information
@dataclass(frozen=True)
class LeanMessage:
    severity: str  # "error", "warning" or "information"
    text: str
    line: int  # 1-based
    column: int  # 0-based
    kind: str = ""

    @property
    def is_error(self) -> bool:
        return self.severity == "error"

    @property
    def is_sorry(self) -> bool:
        return self.kind == "hasSorry"

    def format(self) -> str:
        """Human-readable form, e.g. '1:8: warning: declaration uses `sorry`'."""
        return f"{self.line}:{self.column}: {self.severity}: {self.text}"


# Output of checking one piece of Lean code
@dataclass(frozen=True)
class LeanResult:
    messages: tuple[LeanMessage, ...]
    returncode: int | None  # none if lean is stopped by timeout
    stderr: str
    duration_s: float  # time spent
    timed_out: bool = False

    @property
    def errors(self) -> list[LeanMessage]:
        return [m for m in self.messages if m.is_error]

    @property
    def uses_sorry(self) -> bool:
        return any(m.is_sorry for m in self.messages)

    # True only if Lean finished normally, no errors no sorry.
    #  crash or a missing toolchain produces no JSON messages -> no errors not enough.
    @property
    def is_success(self) -> bool:
        return (
            not self.timed_out
            and self.returncode == 0
            and not self.errors
            and not self.uses_sorry
        )


# Parse the output of lean --json. -> one JSON object per line
def parse_messages(stdout: str, line_offset: int = 0) -> tuple[LeanMessage, ...]:
    messages = []
    for raw_line in stdout.splitlines():
        raw_line = raw_line.strip()
        if not raw_line.startswith("{"):
            continue  # skip anything that is not a JSON message
        data = json.loads(raw_line)
        messages.append(
            LeanMessage(
                severity=data["severity"],
                text=data["data"],
                line=data["pos"]["line"] - line_offset,
                column=data["pos"]["column"],
                kind=data.get("kind", ""),
            )
        )
    return tuple(messages)


# checking the lean code
class LeanRunner:
    def __init__(
        self, project_dir: Path = DEFAULT_PROJECT_DIR, timeout_s: float = 300
    ) -> None:

        if not project_dir.is_dir():
            raise FileNotFoundError(f"Lean project not found: {project_dir}")
        self.project_dir = project_dir
        self.timeout_s = timeout_s

    # check code with lean, import Mathlib is added automatically.
    def check(self, code: str) -> LeanResult:

        start = time.perf_counter()

        # ignore_cleanup_errors: on Windows, Lean may still hold the file briefly.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            lean_file = Path(tmp_dir) / "Check.lean"
            lean_file.write_text(HEADER + code + "\n", encoding="utf-8")
            try:
                completed = subprocess.run(
                    ["lake", "env", "lean", "--json", str(lean_file)],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=self.timeout_s,
                    check=False,  # exit code 1  == Lean found errors
                )
            except subprocess.TimeoutExpired:
                return LeanResult(
                    messages=(),
                    returncode=None,
                    stderr="",
                    duration_s=time.perf_counter() - start,
                    timed_out=True,
                )

        return LeanResult(
            messages=parse_messages(completed.stdout, line_offset=HEADER_LINES),
            returncode=completed.returncode,
            stderr=completed.stderr,
            duration_s=time.perf_counter() - start,
        )
