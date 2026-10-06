#!/usr/bin/env python3
"""Create a project's GitHub Actions workflow for notifying this Homebrew tap."""

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FORMULA_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def render(formula):
    if not FORMULA_NAME.fullmatch(formula):
        raise ValueError("Formula names must use lowercase letters, digits, and single hyphens between words")
    template = (ROOT / "templates/homebrew.yml.in").read_text()
    if template.count("@@FORMULA@@") != 1:
        raise ValueError("Workflow template must contain exactly one @@FORMULA@@ marker")
    return template.replace("@@FORMULA@@", formula)


def generate(formula, project, force=False):
    content = render(formula)
    project = Path(project).expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f"Project directory does not exist: {project}")
    output = project / ".github/workflows/homebrew.yml"
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects an existing workflow by default.
    with output.open("w" if force else "x") as file:
        file.write(content)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("formula", help="Homebrew package name, e.g. my-tool")
    parser.add_argument("project", help="Existing local project directory")
    parser.add_argument("--force", action="store_true", help="Replace an existing homebrew.yml workflow")
    args = parser.parse_args(argv)
    try:
        output = generate(args.formula, args.project, force=args.force)
    except FileExistsError:
        parser.error("The project already has .github/workflows/homebrew.yml; review it or use --force to replace it")
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Created {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
