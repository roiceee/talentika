#!/usr/bin/env python3
"""Format pytest -v output: class::test names, green PASSED, right-aligned %."""
import sys
import re
import shutil

WIDTH  = shutil.get_terminal_size((120, 24)).columns
GREEN  = "\033[32m"
RED    = "\033[31m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# Matches optional/path/file.py::ClassName::test_name PASSED [ 6%]
RESULT_RE = re.compile(
    r'^(?:[^\s]*\.py::)?(\w+::test_\w+)\s+(PASSED|FAILED|ERROR)\s+\[\s*(\d+)%\s*\]'
)

for raw in sys.stdin:
    line = raw.rstrip("\n")
    m = RESULT_RE.match(line)
    if m:
        test_id, verdict, pct = m.group(1), m.group(2), m.group(3)
        color   = GREEN if verdict == "PASSED" else RED
        pct_str = f"[{pct}%]"

        left      = f"{test_id}  {BOLD}{color}{verdict}{RESET}"
        right     = f"{color}{pct_str}{RESET}"
        left_vis  = len(test_id) + 2 + len(verdict)
        right_vis = len(pct_str)
        pad       = max(1, WIDTH - left_vis - right_vis)

        print(f"{left}{' ' * pad}{right}")
    else:
        print(line)
