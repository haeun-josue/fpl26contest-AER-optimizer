#!/usr/bin/env python3
# Copyright (C) 2026, Advanced Micro Devices, Inc. All rights reserved.
# Portions of this file consist of AI-generated content.
# SPDX-License-Identifier: Apache 2.0

"""
Data-driven test runner for the Custom Tools MCP server.

What it does
------------
1. Walks `tools/` exactly the way `server.py` does:
   skips `__init__.py` and any file whose stem starts with `_`,
   imports the rest as `tools.<stem>`, and validates the four required
   attributes (`NAME`, `DESCRIPTION`, `INPUT_SCHEMA`, `run`).

2. For each registered tool whose `NAME` matches a directory under
   `example_io/`, it loads every paired `case_<N>_input.json` /
   `case_<N>_output.json` file, calls `run(input_dict)`, and compares
   the result to the expected output via deep equality.

3. Tools without a matching `example_io/<NAME>/` directory are listed
   as skipped at the end of the run -- not failed. So shipping cases
   is recommended but not required.

Exit code: 0 if every case passes (and no orphan input/output files
are detected), 1 otherwise.
"""
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional, Tuple

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

REQUIRED_ATTRS = ("NAME", "DESCRIPTION", "INPUT_SCHEMA", "run")


def discover_tools() -> Dict[str, ModuleType]:
    """Return a {NAME: module} registry. Mirrors `server.py::_discover_tools`."""
    registry: Dict[str, ModuleType] = {}
    tools_dir = ROOT / "tools"
    if not tools_dir.is_dir():
        return registry

    for path in sorted(tools_dir.glob("*.py")):
        stem = path.stem
        if stem == "__init__" or stem.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"tools.{stem}")
        except Exception as e:
            print(f"  ! Failed to import tools.{stem}: {e}")
            continue
        missing = [a for a in REQUIRED_ATTRS if not hasattr(module, a)]
        if missing:
            print(f"  ! Skipping tools.{stem}: missing attribute(s) {missing}")
            continue
        name = module.NAME
        if name in registry:
            print(f"  ! Duplicate NAME '{name}' in tools.{stem}; aborting")
            sys.exit(1)
        registry[name] = module
    return registry


def run_examples_for(name: str, module: ModuleType) -> Optional[Tuple[int, int]]:
    """Run all paired input/output cases under example_io/<name>/.

    Returns (passed, failed), or None if no example_io dir / no cases exist
    (i.e. the tool is "skipped" rather than "failed").
    """
    case_dir = ROOT / "example_io" / name
    if not case_dir.is_dir():
        print(f"  - no example_io/{name}/ directory; skipped")
        return None

    input_files = sorted(case_dir.glob("case_*_input.json"))
    output_files = sorted(case_dir.glob("case_*_output.json"))

    if not input_files and not output_files:
        print(f"  - no case files in example_io/{name}/; skipped")
        return None

    # Detect orphan output files (output without input) so users notice typos.
    input_stems = {p.stem.removesuffix("_input") for p in input_files}
    output_stems = {p.stem.removesuffix("_output") for p in output_files}
    orphan_outputs = sorted(output_stems - input_stems)
    for orphan in orphan_outputs:
        print(f"  ! orphan {orphan}_output.json (no matching {orphan}_input.json)")

    passed = 0
    failed = len(orphan_outputs)

    for input_path in input_files:
        case_id = input_path.stem.removesuffix("_input")  # e.g. "case_1"
        expected_path = case_dir / f"{case_id}_output.json"
        if not expected_path.is_file():
            print(f"  X {case_id}: missing expected output {expected_path.name}")
            failed += 1
            continue

        try:
            arguments: Dict[str, Any] = json.loads(input_path.read_text())
            expected: Dict[str, Any] = json.loads(expected_path.read_text())
        except Exception as e:
            print(f"  X {case_id}: failed to parse JSON ({e})")
            failed += 1
            continue

        try:
            actual = module.run(arguments)
        except Exception as e:
            print(f"  X {case_id}: run() raised {type(e).__name__}: {e}")
            failed += 1
            continue

        if actual == expected:
            print(f"  OK {case_id}")
            passed += 1
        else:
            print(f"  X {case_id}")
            print(f"      input:    {json.dumps(arguments)}")
            print(f"      expected: {json.dumps(expected)}")
            print(f"      actual:   {json.dumps(actual)}")
            failed += 1

    return passed, failed


def main() -> int:
    print("Custom Tools MCP Server -- example_io test runner")
    print("=" * 60)

    registry = discover_tools()
    if not registry:
        print("No tools discovered under tools/. Nothing to test.")
        return 1

    print(f"Discovered {len(registry)} tool(s): {', '.join(sorted(registry))}")

    total_pass = 0
    total_fail = 0
    skipped = []

    for name in sorted(registry):
        print(f"\n[{name}]")
        result = run_examples_for(name, registry[name])
        if result is None:
            skipped.append(name)
            continue
        p, f = result
        total_pass += p
        total_fail += f

    print("\n" + "=" * 60)
    print(f"Summary: {total_pass} passed, {total_fail} failed")
    if skipped:
        print(f"Skipped (no example_io/<name>/ directory): {', '.join(skipped)}")

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
