#!/usr/bin/env python3
"""Recommend local models for a task, sized to the host's RAM.

Reads model standings from the repo's `model-table.md` at runtime (the single
source of truth — CLAUDE.md guardrail #4). Detects the host chip and unified/
total RAM, then prints a ranked recommendation per task, filtered to what fits
with headroom.

Run:
    python recommend_models.py                 # all tasks
    python recommend_models.py --task coding    # one task
    python recommend_models.py --ram-gb 16      # override detected RAM
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

TASKS = ("coding", "turkish", "rag")

# Map a --task flag to the row label used in model-table.md's by-task table.
TASK_ROW_PATTERNS: dict[str, re.Pattern[str]] = {
    "coding": re.compile(r"coding", re.IGNORECASE),
    "turkish": re.compile(r"turkish", re.IGNORECASE),
    "rag": re.compile(r"\brag\b|embedding", re.IGNORECASE),
}

# The hardware table's RAM column buckets the *machine* (8/16/48/80 GB), and
# each tier's pick already leaves OS/KV-cache headroom. So we match the host to
# the largest tier it qualifies for, rather than treating the number as a model
# footprint. A small slack lets a 48 GB Mac still claim the "48 GB" tier despite
# a few hundred MB of reporting variance.
TIER_SLACK_GB = 2.0

TBD_MARKERS = ("_tbd_", "tbd", "_todo_", "—", "-")


@dataclass
class HostInfo:
    chip: str
    total_ram_gb: float
    detected: bool  # False if we fell back to an override or a guess


@dataclass
class HardwareRow:
    ram_gb: float  # the RAM tier this row targets
    pick: str
    quant: str
    good_for: str


@dataclass
class TaskRow:
    task_label: str
    pick: str
    notes: str


@dataclass
class ModelTable:
    hardware_rows: list[HardwareRow] = field(default_factory=list)
    task_rows: list[TaskRow] = field(default_factory=list)
    parse_notes: list[str] = field(default_factory=list)


def detect_host(ram_override_gb: float | None) -> HostInfo:
    """Detect chip + total RAM. macOS via sysctl; cross-platform fallback."""
    chip = platform.processor() or platform.machine() or "unknown"
    total_ram_gb: float | None = None
    detected = True

    if sys.platform == "darwin":
        chip = _sysctl("machdep.cpu.brand_string") or chip
        memsize = _sysctl("hw.memsize")
        if memsize and memsize.isdigit():
            total_ram_gb = int(memsize) / (1024**3)

    if total_ram_gb is None:
        total_ram_gb = _fallback_ram_gb()
        detected = total_ram_gb is not None
        if not detected:
            chip = f"{chip} (cpus={os.cpu_count()})"

    if ram_override_gb is not None:
        total_ram_gb = ram_override_gb
        detected = False  # explicit override, not auto-detected

    return HostInfo(chip=chip, total_ram_gb=total_ram_gb or 0.0, detected=detected)


def _sysctl(key: str) -> str | None:
    try:
        out = subprocess.run(
            ["sysctl", "-n", key],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return out.stdout.strip() or None
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return None


def _fallback_ram_gb() -> float | None:
    """Best-effort RAM detection off macOS, stdlib only."""
    # Linux: /proc/meminfo
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        try:
            for line in meminfo.read_text().splitlines():
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return kb / (1024**2)
        except (OSError, ValueError, IndexError):
            pass
    # POSIX sysconf (Linux/some Unix)
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        if pages > 0 and page_size > 0:
            return pages * page_size / (1024**3)
    except (ValueError, OSError, AttributeError):
        pass
    return None


def find_repo_root(start: Path) -> Path:
    """Walk up until we find model-table.md (or hit the filesystem root)."""
    for parent in [start, *start.parents]:
        if (parent / "model-table.md").is_file():
            return parent
    # Fall back to two levels up from this file (projects/00-serve-lmstudio/).
    return start.parents[1] if len(start.parents) >= 2 else start


def _is_tbd(cell: str) -> bool:
    return cell.strip().lower() in TBD_MARKERS or not cell.strip()


def _split_row(line: str) -> list[str]:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def _ram_gb_from_cell(cell: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*GB", cell, re.IGNORECASE)
    return float(m.group(1)) if m else None


def parse_model_table(path: Path) -> ModelTable:
    """Parse the two markdown tables in model-table.md.

    The canonical table is a living scaffold: cells may be `_TBD_`. We parse
    every column we can and record what was empty so the CLI can degrade
    gracefully instead of crashing.
    """
    table = ModelTable()
    if not path.is_file():
        table.parse_notes.append(f"model-table.md not found at {path}")
        return table

    lines = path.read_text(encoding="utf-8").splitlines()
    section: str | None = None

    for line in lines:
        low = line.lower()
        if low.startswith("## recommendation by hardware"):
            section = "hardware"
            continue
        if low.startswith("## recommendation by task"):
            section = "task"
            continue
        if line.startswith("## "):
            section = None
            continue

        if not line.lstrip().startswith("|"):
            continue
        cells = _split_row(line)
        if len(cells) < 2:
            continue
        # Skip header + separator rows.
        joined = "".join(cells).lower()
        if set(joined) <= set("-: ") or "ram" in cells[0].lower() and "vram" in joined:
            continue
        if section == "hardware" and cells[0].lower().startswith("unified"):
            continue
        if section == "task" and cells[0].lower() == "task":
            continue

        if section == "hardware" and len(cells) >= 4:
            ram = _ram_gb_from_cell(cells[0])
            if ram is None:
                continue
            table.hardware_rows.append(
                HardwareRow(
                    ram_gb=ram,
                    pick=cells[1],
                    quant=cells[2],
                    good_for=cells[3],
                )
            )
        elif section == "task" and len(cells) >= 3:
            table.task_rows.append(
                TaskRow(task_label=cells[0], pick=cells[1], notes=cells[2])
            )

    if all(_is_tbd(r.pick) for r in table.hardware_rows) and table.hardware_rows:
        table.parse_notes.append(
            "model-table.md hardware picks are all _TBD_ (scaffold not yet filled)."
        )
    if all(_is_tbd(r.pick) for r in table.task_rows) and table.task_rows:
        table.parse_notes.append(
            "model-table.md by-task picks are all _TBD_ (scaffold not yet filled)."
        )
    return table


def fitting_hardware_rows(table: ModelTable, total_ram_gb: float) -> list[HardwareRow]:
    """Hardware tiers the host qualifies for (tier RAM ≤ host RAM), best first."""
    fits = [r for r in table.hardware_rows if r.ram_gb <= total_ram_gb + TIER_SLACK_GB]
    return sorted(fits, key=lambda r: r.ram_gb, reverse=True)


def task_row_for(table: ModelTable, task: str) -> TaskRow | None:
    pat = TASK_ROW_PATTERNS[task]
    for row in table.task_rows:
        if pat.search(row.task_label):
            return row
    return None


def recommend(table: ModelTable, host: HostInfo, task: str) -> list[str]:
    """Build the human-readable recommendation lines for one task."""
    lines: list[str] = [f"## Task: {task}"]

    task_row = task_row_for(table, task)
    if task_row is None:
        lines.append(f"  (no '{task}' row found in model-table.md)")
    elif _is_tbd(task_row.pick):
        note = task_row.notes if not _is_tbd(task_row.notes) else ""
        lines.append(f"  by-task pick: not yet set in model-table.md (_TBD_)."
                     + (f" Selection note: {note}" if note else ""))
    else:
        lines.append(f"  by-task pick: {task_row.pick}  ({task_row.notes})")

    fits = fitting_hardware_rows(table, host.total_ram_gb)
    if not fits:
        lines.append(
            f"  No hardware tier fits {host.total_ram_gb:.0f} GB. "
            f"Try a smaller quant or the smallest model in the table."
        )
        return lines

    lines.append(
        f"  Hardware tiers your {host.total_ram_gb:.0f} GB machine qualifies for "
        f"(largest first):"
    )
    for rank, row in enumerate(fits, start=1):
        pick = row.pick if not _is_tbd(row.pick) else "(pick _TBD_ in model-table.md)"
        quant = row.quant if not _is_tbd(row.quant) else "?"
        good = row.good_for if not _is_tbd(row.good_for) else ""
        reason = f"fits {row.ram_gb:.0f} GB tier"
        if good:
            reason += f"; good for {good}"
        lines.append(f"    {rank}. {pick} [{quant}] — {reason}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recommend local models for a task, sized to host RAM "
        "(reads model-table.md as the source of truth)."
    )
    parser.add_argument(
        "--task",
        choices=TASKS,
        help="One of: coding, turkish, rag. Default: print all three.",
    )
    parser.add_argument(
        "--ram-gb",
        type=float,
        default=None,
        help="Override detected total RAM (GB), e.g. to size for another box.",
    )
    parser.add_argument(
        "--model-table",
        type=Path,
        default=None,
        help="Path to model-table.md (default: auto-discover from repo root).",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    table_path = args.model_table or (find_repo_root(here) / "model-table.md")

    host = detect_host(args.ram_gb)
    table = parse_model_table(table_path)

    print("# Local model recommendation")
    src = "auto-detected" if host.detected else "override / fallback"
    print(f"Host: {host.chip} · {host.total_ram_gb:.0f} GB RAM ({src})")
    print(f"Model table: {table_path}")
    if table.parse_notes:
        print("Notes:")
        for note in table.parse_notes:
            print(f"  - {note}")
    print()

    tasks = [args.task] if args.task else list(TASKS)
    for task in tasks:
        for line in recommend(table, host, task):
            print(line)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
