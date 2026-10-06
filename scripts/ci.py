#!/usr/bin/env python3
"""Select changed public formulas for Homebrew CI (private sources stay local)."""

import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def select(lock, files):
    names = {Path(file).stem for file in files if file.startswith("Formula/") and file.endswith(".rb")}
    return sorted(name for name in names if name in lock and lock[name].get("commit") and not lock[name]["private"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args()
    lock = json.loads((ROOT / "sources.json").read_text())
    if args.base:
        def diff(*flags):
            return subprocess.check_output(
                ["git", "diff", "--name-only", *flags, args.base, args.head, "--", "Formula"],
                cwd=ROOT, text=True,
            ).splitlines()
        names = select(lock, diff("--diff-filter=AM"))
        added = select(lock, diff("--diff-filter=A"))
    else:
        names = select(lock, [str(file.relative_to(ROOT)) for file in (ROOT / "Formula").glob("*.rb")])
        added = []
    print("formulae=" + ",".join(f"mikeoertli/tap/{name}" for name in names))
    print("added=" + ",".join(f"mikeoertli/tap/{name}" for name in added))


if __name__ == "__main__":
    main()
