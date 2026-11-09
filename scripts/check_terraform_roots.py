#!/usr/bin/env python3
"""Fail if the CI validation matrix omits or invents Terraform root directories.

This is a static inventory; it does not run Terraform, fetch providers,
create state or change any AWS resource.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def module_dirs(root: Path) -> set[str]:
    result: set[str] = set()
    for path in root.rglob("*.tf"):
        if any(part in {".terraform", ".git"} for part in path.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"symlinked Terraform file: {path}")
        result.add(path.parent.relative_to(root).as_posix())
    return result


def ci_module_dirs(workflow: Path) -> set[str]:
    text = workflow.read_text(encoding="utf-8")
    # Only the matrix list beneath 'module:' counts; other incidental paths
    # in documentation, scripts and comments must not change the gate.
    match = re.search(
        r"(?m)^\s*module:\s*\n((?:\s+-\s+[^\n]+\n)+)",
        text,
    )
    if match is None:
        raise ValueError("Terraform CI is missing a module matrix")
    return {line.strip().removeprefix("- ").strip().strip('"\'')
            for line in match.group(1).splitlines()}


def check(root: Path, workflow: Path) -> list[str]:
    actual = module_dirs(root)
    configured = ci_module_dirs(workflow)
    return [
        *[f"unvalidated Terraform module: {path}" for path in sorted(actual - configured)],
        *[f"CI matrix has no Terraform module: {path}" for path in sorted(configured - actual)],
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = check(args.root, args.root / ".github/workflows/terraform-validate.yml")
    for issue in errors:
        print("FAIL:", issue)
    if errors:
        return 1
    print("PASS: CI Terraform matrix covers every checked-in .tf module directory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
