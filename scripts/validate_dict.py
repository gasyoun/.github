#!/usr/bin/env python3
"""Data gate for Sanskrit dictionary repositories (stdlib only, Python 3.9+).

Checks changed text files for: UTF-8 without BOM, change-file line format
("NNN old|new|ins|del"), <L> lines that carry a headword, and a catastrophic
headword-count drop against the base revision. No network, no third-party deps.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile

CHANGE_RX = re.compile(r"^\d+\s+(old|new|ins|del)(\s|$)")
TEXT_EXT = {".txt", ".xml", ".changes", ".tsv"}
MAX_FILES = 3000


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def changed_files(base: str):
    if base and set(base) != {"0"}:
        r = git("diff", "--name-only", "--diff-filter=ACMR", base, "HEAD")
        if r.returncode == 0:
            return [p for p in r.stdout.splitlines() if p][:MAX_FILES]
    r = git("diff", "--name-only", "--diff-filter=ACMR", "HEAD~1", "HEAD")
    if r.returncode == 0:
        return [p for p in r.stdout.splitlines() if p][:MAX_FILES]
    r = git("ls-files")
    return [p for p in r.stdout.splitlines() if p][:MAX_FILES]


def is_change_file(path: str) -> bool:
    name = os.path.basename(path).lower()
    return name.startswith("changes") or name.startswith("change_") or name.startswith("change-")


def read_text(path: str) -> str:
    with open(path, "rb") as fh:
        data = fh.read()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM present")
    return data.decode("utf-8")


def count_l(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith("<L>"))


def check_file(path: str, base: str = ""):
    try:
        text = read_text(path)
    except UnicodeDecodeError as exc:
        return ["%s: not valid UTF-8 (%s)" % (path, exc)]
    except ValueError as exc:
        return ["%s: %s" % (path, exc)]

    errors = []
    if is_change_file(path):
        bad = []
        for i, line in enumerate(text.splitlines(), 1):
            s = line.strip()
            if not s or s[0] in "#;/":
                continue
            if s[0].isdigit() and not CHANGE_RX.match(s):
                bad.append(i)
        for n in bad[:5]:
            errors.append("%s:%d: change line does not match 'NNN old|new|ins|del'" % (path, n))
        if len(bad) > 5:
            errors.append("%s: ... %d more malformed change lines" % (path, len(bad) - 5))

    total_l = count_l(text)
    if total_l:
        empty = [i for i, line in enumerate(text.splitlines(), 1)
                 if line.startswith("<L>") and not line[3:].strip()]
        for n in empty[:5]:
            errors.append("%s:%d: <L> line has no headword" % (path, n))
        if base and total_l >= 5000:
            old = git("show", "%s:%s" % (base, path))
            if old.returncode == 0 and count_l(old.stdout) >= 5000:
                before = count_l(old.stdout)
                if total_l < before * 0.995:
                    errors.append("%s: headword count dropped %d -> %d (>0.5%%)" % (path, before, total_l))
    return errors


def selftest() -> int:
    td = tempfile.mkdtemp()
    cases = []
    good = os.path.join(td, "changes_good.txt")
    with open(good, "w", encoding="utf-8") as fh:
        fh.write("123 old\n124 new corrected reading\n")
    cases.append((good, []))
    bad = os.path.join(td, "changes_bad.txt")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write("123 old\n123 oops\n")
    cases.append((bad, ["does not match"]))
    bom = os.path.join(td, "bom.txt")
    with open(bom, "wb") as fh:
        fh.write(b"\xef\xbb\xbfabc\n")
    cases.append((bom, ["BOM"]))
    empty = os.path.join(td, "empty_l.txt")
    with open(empty, "w", encoding="utf-8") as fh:
        fh.write("<L>\n")
    cases.append((empty, ["no headword"]))

    failed = 0
    for path, want in cases:
        got = check_file(path)
        ok = (not want and not got) or (want and any(w in g for g in got for w in want))
        print(("PASS" if ok else "FAIL"), os.path.basename(path), got)
        failed += 0 if ok else 1
    print("selftest: %d/%d" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("paths", nargs="*")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if args.paths:
        files = [p for p in args.paths if os.path.exists(p)]
    else:
        files = [p for p in changed_files(args.base)
                 if os.path.splitext(p)[1].lower() in TEXT_EXT and os.path.exists(p)]

    errors = []
    for path in files:
        errors += check_file(path, args.base)

    lines = ["data-validate: %d file(s) checked, %d error(s)" % (len(files), len(errors))]
    lines += ["- %s" % e for e in errors[:50]]
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
