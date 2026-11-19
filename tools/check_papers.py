#!/usr/bin/env python3
"""Checks the whitepapers repository before a commit. Run from the repository root:

    python tools/check_papers.py

It checks:
  1. Layout: every paper is a folder under papers/ (or archive/) with a README.md, and nothing
     else sits loose at the top of papers/.
  2. Names: folder and file names are lowercase-with-hyphens (code files may follow their
     language's rules, for example PizzaPoolLab.java).
  3. The header block: each paper's README.md starts with a title and has Classification,
     Prepared by, Date, Version and Status lines.
  4. Links: every relative link and picture in a paper points at a file that exists.
  5. Pictures: every .png in an assets/ folder has a matching .png.alt.md description.
  6. Private words: no paper mentions a real client, system, ticket key or person. The list of
     words lives in tools/private-terms.txt, which is NOT committed (see CLAUDE.md). Generic
     patterns (ticket keys, email addresses) are checked even without that file.

Exits 1 if anything fails, so it can run as a pre-commit hook.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SHELVES = ("papers", "archive")
HEADER_FIELDS = ("Classification", "Prepared by", "Date", "Version", "Status")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FILE_NAME = re.compile(r"^[a-z0-9]+([-_.][a-z0-9]+)*$")
CODE_EXT = {".java", ".py", ".ps1", ".sh", ".js", ".ts", ".kt", ".xml", ".properties", ".json", ".gitignore"}
LOOSE_OK = {"README.md", "LICENSE", ".gitignore", ".gitattributes"}
STANDARD_NAMES = {"README.md", "RESULTS.md", "CLAUDE.md", "SKILL.md", "LICENSE", "CHANGELOG.md"}
SKIP_DIRS = {".git", "target", "node_modules", "__pycache__", "logs", ".idea", ".vscode"}
TEXT_EXT = {".md", ".py", ".java", ".ps1", ".sh", ".xml", ".properties", ".json", ".txt", ".yml", ".yaml", ".js"}
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
GENERIC_PRIVATE = [
    (re.compile(r"\b[A-Z][A-Z0-9]{1,9}-\d{2,6}\b"), "a ticket key (for example ABC-1234)"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "an email address"),
]

problems = []


def fail(path, msg):
    problems.append(f"{os.path.relpath(path, ROOT)}: {msg}")


def private_terms():
    p = os.path.join(ROOT, "tools", "private-terms.txt")
    if not os.path.exists(p):
        print("Note: tools/private-terms.txt not found, so only generic private patterns are checked.")
        return []
    terms = [t.strip() for t in open(p, encoding="utf-8") if t.strip() and not t.startswith("#")]
    return [(re.compile(rf"(?<![A-Za-z0-9]){re.escape(t)}(?![A-Za-z0-9])", re.I), "a private word") for t in terms]


def walk(top):
    for d, dirs, files in os.walk(top):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        yield d, dirs, files


def check_names(top):
    for d, dirs, files in walk(top):
        in_code = "src" in os.path.relpath(d, top).split(os.sep)   # Java packages follow Java's rules
        for x in dirs:
            if not in_code and x != "src" and not SLUG.match(x):
                fail(os.path.join(d, x), "folder name should be lowercase-with-hyphens")
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in CODE_EXT or f in STANDARD_NAMES or f.startswith("."):
                continue
            if not FILE_NAME.match(f.lower()) or f != f.lower():
                fail(os.path.join(d, f), "file name should be lowercase-with-hyphens")


def check_paper(folder):
    readme = os.path.join(folder, "README.md")
    if not os.path.exists(readme):
        fail(folder, "a paper folder needs a README.md (the paper itself)")
        return
    text = open(readme, encoding="utf-8").read()
    if not text.lstrip().startswith("# "):
        fail(readme, "the paper should start with a '# Title' line")
    head = text[:3000]
    for field in HEADER_FIELDS:
        if not re.search(rf"^\*\*{re.escape(field)}:\*\*", head, re.M):
            fail(readme, f"header block is missing '**{field}:**'")
    for d, _, files in walk(folder):
        for f in files:
            p = os.path.join(d, f)
            if f.endswith(".md"):
                check_links(p)
            if d.endswith(os.sep + "assets") and f.endswith(".png") and f + ".alt.md" not in files:
                fail(p, "picture has no matching .png.alt.md description")


def check_links(md):
    text = open(md, encoding="utf-8").read()
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for target in LINK.findall(text):
        if re.match(r"^(https?:|mailto:|#)", target):
            continue
        path = os.path.normpath(os.path.join(os.path.dirname(md), target.split("#")[0]))
        if not os.path.exists(path):
            fail(md, f"broken link: {target}")


def check_private(patterns):
    for d, _, files in walk(ROOT):
        for f in files:
            p = os.path.join(d, f)
            if os.path.splitext(f)[1].lower() not in TEXT_EXT or f == "private-terms.txt":
                continue
            if os.path.relpath(p, ROOT).replace(os.sep, "/") in ("tools/check_papers.py", "LICENSE"):
                continue
            try:
                text = open(p, encoding="utf-8").read()
            except UnicodeDecodeError:
                continue
            for n, line in enumerate(text.splitlines(), 1):
                for rx, what in patterns:
                    if m := rx.search(line):
                        fail(p, f"line {n} contains {what}: '{m.group(0)}'")


def main():
    for shelf in SHELVES:
        top = os.path.join(ROOT, shelf)
        if not os.path.isdir(top):
            continue
        for entry in sorted(os.listdir(top)):
            p = os.path.join(top, entry)
            if os.path.isdir(p):
                if not SLUG.match(entry):
                    fail(p, "paper folder name should be lowercase-with-hyphens")
                check_paper(p)
                check_names(p)
            elif entry not in LOOSE_OK:
                fail(p, f"loose file: every paper gets its own folder under {shelf}/")
    check_private(GENERIC_PRIVATE + private_terms())

    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
