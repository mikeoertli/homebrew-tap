#!/usr/bin/env python3
"""Update Homebrew formula versions, pinned upstream commits, and archive checksums."""

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tarfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")


def request(url):
    headers = {"User-Agent": "mikeoertli-homebrew-tap"}
    # Never forward the API credential to archive hosts or GitHub redirects.
    if url.startswith("https://api.github.com/"):
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
        return response.read()


def api(path):
    return json.loads(request(f"https://api.github.com/{path}"))


def semver(tag):
    match = SEMVER.fullmatch(tag)
    if not match:
        raise ValueError(f"Expected a stable semantic version tag, got {tag!r}")
    return tuple(map(int, match.groups()))


def latest_tag(repo):
    tags = []
    page = 1
    while True:
        batch = api(f"repos/{repo}/tags?per_page=100&page={page}")
        tags.extend(tag["name"] for tag in batch if SEMVER.fullmatch(tag["name"]))
        if len(batch) < 100:
            break
        page += 1
    return max(tags, key=semver) if tags else None


def source_files(archive):
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as source:
        result = {}
        for member in source.getmembers():
            name = member.name.partition("/")[2]
            if member.isfile() and name in ("VERSION", "go.mod"):
                result[name] = source.extractfile(member).read().decode("utf-8")
    if "go.mod" not in result:
        raise ValueError("Upstream archive has no root go.mod")
    return result


def render(name, entry, template):
    repo = entry["repository"]
    commit = entry["commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected a full Git commit SHA")
    semver(entry["version"])
    if entry["private"]:
        source = f'  url "git@github.com:{repo}.git", using: :git, revision: "{commit}"\n'
    else:
        if not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise ValueError("Expected an archive SHA-256 checksum")
        source = f'  url "https://github.com/{repo}/archive/{commit}.tar.gz"\n'
    source += f'  version "{entry["version"]}"\n'
    if not entry["private"]:
        source += f'  sha256 "{entry["sha256"]}"\n'
    head_url = f"git@github.com:{repo}.git" if entry["private"] else f"https://github.com/{repo}.git"
    head = f'  head "{head_url}", branch: "main"'
    if entry.get("revision", 0):
        head = f'  revision {entry["revision"]}\n' + head
    if template.count("@@SOURCE@@") != 1 or template.count("@@HEAD@@") != 1:
        raise ValueError(f"{name}: template must have exactly one source marker and one HEAD marker")
    return template.replace("@@SOURCE@@", source.rstrip()).replace("@@HEAD@@", head)


def resolve(entry, tag=None, snapshot=False):
    repo = entry["repository"]
    metadata = api(f"repos/{repo}")
    ref = metadata["default_branch"] if snapshot else tag
    commit = api(f"repos/{repo}/commits/{ref}")["sha"]
    private = metadata["private"]
    if private:
        # Read only metadata through the authenticated API; source installs use SSH.
        try:
            content = api(f"repos/{repo}/contents/VERSION?ref={commit}")
            embedded = base64.b64decode(content["content"]).decode().strip()
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            embedded = None
        digest = None
    else:
        archive = request(f"https://github.com/{repo}/archive/{commit}.tar.gz")
        files = source_files(archive)
        embedded = files.get("VERSION", "").strip() or None
        digest = hashlib.sha256(archive).hexdigest()
    version = (embedded or "0.0.0").removeprefix("v") if snapshot else tag.removeprefix("v")
    semver(version)
    if not snapshot and embedded and embedded.removeprefix("v") != version:
        raise ValueError(f"{repo}: tag {tag} does not match VERSION ({embedded})")
    if entry.get("version") and semver(version) < semver(entry["version"]):
        raise ValueError(f"Refusing downgrade from {entry['version']} to {version}")
    changed = commit != entry.get("commit") or version != entry.get("version") or private != entry.get("private")
    revision = entry.get("revision", 0)
    if changed:
        revision = revision + 1 if version == entry.get("version") else 0
    return dict(entry, commit=commit, version=version, ref=ref, snapshot=snapshot,
                private=private, sha256=digest, revision=revision)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("formula", nargs="?", help="Package name (required with --tag or --snapshot)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--tag", help="Stable upstream tag, e.g. v1.2.0")
    mode.add_argument("--snapshot", action="store_true", help="Explicitly pin the current default branch")
    mode.add_argument("--render", action="store_true", help="Render formulas from existing locked sources, offline")
    parser.add_argument("--dry-run", action="store_true", help="Show proposed updates without writing files")
    args = parser.parse_args(argv)
    if (args.tag or args.snapshot) and not args.formula:
        parser.error("--tag and --snapshot require a formula name")
    if args.tag:
        semver(args.tag)
    lock_path = ROOT / "sources.json"
    lock = json.loads(lock_path.read_text())
    if args.formula and args.formula not in lock:
        parser.error(f"Unknown formula {args.formula!r}")
    names = [args.formula] if args.formula else list(lock)
    plans = []
    for name in names:
        entry = lock[name]
        if args.render:
            if not entry.get("commit"):
                continue
        else:
            tag = args.tag
            if not args.snapshot and not tag:
                if not entry.get("commit"):
                    print(f"{name}: not bootstrapped; publish upstream and update explicitly first")
                    continue
                # The workflow token cannot read private upstream repos. Private updates
                # are deliberately explicit and need an upstream-scoped local credential.
                if entry.get("private"):
                    print(f"{name}: private upstream; skipping automatic checks")
                    continue
                tag = latest_tag(entry["repository"])
                if not tag:
                    print(f"{name}: no stable tags; keeping pinned snapshot")
                    continue
                if entry.get("version") and semver(tag) < semver(entry["version"]):
                    print(f"{name}: latest tag predates packaged version; skipping")
                    continue
            entry = resolve(entry, tag=tag, snapshot=args.snapshot)
        template = (ROOT / "templates" / f"{name}.rb.in").read_text()
        path = ROOT / "Formula" / f"{name}.rb"
        content = render(name, entry, template)
        # Preserve bottle blocks and downstream edits on an unchanged release check.
        if not args.render and entry == lock[name] and path.exists():
            print(f"{name}: already current")
            continue
        print(f"{name}: {entry['version']} ({entry['ref']}, {entry['commit'][:12]})")
        plans.append((name, entry, path, content))
    # Resolve and validate every source before making any changes.
    if not args.dry_run:
        for name, entry, path, content in plans:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            lock[name] = entry
        if plans:
            lock_path.write_text(json.dumps(lock, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, urllib.error.URLError) as error:
        sys.exit(f"Update failed: {error}")
