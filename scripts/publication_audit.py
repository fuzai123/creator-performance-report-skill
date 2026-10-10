#!/usr/bin/env python3
"""Reject likely private material before publishing a skill directory."""

import argparse
import re
import sys
from pathlib import Path


ALLOWED_SUFFIXES = {".md", ".py", ".gitignore"}
CHECKS = {
    "web address": re.compile(r"(?:https?://|www\.)\S+", re.I),
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "Windows user path": re.compile(r"\b[A-Z]:[\\/](?:Users|Documents)[\\/]", re.I),
    "Unix user path": re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+/"),
    "possible access token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._-]{20,})\b"),
    "embedded source host": re.compile(r"\b(?:feishu|larksuite|shopify-admin)\.[A-Za-z.]+\b", re.I),
}


def audit(root):
    issues = []
    for path in root.rglob("*"):
        if ".git" in path.relative_to(root).parts or "__pycache__" in path.parts:
            continue
        if path.is_symlink():
            issues.append(f"{path.relative_to(root)}: symlink not allowed")
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if path.suffix not in ALLOWED_SUFFIXES and path.name != ".gitignore":
            issues.append(f"{relative}: unexpected file type")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            issues.append(f"{relative}: not UTF-8 text")
            continue
        for label, pattern in CHECKS.items():
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                issues.append(f"{relative}:{line}: {label}")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory.resolve()
    if not root.is_dir():
        parser.error("directory does not exist")
    issues = audit(root)
    if issues:
        print("Publication blocked:\n" + "\n".join(f"- {issue}" for issue in issues), file=sys.stderr)
        return 1
    print("Publication audit passed; manually inspect staged diff and history as well")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
